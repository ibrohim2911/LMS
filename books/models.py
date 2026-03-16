from django.db import models
from django.conf import settings
from common.models import BaseModel
from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.db.models import F, Avg, Max
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
RESERV_STATUS_CHOICES = (
    ('pending', 'Pending'),
    ('approved', 'Approved'),
    ('given', 'Given'),
    ('returned', 'Returned'),
    ('not_returned', 'Not Returned'),

)
class Journals(BaseModel):
    name=models.CharField(max_length=300)
    publisher=models.CharField(max_length=300)
    description=models.TextField()
    iccn=models.CharField(max_length=300)
    start_date=models.DateField(null=True, blank=True)
    end_date=models.DateField(null=True, blank=True)
    img = models.ImageField(upload_to='journals_images/', null=True, blank=True)
class Category(BaseModel):
    name = models.CharField(max_length=255)
    visible = models.BooleanField(default=True)
    icon = models.TextField(null=True, blank=True)
    def __str__(self):
        return self.name
class subCategory(BaseModel):
    name = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subcategories')
    visible = models.BooleanField(default=True)
    def __str__(self):
        return self.name
class Tag(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name
class Author(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name
class Kitob(BaseModel):
    name = models.CharField(max_length=255)
    subcategory = models.ForeignKey(subCategory, on_delete=models.SET_NULL, null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    read_time = models.IntegerField(default=14, null=True, blank=True)
    quantity = models.IntegerField()
    visible = models.BooleanField(default=True)
    rating = models.IntegerField(null=True, blank=True)
    description = models.TextField()
    author = models.ManyToManyField(Author)
    location = models.CharField(max_length=255, null=True,blank=True)
    is_available = models.BooleanField(default=True)
    tags = models.ManyToManyField(Tag)
    isbn = models.CharField(max_length=20)
    is_frequent=models.BooleanField()
    img = models.ImageField(upload_to='book_images/', null=True, blank=True)
    published_date = models.DateField(null=True, blank=True)
    pdf = models.FileField(upload_to='book_pdfs/', null=True, blank=True)
    audio = models.FileField(upload_to='book_audios/', null=True, blank=True)
    is_physical = models.BooleanField(default=True)
    pages = models.IntegerField(null=True, blank=True)
    def __str__(self):
        return self.name + " " + ", ".join(str(author) for author in self.author.all())
    
    def get_read_count(self):
        """Returns how many times this book has been read (completed reservations)."""
        return self.reservation_set.filter(status=3).count()
    
    def get_average_rating(self):
        """Returns the average rating for this book, or None if no ratings exist."""
        avg = self.ratings.aggregate(Avg('score'))['score__avg']
        return round(avg, 1) if avg else None
class Reservation(BaseModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    book = models.ForeignKey(Kitob, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=RESERV_STATUS_CHOICES, default='pending')
    place = models.BigIntegerField(null=True, blank=True)
    reserved_from = models.DateTimeField(null=True, blank=True)
    reserved_until = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    returned_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'{self.user.username} - {self.book.name}'

class Rating(BaseModel):
    book = models.ForeignKey(Kitob, on_delete=models.CASCADE, related_name='ratings')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='given_ratings')
    score = models.IntegerField(choices=[(i, i) for i in range(1, 6)])  # 1-5 stars
    comment = models.ForeignKey('Comment', null=True, blank=True, on_delete=models.SET_NULL, related_name='rating_comment') 
    
    class Meta:
        unique_together = ('book', 'user')  # One rating per user per book
    
    def __str__(self):
        return f'{self.user.username} rated {self.book.name} - {self.score} stars'

class Comment(BaseModel):
    book = models.ForeignKey(Kitob, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comments')
    reply_to = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies')
    rating = models.ForeignKey(Rating, null=True, blank=True, on_delete=models.SET_NULL, related_name='comments')
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='child_comments')

    content = models.TextField()
    
    def __str__(self):
        return f'{self.user.username} commented on {self.book.name}'
class Bookmark(BaseModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookmarks')
    book = models.ForeignKey(Kitob, on_delete=models.CASCADE, related_name='bookmarks')

    class Meta:
        unique_together = ('user', 'book')  # Prevent duplicate bookmarks

    def __str__(self):
        return f'{self.user.username} bookmarked {self.book.name}'

@receiver(pre_save, sender=Reservation)
def reservation_pre_save(sender, instance, **kwargs):
    if instance.pk:
        try:
            old = Reservation.objects.get(pk=instance.pk)
            instance._pre_save_status = old.status
            instance._pre_save_place = old.place
        except Reservation.DoesNotExist:
            instance._pre_save_status = None
            instance._pre_save_place = None
    else:
        instance._pre_save_status = None
        instance._pre_save_place = None

    # Validate approval conditions
    if instance.status == 'approved' and instance._pre_save_status != 'approved':
        # Check user constraints
        if instance.user.is_banned:
             raise ValidationError('Cannot approve: User is banned.')
        
        # Check max books
        active_count = Reservation.objects.filter(
            user=instance.user, 
            status__in=['approved', 'given']
        ).exclude(pk=instance.pk).count()
        
        if active_count >= instance.user.max_allowed:
            raise ValidationError(f'Cannot approve: User has reached the limit of {instance.user.max_allowed} books.')

        # Check availability
        # Note: If we are approving, we are about to reserve a copy.
        # We must ensure there is a copy to reserve.
        if instance.book.quantity <= 0:
            raise ValidationError('Cannot approve reservation: no copies available for this book.')


@receiver(post_save, sender=Reservation)
def reservation_post_save(sender, instance, created, **kwargs):
    # 1. Assign place for new PENDING reservations only
    if created and instance.status == 'pending':
        max_place = (
            Reservation.objects.filter(book=instance.book, status='pending')
            .exclude(pk=instance.pk)
            .aggregate(m=Max('place'))
        )['m']

        if instance.place is None:
            instance.place = (max_place or 0) + 1
            Reservation.objects.filter(pk=instance.pk).update(place=instance.place)
            # Refresh instance place
            instance.place = (max_place or 0) + 1

    # 2. Handle Status Transitions
    prev_status = getattr(instance, '_pre_save_status', None)
    prev_place = getattr(instance, '_pre_save_place', None)
    
    if prev_status != instance.status:
        now = timezone.now()
        book_qs = Kitob.objects.filter(pk=instance.book.pk)
        
        try:
            with transaction.atomic():
                # APPROVED: pending -> approved
                if instance.status == 'approved' and prev_status != 'approved':
                    # Remove from Queue: If they were in the queue, remove them and shift others up
                    if prev_place and prev_place > 0:
                         Reservation.objects.filter(book=instance.book, status='pending', place__gt=prev_place).update(place=F('place') - 1)
                         # instance place is cleared below
                    
                    # Clear own place as they are no longer "waiting"
                    Reservation.objects.filter(pk=instance.pk).update(place=None)
                    
                    # Decrement quantity
                    book_qs.update(quantity=F('quantity') - 1)
                    
                    # Set approved_at (24h window starts)
                    Reservation.objects.filter(pk=instance.pk).update(approved_at=now)
                
                # GIVEN: approved -> given
                elif instance.status == 'given' and prev_status == 'approved':
                    # Set reading timers
                    read_time = instance.book.read_time or 14
                    Reservation.objects.filter(pk=instance.pk).update(
                        reserved_from=now,
                        reserved_until=now + timezone.timedelta(days=read_time)
                    )
                    # Note: Quantity was already decremented on approval.
                
                # RETURNED: given -> returned
                elif instance.status == 'returned' and prev_status == 'given':
                    # Increment quantity
                    book_qs.update(quantity=F('quantity') + 1)
                    # Set returned_at timestamp
                    Reservation.objects.filter(pk=instance.pk).update(returned_at=now)
                    # Place is already None/0 from approval step

                # NOT RETURNED: given -> not_returned
                # (No quantity change, book is still out)

                # CANCELLATION/RESET (e.g. Approved -> Cancelled/Pending/Returned without being given)
                # If we revert from Approved to something else (except Given), we must restore quantity.
                elif prev_status == 'approved' and instance.status not in ['given', 'approved']:
                     book_qs.update(quantity=F('quantity') + 1)

                
                # Refresh book availability status based on new quantity
                book = Kitob.objects.select_for_update().get(pk=instance.book.pk)
                if book.quantity < 0:
                    book.quantity = 0
                book.is_available = book.quantity > 0
                book.save(update_fields=['quantity', 'is_available'])

        except Kitob.DoesNotExist:
            pass

    # 3. Queue Shifting (Clean up)
    # Logic handled inside transition block (pending -> approved shifts queue).
    pass

    # 4. Auto-Approve Logic (For NEW pending request OR when book becomes available)
    # Trigger: Created Pending OR Book Returned (Quantity became > 0)
    
    # We need to re-fetch book quantity because we might have just updated it
    instance.book.refresh_from_db()

    # We only auto-approve if there is stock available
    if instance.book.quantity > 0:
        # Check queue for who is eligible
        # Criteria: Status pending, lowest place, valid user
        candidates = Reservation.objects.filter(
            book=instance.book,
            status='pending',
            place__gt=0  # Valid queue position
        ).order_by('place')

        for candidate in candidates:
             # Refresh book quantity inside loop as we might have decremented it in previous iteration
             instance.book.refresh_from_db()
             if instance.book.quantity <= 0:
                 break # No more books
             
             # Validation check
             user = candidate.user
             if user.is_banned:
                 continue
             
             active_count = Reservation.objects.filter(
                user=user, 
                status__in=['approved', 'given']
             ).count()
             
             if active_count >= user.max_allowed:
                 continue
             
             # If Valid, Approve
             # This save() will trigger post_save recursively:
             # - Decrement quantity
             # - Shift queue (remove this candidate from place 1, everyone else moves up)
             # - Set approved_at
             candidate.status = 'approved'
             candidate.save()

@receiver(post_delete, sender=Reservation)
def reservation_post_delete(sender, instance, **kwargs):
    # Shift queue if a pending reservation with a valid place is deleted
    if instance.status == 'pending' and instance.place is not None and instance.place > 0:
         Reservation.objects.filter(book=instance.book, status='pending', place__gt=instance.place).update(place=F('place')-1)

    # If an APPROVED reservation is deleted, we must restore quantity
    if instance.status == 'approved':
        try:
            with transaction.atomic():
                Kitob.objects.filter(pk=instance.book.pk).update(quantity=F('quantity') + 1)
                book = Kitob.objects.select_for_update().get(pk=instance.book.pk)
                book.is_available = book.quantity > 0
                book.save(update_fields=['quantity', 'is_available'])
        except Kitob.DoesNotExist:
            pass

@receiver(post_save, sender=Rating)
def set_avg_rating(sender,instance,**kwargs):
    book = instance.book
    avg_rating = book.ratings.aggregate(Avg('score'))['score__avg']
    book.rating = round(avg_rating, 1) if avg_rating else None
    book.save(update_fields=['rating'])
@receiver(post_delete, sender=Rating)
def update_avg_rating_on_delete(sender, instance, **kwargs):
    book = instance.book
    avg_rating = book.ratings.aggregate(Avg('score'))['score__avg']
    book.rating = round(avg_rating, 1) if avg_rating else None
    book.save(update_fields=['rating'])
