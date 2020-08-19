CONTEXT_DATA = dict(models={}, serializers={}, types={})


def before_all(context):
    context.data = CONTEXT_DATA
