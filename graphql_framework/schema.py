from graphql import GraphQLArgument, GraphQLField, GraphQLObjectType, GraphQLSchema
from graphql.type.scalars import GraphQLInt
from rest_framework.fields import IntegerField

from .converter import to_gql_type


class Schema:
    fields = {}

    def __init_subclass__(cls):
        # See what fields were added and add those to our schema
        Schema.fields.update(
            {
                k: v
                for k, v in cls.__dict__.items()
                if not k.startswith("_") and isinstance(v, GraphQLField)
            }
        )

    @classmethod
    def as_schema(cls):
        return GraphQLSchema(GraphQLObjectType("Query", lambda: Schema.fields))


class SerializerSchema:
    """
    Turns a Django REST Framework Serializer into a GraphQL CRUD schema.
    """

    def __init_subclass__(cls, serializer, model=None):
        cls.serializer = serializer
        cls.model = model

    @classmethod
    def get(cls, root, info, id):
        if cls.model is None:
            raise NotImplementedError("Must provide either a model or get() function")
        return cls.model.objects.get(pk=id)

    @classmethod
    def field_singular(cls, args=None):
        if args is None:
            args = ()
        # Figure out the fields on the serializer, turn them into graphql ones
        serializer = cls.serializer()
        schema = dict()
        for field_name, field in serializer.fields.items():
            try:
                gql_type = to_gql_type(field)
            except NotImplementedError:
                continue
            schema[field_name] = GraphQLField(gql_type)
        return GraphQLField(
            GraphQLObjectType(cls.serializer.__name__, lambda: schema),
            args={
                arg: GraphQLArgument(to_gql_type(serializer.fields[arg]))
                for arg in args
            },
            resolve=cls.get,
        )

    @classmethod
    def field_list(cls):
        pass
