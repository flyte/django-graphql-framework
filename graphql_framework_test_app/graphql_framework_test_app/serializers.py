from django.contrib.auth import get_user_model
from rest_framework.fields import CharField
from rest_framework.serializers import ModelSerializer

from graphql_framework.fields import TypedSerializerMethodField

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

    # TODO: Tasks pending completion -@flyte at 12/08/2020, 15:29:04
    # How to access properties/functions on model via GraphQL?

    class Meta:
        model = UserAttribute
        fields = "__all__"
