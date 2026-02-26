from django.db import models
from django.conf import settings
from common.models import BaseModel
from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.db.models import F, Avg, Max
from django.db import transaction
from django.core.exceptions import ValidationError

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

class Tag(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class Kitob(BaseModel):
    name = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    read_time = models.DateField(default=None, null=True, blank=True)
    quantity = models.IntegerField()
    visible = models.BooleanField(default=True)
    reader = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='read_books')
    rating = models.IntegerField(null=True, blank=True)
    description = models.TextField()
    author = models.CharField(max_length=255)
    is_available = models.BooleanField(default=True)
    tags = models.ManyToManyField(Tag)
    isbn = models.CharField(max_length=20)
    is_frequent=models.BooleanField()
    img = models.ImageField(upload_to='book_images/', null=True, blank=True)
    published_date = models.DateField(null=True, blank=True)
    
    def __str__(self):
        return self.name + " " + self.author
    
    def get_read_count(self):
        """Returns how many times this book has been read (completed reservations)."""
        return self.reservation_set.filter(status=3).count()
    
    def get_average_rating(self):
        """Returns the average rating for this book, or None if no ratings exist."""
        avg = self.ratings.aggregate(Avg('score'))['score__avg']
        return round(avg, 1) if avg else None
class Ebook(BaseModel):
    author = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    description = models.TextField()
    new_column = models.BigIntegerField()
    img = models.ImageField(upload_to='ebook_images/', null=True, blank=True)
    def __str__(self):
        return self.title

class Reservation(BaseModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    book = models.ForeignKey(Kitob, on_delete=models.CASCADE)
    status = models.IntegerField(default=1) # 1 for pending, 2 for approved, 3 returned 4 should have returned.
    place = models.BigIntegerField(null=True, blank=True)

    def __str__(self):
        return f'{self.user.username} - {self.book.name}'

class Rating(BaseModel):
    book = models.ForeignKey(Kitob, on_delete=models.CASCADE, related_name='ratings')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='given_ratings')
    score = models.IntegerField(choices=[(i, i) for i in range(1, 6)])  # 1-5 stars
    comment = models.TextField(blank=True, null=True)
    
    class Meta:
        unique_together = ('book', 'user')  # One rating per user per book
    
    def __str__(self):
        return f'{self.user.username} rated {self.book.name} - {self.score} stars'


@receiver(post_save, sender=Reservation)
def update_book_availability(sender, instance, **kwargs):
    """Update the availability of the book when a reservation is created or updated."""
    book = instance.book
    if instance.status == 2:  # Approved
        book.is_available = False
    elif instance.status == 3:  # Returned
        book.is_available = True
    elif instance.status == 4:  # Should have returned
        book.is_available = False
    book.save()


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
    # Prevent approving a reservation when there are no available copies
    # If this reservation is transitioning to approved (2) from a non-approved state
    will_be_approved = (instance.status == 2) and (instance._pre_save_status != 2)
    if will_be_approved:
        # instance.book may be a Kitob instance or a pk; ensure we load fresh value
        book = instance.book
        if book.quantity <= 0:
            raise ValidationError('Cannot approve reservation: no copies available for this book.')


@receiver(post_save, sender=Reservation)
def reservation_post_save(sender, instance, created, **kwargs):
    # Assign place for newly created reservations
    if created:
        max_place = (
            Reservation.objects.filter(book=instance.book)
            .exclude(pk=instance.pk)
            .aggregate(m=Max('place'))
        )['m']

        if instance.place is None:
            instance.place = (max_place or 0) + 1
            Reservation.objects.filter(pk=instance.pk).update(place=instance.place)
        else:
            Reservation.objects.filter(book=instance.book, place__gte=instance.place).exclude(pk=instance.pk).update(place=F('place')+1)

    # If status changed to returned (3) from something else, shift queue up
    prev_status = getattr(instance, '_pre_save_status', None)
    prev_place = getattr(instance, '_pre_save_place', None)
    if prev_status != instance.status and instance.status == 3:
        # use previous place (before return) to shift the queue
        shift_from = prev_place if prev_place is not None else instance.place
        if shift_from is not None:
            Reservation.objects.filter(book=instance.book, place__gt=shift_from).update(place=F('place')-1)
        # set returned reservation's place to 0 to mark it as returned
        Reservation.objects.filter(pk=instance.pk).update(place=0)

    # Handle quantity and availability changes when status transitions occur
    # Use atomic updates to avoid race conditions
    prev_status = getattr(instance, '_pre_save_status', None)
    try:
        with transaction.atomic():
            book_qs = Kitob.objects.filter(pk=instance.book.pk)
            # If reservation was approved now (transitioned to 2), decrement quantity
            if prev_status != instance.status and instance.status == 2:
                book_qs.update(quantity=F('quantity') - 1)
            # If reservation was previously approved and now returned (3) or deleted, increment quantity
            if prev_status == 2 and instance.status == 3:
                book_qs.update(quantity=F('quantity') + 1)
            # Refresh book instance and set availability
            book = Kitob.objects.select_for_update().get(pk=instance.book.pk)
            # Ensure quantity never goes negative
            if book.quantity < 0:
                # Clamp to zero
                book.quantity = 0
            book.is_available = book.quantity > 0
            book.save(update_fields=['quantity', 'is_available'])
    except Kitob.DoesNotExist:
        pass


@receiver(post_delete, sender=Reservation)
def reservation_post_delete(sender, instance, **kwargs):
    if instance.place is not None:
        Reservation.objects.filter(book=instance.book, place__gt=instance.place).update(place=F('place')-1)
    # If a reservation that was approved is deleted, return the copy to inventory
    try:
        if instance.status == 2:
            with transaction.atomic():
                Kitob.objects.filter(pk=instance.book.pk).update(quantity=F('quantity') + 1)
                book = Kitob.objects.select_for_update().get(pk=instance.book.pk)
                if book.quantity < 0:
                    book.quantity = 0
                book.is_available = book.quantity > 0
                book.save(update_fields=['quantity', 'is_available'])
    except Kitob.DoesNotExist:
        pass