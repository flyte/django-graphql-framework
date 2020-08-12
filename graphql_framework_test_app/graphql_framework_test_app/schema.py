from django.contrib.auth import get_user_model

from graphql_framework.schema import ModelSerializerType, Schema

from .models import UserAttribute
from .serializers import UserAttributeSerializer, UserSerializer

User = get_user_model()


class UserType(ModelSerializerType, serializer_cls=UserSerializer):
    pass


class UserAttributeType(ModelSerializerType, serializer_cls=UserAttributeSerializer):
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
    )

    user_attribute = UserAttributeType(
        singular_lookup_fields=("id", "user__email", "user__username"),
        list_lookup_fields=None,  # None means all here
        list_field="user_attributes",
        create_mutation=True,
        update_mutation=True,
    )
