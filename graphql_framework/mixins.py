from rest_framework.serializers import ModelSerializer


class ModelSerializerExtraFieldsMixin:
    def get_field_names(self, declared_fields, info):
        fields = super().get_field_names(declared_fields, info)
        return fields + getattr(self.Meta, "extra_fields", [])
