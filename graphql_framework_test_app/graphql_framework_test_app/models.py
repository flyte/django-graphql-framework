from django.contrib.auth import get_user_model
from django.db import models


class UserAttribute(models.Model):
    height = models.FloatField()
    user = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, related_name="attributes"
    )

    @property
    def name_and_height(self):
        return f"{self.user.first_name} is {self.height} metres tall"

    def get_height_with_mult(self, mult):
        return self.height * mult
