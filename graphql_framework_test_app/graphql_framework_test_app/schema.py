from django.contrib.auth import get_user_model
from rest_framework.serializers import ModelSerializer

from graphql_framework.schema import Schema, SerializerSchema

User = get_user_model()


class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"


class Query(Schema):
    _human_schema = SerializerSchema(UserSerializer)
    human = _human_schema.query_singular
    # humans = _human_schema.query_multiple
