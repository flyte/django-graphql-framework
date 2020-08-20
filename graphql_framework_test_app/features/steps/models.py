from behave import given, then, when  # pylint: disable=no-name-in-module
from django.db import models


@given("{model_name} model exists")
def step(context, model_name):
    context.data["models"][model_name] = type(
        model_name, (models.Model,), {"__module__": "graphql_framework_test_app"}
    )


@given("{model_name} model exists with a {field_type} test field")
def step(context, model_name, field_type):
    field_args = []
    field_kwargs = {}
    if field_type == "CharField":
        field_kwargs["max_length"] = 128
    field_cls = getattr(models, field_type)
    context.data["models"][model_name] = type(
        model_name,
        (models.Model,),
        {
            "__module__": "graphql_framework_test_app",
            "test_field": field_cls(*field_args, **field_kwargs),
        },
    )

