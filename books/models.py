from django.db import models
from django.conf import settings
from common.models import BaseModel
from django.db.models.signals import post_save
from django.dispatch import receiver

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
    category = models.ForeignKey(Category, on_delete=models.SET_NULL)
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
    place = models.BigIntegerField()

    def __str__(self):
        return f'{self.user.username} - {self.book.name}'

@post_save(sender=Reservation)
def update_book_availability(sender, instance, **kwargs):
    """Update the availability of the book when a reservation is created or updated."""
    book = instance.book
    if instance.status == 2:  # Approved
        book.is_available = False
    elif instance.status == 3:  # Returned
        book.is_available = True
    book.save()