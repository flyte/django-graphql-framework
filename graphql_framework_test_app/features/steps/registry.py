import graphql
from behave import given, then, when  # pylint: disable=no-name-in-module
from graphql import GraphQLField, GraphQLNonNull, GraphQLObjectType, GraphQLString

from graphql_framework.schema import Schema


@when("{type_name} type is added to the registry")
def step(context, type_name):
    Schema.register_type(context.data["types"][type_name])


@then("{type_name} type exists in the registry for {model_name} model")
def step(context, type_name, model_name):
    type_ = Schema.objecttype_registry[context.data["models"][model_name]]
    assert type_.name == context.data["types"][type_name].name


@then("Registry entry for {model_name} model is a GraphQLObjectType")
def step(context, model_name):
    type_ = Schema.objecttype_registry[context.data["models"][model_name]]
    assert isinstance(type_, GraphQLObjectType)


@then(
    "Registry entry for {model_name} model has test field converted to GraphQL {gql_field_type} field"
)
def step_impl(context, model_name, gql_field_type):
    model = context.data["models"][model_name]
    object_type = Schema.objecttype_registry[model]
    model_field = getattr(model, "test_field").field
    gql_field = object_type.fields["test_field"]
    desired_gql_type = type(getattr(graphql, gql_field_type))
    assert isinstance(gql_field, GraphQLField)
    if model_field.null:
        assert isinstance(gql_field.type, GraphQLNonNull)
        assert isinstance(gql_field.type.of_type, desired_gql_type)
    else:
        assert isinstance(gql_field.type.of_type, desired_gql_type)
