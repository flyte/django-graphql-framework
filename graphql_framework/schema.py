from graphql import GraphQLField, GraphQLObjectType
from graphql.type.scalars import GraphQLInt
from rest_framework.fields import IntegerField

SCHEMA = {}


class SerializerSchema:
    """
    Turns a Django REST Framework Serializer into a GraphQL CRUD schema.
    """

    def __init__(self, serializer):
        self.serializer = serializer

    @property
    def query_singular(self):
        # Figure out the fields on the serializer, turn them into graphql ones
        serializer = self.serializer()
        schema = dict()
        for field_name, field in serializer.fields.items():
            if isinstance(field, IntegerField):
                gql_type = GraphQLInt
            else:
                gql_type = None
            if gql_type is not None:
                schema[field_name] = GraphQLField(gql_type)
        return GraphQLObjectType(self.serializer.__name__, lambda: schema)

    @property
    def query_multiple(self):
        pass
