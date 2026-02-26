from django.db import models
from django.conf import settings
from common.models import BaseModel

class News(BaseModel):
    title = models.CharField(max_length=255)
    main = models.TextField()
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    new_column = models.BigIntegerField()
    img = models.ImageField(upload_to='news_images/', null=True, blank=True)
    def __str__(self):
        return self.title