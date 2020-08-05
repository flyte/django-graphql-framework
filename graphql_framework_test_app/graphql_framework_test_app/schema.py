from django.contrib.auth import get_user_model
from rest_framework.fields import SerializerMethodField, CharField
from rest_framework.serializers import ModelSerializer

from graphql_framework.schema import Schema, SerializerSchema

User = get_user_model()


class UserSerializer(ModelSerializer):
    my_method_field = SerializerMethodField()

    class Meta:
        model = User
        fields = "__all__"

    def get_my_method_field(self, obj):
        return "It's working!!"

    get_my_method_field.type = CharField


class HumanSchema(SerializerSchema, serializer_cls=UserSerializer, model=User):
    # def get(self, id):
    #     return User.objects.get(pk=id)
    pass


class Query(Schema):
    human = HumanSchema.field_singular(args=("id",))
    # humans = HUMAN_SCHEMA.query_multiple
