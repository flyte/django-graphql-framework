from __future__ import annotations

from typing import TYPE_CHECKING

from graphql import GraphQLArgument, GraphQLField, GraphQLObjectType, GraphQLSchema
from graphql.type.scalars import GraphQLInt
from rest_framework.relations import RelatedField

from graphql_framework.fields import TypedSerializerMethodField

from .converter import to_gql_type

if TYPE_CHECKING:
    from typing import Dict, Type
    from rest_framework.serializers import ModelSerializer
    from django.db.models import Model
    from django.db.models import QuerySet


class Schema:
    _schemas = {}  # type: Dict[str, ModelSerializerSchema]
    schema = None
    objecttype_registry = {}  # type: Dict[str, GraphQLObjectType]

    def __init_subclass__(cls):
        # See what fields were added and add those to our schema
        Schema._schemas.update(
            {
                k: v
                for k, v in cls.__dict__.items()
                if not k.startswith("_") and isinstance(v, ModelSerializerSchema)
            }
        )
        Schema._update_schema()

    # IDEA: Possible implementations -@flyte at 07/08/2020, 12:52:52
    # Recursive function to follow relations and create/add their ObjectTypes to the registry?

    @classmethod
    def _update_schema(cls):
        """
        Update the schema attribute with the latest additions.
        """
        objecttypes_required = set()
        for field_name, schema in cls._schemas.items():
            serializer = schema.serializer_cls()
            serializer_related_fields = [
                field for field in serializer.fields if isinstance(field, RelatedField)
            ]  # type: List[RelatedField]
            for related_field in serializer_related_fields:
                print(related_field)

    # @classmethod
    # def as_schema(cls):
    #     return GraphQLSchema(GraphQLObjectType("Query", lambda: Schema.fields))


class ModelSerializerSchema:
    """
    Turns a Django REST Framework Serializer into a GraphQL CRUD schema.
    """

    serializer_cls = None  # type: Type[ModelSerializer]
    model = None  # type: Type[Model]

    def __init_subclass__(cls, serializer_cls: Type[ModelSerializer]):
        cls.serializer_cls = serializer_cls
        cls.model = serializer_cls.Meta.model

    def __init__(
        self,
        lookup_fields: tuple = None,
        field: str = None,
        list_field: str = None,
        queryset: QuerySet = None,
    ):
        self.lookup_fields = lookup_fields if lookup_fields is not None else ("id",)
        self.field = field
        self.list_field = list_field
        self.queryset = queryset if queryset is not None else self.model.objects.all()

    # @classmethod
    # def get_singular(cls, root, info, **kwargs):
    #     if cls.model is None:
    #         raise NotImplementedError(
    #             "Must provide either a model or get_singular() function"
    #         )
    #     if not kwargs:
    #         raise ValueError(
    #             "Must provide a way of looking up the object: %s"
    #             % (cls.singular_lookup_fields,)
    #         )
    #     serializer = cls.serializer_cls(cls.model.objects.get(**kwargs))
    #     return serializer.data

    # @classmethod
    # def field_singular(cls, lookup_fields=None):
    #     cls.singular_lookup_fields = lookup_fields or ("id",)
    #     object_type = Schema.type_registry.get(cls.serializer_cls.__name__)

    #     if object_type is None:
    #         # TODO: Tasks pending completion -@flyte at 06/08/2020, 17:24:09
    #         # Put this in a separate function

    #         # Create a new ObjectType and add it to the registry
    #         serializer = cls.serializer_cls()
    #         schema = dict()
    #         for field_name, field in serializer.fields.items():
    #             if isinstance(field, RelatedField):
    #                 # Schema.type_registry.get(cls.)
    #                 pass
    #             nullable = None
    #             if isinstance(field, TypedSerializerMethodField):
    #                 nullable = not field.required
    #                 field = field.field_type()
    #             try:
    #                 gql_type = to_gql_type(field, nullable=nullable)
    #             except NotImplementedError:
    #                 continue
    #             schema[field_name] = GraphQLField(gql_type)
    #         # Only set the args as required if there's only one
    #         args_nullable = len(cls.singular_lookup_fields) > 1
    #         object_type = GraphQLObjectType(cls.serializer_cls.__name__, lambda: schema)
    #         Schema.type_registry[cls.serializer_cls.__name__] = object_type

    #     return GraphQLField(
    #         object_type,
    #         args={
    #             arg: GraphQLArgument(
    #                 to_gql_type(serializer.fields[arg], nullable=args_nullable)
    #             )
    #             for arg in cls.singular_lookup_fields
    #         },
    #         resolve=cls.get_singular,
    #     )
