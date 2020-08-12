from django.contrib.auth import get_user_model
from rest_framework.fields import CharField, FloatField
from rest_framework.serializers import ModelSerializer

from graphql_framework.fields import (
    ModelMethodField,
    ModelPropertyField,
    TypedSerializerMethodField,
)

from .models import UserAttribute

User = get_user_model()


class UserSerializer(ModelSerializer):
    full_name = TypedSerializerMethodField(CharField, required=False)

    class Meta:
        model = User
        fields = "__all__"
        # fields = ["id", "username", "email", "first_name", "attributes", "full_name"]

    def get_full_name(self, obj):
        if not obj.first_name and not obj.last_name:
            return None
        if obj.first_name and not obj.last_name:
            return obj.first_name
        if not obj.first_name and obj.last_name:
            return obj.last_name
        return f"{obj.first_name} {obj.last_name}"


class UserAttributeSerializer(ModelSerializer):
    name_and_height = ModelPropertyField(CharField, "name_and_height")
    double_height = ModelMethodField(FloatField, "get_height_with_mult", method_args=(2,))
    triple_height = ModelMethodField(FloatField, "get_height_with_mult", method_args=(3,))

    class Meta:
        model = UserAttribute
        fields = "__all__"
