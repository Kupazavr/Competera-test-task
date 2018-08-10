from django.db import models

# Create your models here.

class Parameters(models.Model):
    article = models.CharField(max_length=200, primary_key=True)
    title = models.CharField(max_length=200, default='')
    price = models.FloatField(max_length=10, default=0)
    gross_weight = models.IntegerField()
    creation_date = models.DateField()
    update_date = models.DateField()
    cost_price = models.FloatField(default=0)
    category = models.CharField(max_length=100, default='')

