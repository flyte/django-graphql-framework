from functools import singledispatch

from graphql import GraphQLNonNull
from graphql.type import scalars
from rest_framework import fields


@singledispatch
def to_gql_type(field, nullable=None):
    raise NotImplementedError("This type has no convertor available")


def add_non_null(field, scalar, nullable=None):
    if nullable:
        return scalar
    if field.required:
        return GraphQLNonNull(scalar)
    return scalar


@to_gql_type.register(fields.BooleanField)
def convert_boolean(field, nullable=None):
    return add_non_null(field, scalars.GraphQLBoolean, nullable)


@to_gql_type.register(fields.CharField)
@to_gql_type.register(fields.EmailField)
@to_gql_type.register(fields.SlugField)
@to_gql_type.register(fields.URLField)
@to_gql_type.register(fields.IPAddressField)
@to_gql_type.register(fields.FileField)
@to_gql_type.register(fields.FilePathField)
@to_gql_type.register(fields.DateTimeField)
@to_gql_type.register(fields.DateField)
@to_gql_type.register(fields.TimeField)
@to_gql_type.register(fields.JSONField)
def convert_string(field, nullable=None):
    return add_non_null(field, scalars.GraphQLString, nullable)


@to_gql_type.register(fields.UUIDField)
def convert_uuid(field, nullable=None):
    return add_non_null(field, scalars.GraphQLID, nullable)


@to_gql_type.register(fields.IntegerField)
def convert_int(field, nullable=None):
    return add_non_null(field, scalars.GraphQLInt, nullable)


@to_gql_type.register(fields.NullBooleanField)
@to_gql_type.register(fields.BooleanField)
def convert_bool(field, nullable=None):
    return add_non_null(field, scalars.GraphQLBoolean, nullable)


@to_gql_type.register(fields.DecimalField)
@to_gql_type.register(fields.FloatField)
@to_gql_type.register(fields.DurationField)
def convert_float(field, nullable=None):
    return add_non_null(field, scalars.GraphQLFloat, nullable)

