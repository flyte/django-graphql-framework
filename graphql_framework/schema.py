from graphql import GraphQLArgument, GraphQLField, GraphQLObjectType
from graphql.type.scalars import GraphQLInt
from rest_framework.fields import IntegerField

from .converter import to_gql_type


class Schema:
    registry = {}

    def __init_subclass__(cls):
        # See what fields were added and add those to our schema
        fields = {
            k: v
            for k, v in cls.__dict__.items()
            if not k.startswith("_") and isinstance(v, GraphQLField)
        }
        Schema.registry.update(fields)


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
            try:
                gql_type = to_gql_type(field)
            except NotImplementedError:
                continue
            schema[field_name] = GraphQLField(gql_type)
        return GraphQLField(
            GraphQLObjectType(self.serializer.__name__, lambda: schema),
            args=dict(id=GraphQLArgument(GraphQLInt)),
        )

    @property
    def query_multiple(self):
        pass
