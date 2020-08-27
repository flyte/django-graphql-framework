from django.contrib.auth import get_user_model

from graphql_framework.schema import ModelSerializerType, Schema

from .models import UserAttribute, UserAttribute2
from .serializers import UserAttribute2Serializer, UserAttributeSerializer, UserSerializer

User = get_user_model()


class UserType(ModelSerializerType, serializer_cls=UserSerializer):
    pass


class UserAttributeType(ModelSerializerType, serializer_cls=UserAttributeSerializer):
    pass


class UserAttribute2Type(ModelSerializerType, serializer_cls=UserAttribute2Serializer):
    pass


class MySchema(Schema):
    # user = UserSchema.field_singular(lookup_fields=("id", "username", "email"))
    # users = UserSchema.field_multiple

    # user_attribute = UserAttributeSchema.field_singular()

    user = UserType(
        singular_lookup_fields=("id", "first_name", "username", "email"),
        field="user",  # Otherwise will just use the field name we assigned it to. None to not use one.
        list_field=None,  # Set to None to not use one
        create_mutation=False,
        update_mutation=True,
        delete_mutation=False,
    )

    user_attribute = UserAttributeType(
        singular_lookup_fields=("id", "user__email", "user__username"),
        list_lookup_fields=None,  # None means all here
        list_field="user_attributes",
        create_mutation=True,
        update_mutation=True,
        delete_mutation=True,
    )

    user_attribute2 = UserAttribute2Type(
        singular_lookup_fields=("id",),
        list_lookup_fields=None,  # None means all here
        list_field="user_attribute2s",
        create_mutation=True,
        update_mutation=True,
        delete_mutation=True,
    )
