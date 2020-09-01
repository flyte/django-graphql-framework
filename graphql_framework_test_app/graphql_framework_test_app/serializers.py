from django.contrib.auth import get_user_model
from rest_framework.fields import CharField, FloatField
from rest_framework.relations import RelatedField
from rest_framework.serializers import ModelSerializer

from graphql_framework.fields import (
    ModelMethodField,
    ModelPropertyField,
    TypedSerializerMethodField,
)
from graphql_framework.mixins import ModelSerializerExtraFieldsMixin

from .models import UserAttribute, UserAttribute2

User = get_user_model()


class UserSerializer(ModelSerializerExtraFieldsMixin, ModelSerializer):
    full_name = TypedSerializerMethodField(CharField, required=False)

    class Meta:
        model = User
        fields = "__all__"
        extra_fields = ["attributes"]

    def get_full_name(self, obj):
        if not obj.first_name and not obj.last_name:
            return None
        if obj.first_name and not obj.last_name:
            return obj.first_name
        if not obj.first_name and obj.last_name:
            return obj.last_name
        return f"{obj.first_name} {obj.last_name}"


class UserAttributeSerializer(ModelSerializerExtraFieldsMixin, ModelSerializer):
    name_and_height = ModelPropertyField(CharField, "name_and_height", required=False)
    double_height = ModelMethodField(
        FloatField, "get_height_with_mult", method_args=(2,), required=False
    )
    triple_height = ModelMethodField(
        FloatField, "get_height_with_mult", method_args=(3,), required=False
    )

    class Meta:
        model = UserAttribute
        fields = "__all__"
        extra_fields = ["more"]
        extra_kwargs = {"more": dict(required=False)}


class UserAttribute2Serializer(ModelSerializer):
    class Meta:
        model = UserAttribute2
        fields = "__all__"
