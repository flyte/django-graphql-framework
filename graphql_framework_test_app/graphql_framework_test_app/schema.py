from django.contrib.auth import get_user_model
from rest_framework.serializers import ModelSerializer

from graphql_framework.schema import Schema, SerializerSchema

User = get_user_model()


class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"


class HumanSchema(SerializerSchema, serializer=UserSerializer, model=User):
    # def get(self, id):
    #     return User.objects.get(pk=id)
    pass


class Query(Schema):
    human = HumanSchema.field_singular(args=("id",))
    # humans = HUMAN_SCHEMA.query_multiple
