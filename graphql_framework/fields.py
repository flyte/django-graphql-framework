from rest_framework.fields import SerializerMethodField

# IDEA: Possible implementations -@flyte at 07/08/2020, 17:13:25
# Should this field_type be an instance of Field instead?


class TypedSerializerMethodField(SerializerMethodField):
    def __init__(self, field_type, *args, **kwargs):
        self.field_type = field_type
        super().__init__(*args, **kwargs)
