from behave import given, then, when  # pylint: disable=no-name-in-module
from django.db import models


@given("{model_name} model exists")
def step(context, model_name):
    context.data["models"][model_name] = type(
        model_name, (models.Model,), {"__module__": "graphql_framework_test_app"}
    )
