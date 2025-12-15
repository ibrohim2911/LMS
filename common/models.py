from django.db import models

class BaseModel(models.Model):
    c_at = models.DateTimeField(auto_now_add=True)
    u_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True