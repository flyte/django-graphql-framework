from behave import given, then, when  # pylint: disable=no-name-in-module
from rest_framework.serializers import ModelSerializer


@given("{serializer_name} serializer exists for {model_name} model")
def step(context, serializer_name, model_name):
    context.data["serializers"][serializer_name] = type(
        serializer_name,
        (ModelSerializer,),
        {
            "Meta": type(
                "Meta",
                (),
                dict(model=context.data["models"][model_name], fields="__all__"),
            )
        },
    )
