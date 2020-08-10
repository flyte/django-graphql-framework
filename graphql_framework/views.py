import json
from importlib import import_module

from django.conf import settings
from django.http.response import (
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseNotAllowed,
    JsonResponse,
)
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView
from graphql import GraphQLObjectType, GraphQLSchema, build_schema, graphql_sync

from .schema import Schema


@csrf_exempt
def graphql(request):
    if request.method.lower() == "options":
        resp = HttpResponse()
        resp["Allow"] = "GET,POST,OPTIONS"
        return resp
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
    def bad_req(reason):
        return (None, None, None, None, HttpResponseBadRequest(reason))

    if request.method.lower() == "post":
        try:
            body_data = json.loads(request.body)
        except ValueError as exc:
            return bad_req(str(exc))
        try:
            query = body_data["query"]
        except KeyError:
            return bad_req("Could not parse query from JSON body")
        variables = body_data.get("variables")
        operation_name = body_data.get("operationName")
        qid = body_data.get("id")
    else:
        try:
            query = request.GET["query"]
        except KeyError:
            return bad_req("Must include 'query' parameter")
        variables = request.GET.get("variables")
        operation_name = request.GET.get("operationName")
        qid = request.GET.get("id")
    return query, variables, qid, operation_name, None


def process_graphql_req(request):
    query, variables, qid, operation_name, error = get_query_data_from_request(request)
    if error is not None:
        return error
    result = graphql_sync(
        Schema.schema,
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["api_url"] = settings.GRAPHQL_FRAMEWORK.get("api_url", "/graphql/")
        return context
