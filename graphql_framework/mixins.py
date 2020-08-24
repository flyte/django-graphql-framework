from typing import List


class ModelSerializerExtraFieldsMixin:
    def get_field_names(self, declared_fields, info) -> List[str]:
        fields = super().get_field_names(declared_fields, info)
        return fields + getattr(self.Meta, "extra_fields", [])
