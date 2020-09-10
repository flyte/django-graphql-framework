from importlib import import_module

from django.conf import settings
from django.contrib import admin
from django.urls import include, path

from .views import graphql

gql_view = graphql
for func_path in getattr(settings, "GRAPHQL_FRAMEWORK_GQL_VIEW_WRAPPERS", []):
    module_name, func_name = func_path.rsplit(".", 1)
    module = import_module(module_name)
    wrapper_func = getattr(module, func_name)
    gql_view = wrapper_func(gql_view)

urlpatterns = [path("", gql_view)]
