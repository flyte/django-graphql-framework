from functools import wraps

from graphql import GraphQLField, GraphQLObjectType

# def query(cls):
#     for attr in cls.__dict__:
#         if attr.startswith("_"):
#             continue
#         # SCHEMA[attr] = getattr(cls, attr)
#         SCHEMA[attr] = GraphQLField(getattr(cls, attr))
#     print(SCHEMA)


def returns(field_type, null=False):
    def decorator(func):
        func.return_type = field_type
        func.returns_null = null
        return func
    return decorator
