from django.contrib.auth import get_user_model
from django.db import models


class UserAttribute(models.Model):
    height = models.FloatField()
    user = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, related_name="attributes"
    )
