from django.contrib.auth import get_user_model
from rest_framework.fields import CharField, SerializerMethodField
from rest_framework.serializers import ModelSerializer

from graphql_framework.decorators import returns
from graphql_framework.schema import Schema, SerializerSchema

User = get_user_model()


class UserSerializer(ModelSerializer):
    full_name = SerializerMethodField(required=False)

    class Meta:
        model = User
        fields = "__all__"

    @returns(CharField)
    def get_full_name(self, obj):
        if not obj.first_name and not obj.last_name:
            return None
        if obj.first_name and not obj.last_name:
            return obj.first_name
        if not obj.first_name and obj.last_name:
            return obj.last_name
        return f"{obj.first_name} {obj.last_name}"



class UserSchema(SerializerSchema, serializer_cls=UserSerializer, model=User):
    # def get(self, id):
    #     return User.objects.get(pk=id)
    pass


class Query(Schema):
    human = UserSchema.field_singular(lookup_fields=("id", "username", "email"))
    # humans = HUMAN_SCHEMA.query_multiple
