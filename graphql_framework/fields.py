from rest_framework.fields import Field, SerializerMethodField

# IDEA: Possible implementations -@flyte at 07/08/2020, 17:13:25
# Should this field_type be an instance of Field instead?


class TypedSerializerMethodField(SerializerMethodField):
    def __init__(self, field_type, *args, **kwargs):
        self.field_type = field_type
        super().__init__(*args, **kwargs)


class ModelPropertyField(Field):
    def __init__(self, field_type, property_name, *args, **kwargs):
        self.field_type = field_type
        self.property_name = property_name
        super().__init__(*args, **kwargs)


class ModelMethodField(Field):
    def __init__(
        self,
        field_type,
        method_name,
        *args,
        method_args=None,
        method_kwargs=None,
        **kwargs
    ):
        if method_args is None:
            method_args = ()
        if method_kwargs is None:
            method_kwargs = {}
        self.field_type = field_type
        self.method_name = method_name
        self.method_args = method_args
        self.method_kwargs = method_kwargs
        super().__init__(*args, **kwargs)

