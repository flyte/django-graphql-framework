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
        lookup_fields=("id", "username", "email"),  # For the singular field arguments
        field="user",  # Otherwise will just use the field name we assigned it to. None to not use one.
        list_field=None,  # Set to None to not use one
    )

    user_attribute = UserAttributeType(
        lookup_fields=(
            "id",
            # "user__id"  # FIXME: This causes an issue because the serializer doesn't have a field called user__id.
        ),
        list_field="user_attributes",
    )
