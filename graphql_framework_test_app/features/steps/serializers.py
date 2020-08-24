from behave import given, then, when  # pylint: disable=no-name-in-module
from rest_framework import fields as rest_framework_fields
from rest_framework.serializers import ModelSerializer

from graphql_framework.fields import TypedSerializerMethodField


@given("Serializer exists for {model_name} model")
def step(context, model_name):
    context.data["serializers"][model_name] = type(
        f"{model_name}Serializer",
        (ModelSerializer,),
        {
            "Meta": type(
                "Meta",
                (),
                dict(model=context.data["models"][model_name], fields="__all__"),
            )
        },
    )


@given(
    "Serializer exists for {model_name} model with a {field_type} TypedSerializerMethodField"
)
def step_impl(context, model_name, field_type):
    def get_test_field(self):
        if field_type == "CharField":
            return "Hello"
        elif field_type == "IntField":
            return 1

    context.data["serializers"][model_name] = type(
        f"{model_name}Serializer",
        (ModelSerializer,),
        dict(
            Meta=type(
                "Meta",
                (),
                dict(model=context.data["models"][model_name], fields=["test_field"]),
            ),
            get_test_field=get_test_field,
            test_field=TypedSerializerMethodField(
                getattr(rest_framework_fields, field_type), method_name="get_test_field"
            ),
        ),
    )
