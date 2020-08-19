from behave import given, then, when  # pylint: disable=no-name-in-module
from graphql_framework.schema import ModelSerializerType


@given("{type_name} type exists for {serializer_name} serializer")
def step(context, type_name, serializer_name):
    context.data["types"][type_name] = type(
        type_name,
        (ModelSerializerType,),
        {},
        serializer_cls=context.data["serializers"][serializer_name],
    )()
