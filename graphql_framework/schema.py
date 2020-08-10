from __future__ import annotations

from typing import TYPE_CHECKING

from graphql import (
    GraphQLArgument,
    GraphQLField,
    GraphQLList,
    GraphQLObjectType,
    GraphQLSchema,
)
from rest_framework.fields import SerializerMethodField
from rest_framework.relations import RelatedField

from graphql_framework.fields import TypedSerializerMethodField

from .converter import to_gql_type

if TYPE_CHECKING:
    # pylint: disable=ungrouped-imports
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
        # NOTE: Needs discussion or investigation -@flyte at 10/08/2020, 11:58:16
        # Currently this will only allow for one ModelSerializer per Model.
        # Is this an issue?
        objecttype_registry = {}  # type: Dict[Model, GraphQLObjectType]
        modelserializer_registry = {}  # type: Dict[Model, ModelSerializer]
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
            modelserializer_registry[type_.model] = type_

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

        # Add the singular and list types
        query = GraphQLObjectType("Query", {})
        for toplevel_field_name, type_ in cls._types.items():
            serializer = type_.serializer_cls()
            singular_field_name = (
                None if type_.field is None else type_.field or toplevel_field_name
            )
            list_field_name = type_.list_field

            # Add args to look up objects across relations
            args = {}
            for field_name, field in serializer.fields.items():
                if not isinstance(field, RelatedField):
                    continue
                for relation_field_name, relation_field in objecttype_registry[
                    field.queryset.model
                ].fields.items():
                    # Don't add a lookup arg for SerializerMethodFields
                    if isinstance(
                        modelserializer_registry[field.queryset.model]
                        .serializer_cls()
                        .fields[relation_field_name],
                        SerializerMethodField,
                    ):
                        continue
                    relation_field_type = relation_field.type
                    # Remove the NotNullable wrapper.
                    # TODO: How does this affect list types?
                    try:
                        relation_field_type = relation_field_type.of_type
                    except AttributeError:
                        pass
                    arg = GraphQLArgument(relation_field_type)
                    args[f"{field_name}__{relation_field_name}"] = arg

            # Add all local fields too
            for field_name in serializer.fields.keys():
                try:
                    args[field_name] = GraphQLArgument(
                        to_gql_type(serializer.fields[field_name], nullable=True)
                    )
                except NotImplementedError:
                    continue

            if singular_field_name is not None:

                def resolve_singular(root, info, type_=type_, **kwargs):
                    return type_.queryset.get(**kwargs)

                query.fields[singular_field_name] = GraphQLField(
                    objecttype_registry[type_.model],
                    args=args
                    if type_.singular_lookup_fields is None
                    else {k: args[k] for k in type_.singular_lookup_fields},
                    resolve=resolve_singular,
                )
            if list_field_name is not None:

                def resolve_list(root, info, type_=type_, **kwargs):
                    return type_.queryset.filter(**kwargs)

                query.fields[list_field_name] = GraphQLField(
                    GraphQLList(objecttype_registry[type_.model]),
                    args=args
                    if type_.list_lookup_fields is None
                    else {k: args[k] for k in type_.list_lookup_fields},
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
        singular_lookup_fields: tuple = None,
        list_lookup_fields: tuple = None,
        field: str = "",
        list_field: str = None,
        queryset: QuerySet = None,
    ):
        self.name = name or self.__class__.__name__
        self.singular_lookup_fields = singular_lookup_fields
        self.list_lookup_fields = list_lookup_fields
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
