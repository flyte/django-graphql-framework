import json
from importlib import import_module

from django.conf import settings
from django.http.response import (
    HttpResponseBadRequest,
    HttpResponseNotAllowed,
    JsonResponse,
)
from django.views.generic import TemplateView
from graphql import GraphQLObjectType, GraphQLSchema, build_schema, graphql_sync

from .schema import Schema


class Root:
    def human(self, info, id):
        return dict(name="Chuck Norris")


def graphql(request):
    if request.method.lower() not in ("get", "post"):
        return HttpResponseNotAllowed("This view only accepts GET or POST requests")

    def content_type(ctype):
        return ctype.lower().strip()

    http_accept_types = map(
        content_type, request.META.get("HTTP_ACCEPT", "text/html").split(",")
    )

    if "application/json" not in http_accept_types:
        return GraphiQL.as_view()(request)

    return process_graphql_req(request)


def process_graphql_req(request):
    try:
        if request.method.lower() == "get":
            query = request.GET["query"]
            variables = request.GET.get("variables")
            qid = request.GET.get("id")
            operation_name = request.GET.get("operationName")
        elif request.method.lower() == "post":
            query = request.POST["query"]
            variables = request.POST.get("variables")
            qid = request.POST.get("id")
            operation_name = request.POST.get("operationName")
        else:
            raise Exception("Cannot process GraphQL request that isn't a GET or POST")
    except KeyError:
        return HttpResponseBadRequest("Must include 'query' parameter")
    if variables is not None:
        variables = json.loads(variables)
    schema = GraphQLSchema(GraphQLObjectType("Query", lambda: Schema.registry))
    result = graphql_sync(
        schema, query, Root(), variable_values=variables, operation_name=operation_name
    )
    ret = dict(data=result.data, errors=[])
    if result.errors:
        for err in result.errors:
            ret["errors"].append(err.formatted)
    if qid is not None:
        ret["id"] = qid
    return JsonResponse(ret)


class GraphiQL(TemplateView):
    template_name = "graphql_framework/graphiql.html"
