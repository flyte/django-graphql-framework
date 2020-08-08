from __future__ import annotations

from typing import TYPE_CHECKING

from graphql import (
    GraphQLArgument,
    GraphQLField,
    GraphQLObjectType,
    GraphQLSchema,
    GraphQLList,
)
from graphql.type.scalars import GraphQLInt
from rest_framework.relations import RelatedField

from graphql_framework.fields import TypedSerializerMethodField

from .converter import to_gql_type

if TYPE_CHECKING:
    from typing import Dict, Type
    from rest_framework.serializers import ModelSerializer
    from rest_framework.fields import Field as SerializerField
    from django.db.models import Model
    from django.db.models import QuerySet


def serializer_field_to_gql_field(serializer_field: Type[SerializerField]):
    nullable = None
    if isinstance(serializer_field, TypedSerializerMethodField):
        nullable = not serializer_field.required
        serializer_field = serializer_field.field_type()
    try:
        gql_type = to_gql_type(serializer_field, nullable=nullable)
    except NotImplementedError:
        return None
    return GraphQLField(gql_type)


class Schema:
    _types = {}  # type: Dict[str, ModelSerializerType]
    schema = None  # type: GraphQLSchema
    objecttype_registry = {}  # type: Dict[str, GraphQLObjectType]

    def __init_subclass__(cls):
        # See what fields were added and add those to our schema
        Schema._types.update(
            {
                k: v
                for k, v in cls.__dict__.items()
                if not k.startswith("_") and isinstance(v, ModelSerializerType)
            }
        )
        Schema._update_schema()

    # IDEA: Possible implementations -@flyte at 07/08/2020, 12:52:52
    # Recursive function to follow relations and create/add their ObjectTypes to the registry?

    @classmethod
    def _update_schema(cls):
        """
        Update the schema attribute with the latest additions.

        Create all top level ObjectTypes first, without any relation fields, add them to
        the type registry. Run through the schemas and fields again now that the type
        registry is populated, modifying the ObjectTypes in the registry to include the
        relation fields.
        """
        objecttype_registry = {}  # type: Dict[Model, GraphQLObjectType]
        # Create all of the ObjectTypes without any relations
        for type_ in cls._types.values():
            serializer = type_.serializer_cls()
            gql_fields = {}
            for field_name, field in serializer.fields.items():
                gql_field = serializer_field_to_gql_field(field)
                if gql_field is None:
                    continue
                gql_fields[field_name] = gql_field
            objecttype_registry[type_.model] = GraphQLObjectType(type_.name, gql_fields)

        # Now go through them all again, and add any relation fields using the
        # objecttype registry.
        for type_ in cls._types.values():
            serializer = type_.serializer_cls()
            obj_type = objecttype_registry[type_.model]
            for field_name, field in serializer.fields.items():
                if not isinstance(field, RelatedField):
                    continue
                obj_type.fields[field_name] = GraphQLField(
                    objecttype_registry[field.queryset.model]
                )

        # TODO: Tasks pending completion -@flyte at 08/08/2020, 08:19:46
        # Implement resolver functions

        # Add the singular and list types
        query = GraphQLObjectType("Query", {})
        for toplevel_field_name, type_ in cls._types.items():
            serializer = type_.serializer_cls()
            singular_field_name = (
                None if type_.field is None else type_.field or toplevel_field_name
            )
            list_field_name = type_.list_field
            if singular_field_name is not None:

                def resolve_singular(root, info, type_=type_, **kwargs):
                    return type_.queryset.get(**kwargs)

                args_nullable = len(type_.lookup_fields) > 1
                query.fields[singular_field_name] = GraphQLField(
                    objecttype_registry[type_.model],
                    args={
                        arg: GraphQLArgument(
                            to_gql_type(serializer.fields[arg], nullable=args_nullable)
                        )
                        for arg in type_.lookup_fields
                    },
                    resolve=resolve_singular,
                )
            if list_field_name is not None:

                def resolve_list(root, info, type_=type_, **kwargs):
                    return type_.queryset.filter(**kwargs)

                query.fields[list_field_name] = GraphQLField(
                    GraphQLList(objecttype_registry[type_.model]),
                    args={
                        arg: GraphQLArgument(
                            to_gql_type(serializer.fields[arg], nullable=True)
                        )
                        for arg in type_.lookup_fields
                    },
                    resolve=resolve_list,
                )

        # TODO: Tasks pending completion -@flyte at 08/08/2020, 08:58:04
        # Add mutations

        Schema.schema = GraphQLSchema(query)
        print(Schema.schema)

    # @classmethod
    # def as_schema(cls):
    #     return GraphQLSchema(GraphQLObjectType("Query", lambda: Schema.fields))


class ModelSerializerType:
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
        name: str = None,
        lookup_fields: tuple = None,
        field: str = "",
        list_field: str = None,
        queryset: QuerySet = None,
    ):
        self.name = name or self.__class__.__name__
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
