from django.db import models
from django.conf import settings

# Create your models here.
class Alertgroup(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, default=None, related_name="alertusers", on_delete=models.CASCADE)
    name = models.CharField(max_length=5,default="AAPL")
    alert = models.DecimalField(decimal_places=2,max_digits=7)