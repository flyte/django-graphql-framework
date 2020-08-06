from graphql import GraphQLArgument, GraphQLField, GraphQLObjectType, GraphQLSchema
from graphql.type.scalars import GraphQLInt
from rest_framework.fields import SerializerMethodField

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

    singular_lookup_fields = ()

    def __init_subclass__(cls, serializer_cls, model=None):
        cls.serializer_cls = serializer_cls
        cls.model = model

    @classmethod
    def get(cls, root, info, **kwargs):
        if cls.model is None:
            raise NotImplementedError("Must provide either a model or get() function")
        if not kwargs:
            raise ValueError(
                "Must provide a way of looking up the object: %s, or a get() function"
                % (cls.singular_lookup_fields,)
            )
        serializer = cls.serializer_cls(cls.model.objects.get(**kwargs))
        return serializer.data

    @classmethod
    def field_singular(cls, lookup_fields=None):
        cls.singular_lookup_fields = lookup_fields or ("id",)
        # Figure out the fields on the serializer, turn them into graphql ones
        serializer = cls.serializer_cls()
        schema = dict()
        for field_name, field in serializer.fields.items():
            nullable = None
            if isinstance(field, SerializerMethodField):
                try:
                    nullable = not field.required
                    field = getattr(serializer, field.method_name).return_type()
                except AttributeError:
                    continue
            try:
                gql_type = to_gql_type(field, nullable=nullable)
            except NotImplementedError:
                continue
            schema[field_name] = GraphQLField(gql_type)
        # Only set the args as required if there's only one
        args_nullable = len(cls.singular_lookup_fields) > 1
        return GraphQLField(
            GraphQLObjectType(cls.serializer_cls.__name__, lambda: schema),
            args={
                arg: GraphQLArgument(
                    to_gql_type(serializer.fields[arg], nullable=args_nullable)
                )
                for arg in cls.singular_lookup_fields
            },
            resolve=cls.get,
        )

    @classmethod
    def field_list(cls):
        pass
