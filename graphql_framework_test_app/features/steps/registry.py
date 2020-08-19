from behave import given, then, when  # pylint: disable=no-name-in-module
from graphql_framework.schema import Schema


@when("{type_name} type is added to the registry")
def step(context, type_name):
    Schema.register_type(context.data["types"][type_name])


@then("{type_name} type exists in the registry for {model_name} model")
def step(context, type_name, model_name):
    type_ = Schema.objecttype_registry[context.data["models"][model_name]]
    assert type_.name == context.data["types"][type_name].name
