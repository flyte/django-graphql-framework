import json
from importlib import import_module

from django.conf import settings
from django.http.response import (
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseNotAllowed,
    JsonResponse,
)
from django.views.generic import TemplateView
from graphql import GraphQLObjectType, GraphQLSchema, build_schema, graphql_sync

from .schema import Schema


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


def get_query_data_from_request(request):
    try:
        if request.method.lower() == "get":
            query = request.GET["query"]
        else:
            query = request.POST["query"]
    except KeyError:
        return (
            None,
            None,
            None,
            None,
            HttpResponseBadRequest("Must include 'query' parameter"),
        )
    variables = request.GET.get("variables", request.POST.get("variables"))
    qid = request.GET.get("id", request.POST.get("id"))
    operation_name = request.GET.get("operationName", request.POST.get("operationName"))
    return query, variables, qid, operation_name, None


def process_graphql_req(request):
    query, variables, qid, operation_name, error = get_query_data_from_request(request)
    if error is not None:
        return error
    if variables is not None:
        variables = json.loads(variables)
    result = graphql_sync(
        Schema.as_schema(),
        query,
        None,
        variable_values=variables,
        operation_name=operation_name,
    )
    ret = dict(data=result.data, errors=[err.formatted for err in result.errors or []])
    if qid is not None:
        ret["id"] = qid
    return JsonResponse(ret)


class GraphiQL(TemplateView):
    template_name = "graphql_framework/graphiql.html"
