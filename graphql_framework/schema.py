from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models
from graphql import (
    GraphQLArgument,
    GraphQLField,
    GraphQLInputField,
    GraphQLInputObjectType,
    GraphQLInt,
    GraphQLList,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLSchema,
)
from rest_framework.fields import SerializerMethodField
from rest_framework.relations import (
    ManyRelatedField,
    PrimaryKeyRelatedField,
    RelatedField,
)

from graphql_framework.fields import (
    ModelMethodField,
    ModelPropertyField,
    TypedSerializerMethodField,
)

from .converter import to_gql_type

if TYPE_CHECKING:
    # pylint: disable=ungrouped-imports
    from typing import Dict, Type
    from rest_framework.serializers import ModelSerializer
    from rest_framework.fields import Field as SerializerField
    from django.db.models import Model
    from django.db.models import QuerySet


class classproperty(object):
    def __init__(self, f):
        self.f = f

    def __get__(self, obj, owner):
        return self.f(owner)


def serializer_field_to_gql_field(serializer_field: Type[SerializerField], **kwargs):
    nullable = None
    if isinstance(
        serializer_field,
        (TypedSerializerMethodField, ModelPropertyField, ModelMethodField),
    ):
        nullable = not serializer_field.required
        serializer_field = serializer_field.field_type()
    try:
        gql_type = to_gql_type(serializer_field, nullable=nullable)
    except NotImplementedError:
        return None
    return GraphQLField(gql_type, **kwargs)


class Schema:
    _types = {}  # type: Dict[str, ModelSerializerType]
    _schema = None  # type: GraphQLSchema
    objecttype_registry = {}  # type: Dict[Type[Model], GraphQLObjectType]
    modelserializer_registry = {}  # type: Dict[Type[Model], ModelSerializer]

    def __init_subclass__(cls):
        # See what fields were added and add those to our schema
        cls._types.update(
            {
                k: v
                for k, v in cls.__dict__.items()
                if not k.startswith("_") and isinstance(v, ModelSerializerType)
            }
        )
        # cls._update_schema()

    @classproperty
    def schema(cls):
        if cls._schema is None:
            cls._update_schema()
        return cls._schema

    @classmethod
    def register_type(cls, type_: "ModelSerializerType"):
        """
        Register an ModelSerializerType in the schema registry for the model it's based on.
        """
        serializer = type_.serializer_cls()
        gql_fields = {}
        for field_name, field in serializer.fields.items():
            field_kwargs = {}
            if isinstance(field, TypedSerializerMethodField):

                def resolve_tsm_field(source, info, type_=type_, field=field, **kwargs):
                    return getattr(type_.serializer_cls(source), field.method_name)(
                        source
                    )

                field_kwargs["resolve"] = resolve_tsm_field
            elif isinstance(field, ModelPropertyField):

                def resolve_mp_field(source, info, type_=type_, field=field, **kwargs):
                    return getattr(source, field.property_name)

                field_kwargs["resolve"] = resolve_mp_field
            elif isinstance(field, ModelMethodField):

                def resolve_mm_field(source, info, type_=type_, field=field, **kwargs):
                    func = getattr(source, field.method_name)
                    return func(*field.method_args, **field.method_kwargs)

                field_kwargs["resolve"] = resolve_mm_field
            gql_field = serializer_field_to_gql_field(field, **field_kwargs)
            if gql_field is None:
                continue
            gql_fields[field_name] = gql_field
        cls.objecttype_registry[type_.model] = GraphQLObjectType(type_.name, gql_fields)
        cls.modelserializer_registry[type_.model] = type_

    @classmethod
    def _update_registry(cls):
        # NOTE: Needs discussion or investigation -@flyte at 10/08/2020, 11:58:16
        # Currently this will only allow for one ModelSerializer per Model.
        # Is this an issue?

        # Create all of the ObjectTypes without any relations
        for type_ in cls._types.values():
            cls.register_type(type_)

    @classmethod
    def _update_schema(cls):
        """
        Update the schema attribute with the latest additions.

        Create all top level ObjectTypes first, without any relation fields, add them to
        the type registry. Run through the schemas and fields again now that the type
        registry is populated, modifying the ObjectTypes in the registry to include the
        relation fields.
        """
        # TODO: Tasks pending completion -@flyte at 18/08/2020, 10:39:19
        # Add any enums for choice fields

        # Go through each of the types in the registry and add any relation
        # fields using the existing entries.
        for type_ in cls._types.values():
            serializer = type_.serializer_cls()
            obj_type = cls.objecttype_registry[type_.model]
            for field_name, field in serializer.fields.items():
                if (
                    isinstance(field, RelatedField)
                    and field.queryset.model in cls.objecttype_registry
                ):
                    obj_type.fields[field_name] = GraphQLField(
                        cls.objecttype_registry[field.queryset.model]
                    )
                elif (
                    isinstance(field, ManyRelatedField)
                    and field.child_relation.queryset.model in cls.objecttype_registry
                ):

                    def field_resolver(source, info, **kwargs):
                        return getattr(source, info.field_name).all()

                    if field.child_relation.queryset.model in cls.objecttype_registry:
                        obj_type.fields[field_name] = GraphQLField(
                            GraphQLList(
                                cls.objecttype_registry[
                                    field.child_relation.queryset.model
                                ]
                            ),
                            resolve=field_resolver,
                        )

        # Create a blank query schema
        query = GraphQLObjectType("Query", {})

        # Add the singular and list types to the schema
        for toplevel_field_name, type_ in cls._types.items():
            serializer = type_.serializer_cls()
            singular_field_name = (
                None if type_.field is None else type_.field or toplevel_field_name
            )
            list_field_name = type_.list_field

            # Add args to look up objects across relations
            args = {}
            for field_name, field in serializer.fields.items():
                if (
                    not isinstance(field, RelatedField)
                    or field.queryset.model not in cls.objecttype_registry
                ):
                    continue
                for relation_field_name, relation_field in cls.objecttype_registry[
                    field.queryset.model
                ].fields.items():
                    # Don't add a lookup arg for SerializerMethodFields
                    if isinstance(
                        cls.modelserializer_registry[field.queryset.model]
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
                    # Skip reverse relation fields (from related_name)
                    if isinstance(relation_field_type, GraphQLObjectType):
                        continue
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

            # TODO: Tasks pending completion -@flyte at 10/08/2020, 15:40:26
            # Add pagination args

            if singular_field_name is not None:

                def resolve_singular(root, info, type_=type_, **kwargs):
                    return type_.queryset.get(**kwargs)

                query.fields[singular_field_name] = GraphQLField(
                    cls.objecttype_registry[type_.model],
                    args=args
                    if type_.singular_lookup_fields is None
                    else {k: args[k] for k in type_.singular_lookup_fields},
                    resolve=resolve_singular,
                )
            if list_field_name is not None:

                def resolve_list(root, info, type_=type_, **kwargs):
                    return type_.queryset.filter(**kwargs)

                query.fields[list_field_name] = GraphQLField(
                    GraphQLList(cls.objecttype_registry[type_.model]),
                    args=args
                    if type_.list_lookup_fields is None
                    else {k: args[k] for k in type_.list_lookup_fields},
                    resolve=resolve_list,
                )

        # TODO: Tasks pending completion -@flyte at 12/08/2020, 12:53:00
        # Allow for mutations based on serializer methods

        mutation = GraphQLObjectType("Mutation", {})
        for toplevel_field_name, type_ in cls._types.items():
            if not type_.create_mutation and not type_.update_mutation:
                continue
            serializer = type_.serializer_cls()
            # TODO: Tasks pending completion -@flyte at 11/08/2020, 12:11:23
            # Get the name of the input object
            create_object_type = GraphQLInputObjectType(f"Create{type_.name}", {})
            for field_name, field in serializer.fields.items():
                if field.read_only or isinstance(field, ManyRelatedField):
                    continue
                gql_type = None
                if isinstance(field, RelatedField):
                    if isinstance(field, PrimaryKeyRelatedField):
                        # TODO: Tasks pending completion -@flyte at 11/08/2020, 17:53:41
                        # Make a module to convert Django types to GraphQL ones
                        model_pk_type = field.queryset.model._meta.pk
                        if isinstance(model_pk_type, models.AutoField):
                            gql_type = GraphQLNonNull(GraphQLInt)
                    # TODO: Tasks pending completion -@flyte at 11/08/2020, 17:55:19
                    # Set gql_type for other field types as well
                if gql_type is None:
                    try:
                        gql_type = to_gql_type(field, nullable=not field.required)
                    except NotImplementedError:
                        continue
                create_object_type.fields[field_name] = GraphQLInputField(gql_type)

            def resolve_create(
                root, info, type_=type_, data_name=toplevel_field_name, **kwargs
            ):
                data = kwargs[data_name]
                serializer = type_.serializer_cls(data=data)
                if not serializer.is_valid():
                    raise ValueError(serializer.errors)
                return serializer.save()

            if type_.create_mutation:
                mutation.fields[f"create_{toplevel_field_name}"] = GraphQLField(
                    cls.objecttype_registry[type_.model],
                    args={
                        toplevel_field_name: GraphQLArgument(
                            GraphQLNonNull(create_object_type)
                        )
                    },
                    resolve=resolve_create,
                )
            if not type_.update_mutation:
                continue

            update_object_type = GraphQLInputObjectType(
                f"Update{type_.name}", create_object_type.fields.copy()
            )
            # Remove all NonNulls
            for field_name, field in update_object_type.fields.items():
                if isinstance(field.type, GraphQLNonNull):
                    field.type = field.type.of_type

            def resolve_update(
                root, info, type_=type_, data_name=toplevel_field_name, **kwargs
            ):
                pk = kwargs[type_.model._meta.pk.name]
                data = kwargs[data_name]
                serializer = type_.serializer_cls(
                    type_.model.objects.get(pk=pk), data, partial=True
                )
                if not serializer.is_valid():
                    raise ValueError(serializer.errors)
                return serializer.save()

            # TODO: Tasks pending completion -@flyte at 12/08/2020, 12:17:05
            # Remove hardcoded Int for primary key and work out the right field type
            mutation.fields[f"update_{toplevel_field_name}"] = GraphQLField(
                cls.objecttype_registry[type_.model],
                args={
                    type_.model._meta.pk.name: GraphQLArgument(
                        GraphQLNonNull(GraphQLInt)
                    ),
                    toplevel_field_name: GraphQLArgument(
                        GraphQLNonNull(update_object_type)
                    ),
                },
                resolve=resolve_update,
            )

            # Delete mutation
            if type_.delete_mutation:

                def resolve_delete(root, info, type_=type_, **kwargs):
                    pk = kwargs[type_.model._meta.pk.name]
                    instance = type_.queryset.get(pk=pk)
                    instance.delete()
                    return instance

                # TODO: Tasks pending completion -@flyte at 26/08/2020, 10:46:55
                # Remove hardcoded Int for primary key and work out the right field type
                mutation.fields[f"delete_{toplevel_field_name}"] = GraphQLField(
                    cls.objecttype_registry[type_.model],
                    args={
                        type_.model._meta.pk.name: GraphQLArgument(
                            GraphQLNonNull(GraphQLInt)
                        )
                    },
                    resolve=resolve_delete,
                )

        cls._schema = GraphQLSchema(query, mutation)


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
        create_mutation: bool = True,
        update_mutation: bool = True,
        delete_mutation: bool = True,
    ):
        self.name = name or self.__class__.__name__
        self.singular_lookup_fields = singular_lookup_fields
        self.list_lookup_fields = list_lookup_fields
        self.field = field
        self.list_field = list_field
        self.queryset = queryset if queryset is not None else self.model.objects.all()
        self.create_mutation = create_mutation
        self.update_mutation = update_mutation
        self.delete_mutation = delete_mutation
        Schema.register_type(self)
