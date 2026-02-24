from django.db import models
from django.conf import settings
from common.models import BaseModel
from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.db.models import F, Max

class Journals(BaseModel):
    name=models.CharField(max_length=300)
    publisher=models.CharField(max_length=300)
    description=models.TextField()
    iccn=models.CharField(max_length=300)
    start_date=models.DateField()
    end_date=models.DateField()
class Category(BaseModel):
    name = models.CharField(max_length=255)
    visible = models.BooleanField(default=True)
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
    rating = models.IntegerField()
    description = models.TextField()
    author = models.CharField(max_length=255)
    is_available = models.BooleanField(default=True)
    tags = models.ManyToManyField(Tag)
    isbn = models.CharField(max_length=20)
    is_frequent=models.BooleanField()
    def __str__(self):
        return self.name + " " + self.author

class Ebook(BaseModel):
    author = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    description = models.TextField()
    new_column = models.BigIntegerField()

    def __str__(self):
        return self.title

class Reservation(BaseModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    book = models.ForeignKey(Kitob, on_delete=models.CASCADE)
    status = models.IntegerField(default=1) # 1 for pending, 2 for approved, 3 returned 4 should have returned.
    place = models.BigIntegerField(null=True, blank=True)

    def __str__(self):
        return f'{self.user.username} - {self.book.name}'

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


@receiver(post_delete, sender=Reservation)
def reservation_post_delete(sender, instance, **kwargs):
    if instance.place is not None:
        Reservation.objects.filter(book=instance.book, place__gt=instance.place).update(place=F('place')-1)