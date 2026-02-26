from django.contrib import admin
from .models import Category, Tag, Kitob, Ebook, Reservation, Rating

admin.site.register(Category)
admin.site.register(Tag)
admin.site.register(Kitob)
admin.site.register(Ebook)
admin.site.register(Reservation)
admin.site.register(Rating)