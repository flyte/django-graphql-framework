from rest_framework.fields import SerializerMethodField


class TypedSerializerMethodField(SerializerMethodField):
    def __init__(self, field_type, *args, **kwargs):
        self.field_type = field_type
        super().__init__(*args, **kwargs)
