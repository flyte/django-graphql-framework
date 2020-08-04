from graphql import GraphQLField, GraphQLObjectType


# def query(cls):
#     for attr in cls.__dict__:
#         if attr.startswith("_"):
#             continue
#         # SCHEMA[attr] = getattr(cls, attr)
#         SCHEMA[attr] = GraphQLField(getattr(cls, attr))
#     print(SCHEMA)
