from django.apps import AppConfig


class GraphQLTestAppConfig(AppConfig):
    name = "graphql_framework_test_app"
    verbose_name = "GraphQL Framework Test App"

    def ready(self):
        from . import schema
