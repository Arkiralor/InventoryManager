from django.db import models
from django_cryptography.fields import EncryptedMixin
import json

class EncryptedJSONField(EncryptedMixin, models.TextField):
    base_class = models.TextField

    def get_prep_value(self, value):
        if value is None or value == "":
            return None
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except (json.JSONDecodeError, TypeError) as e:
                raise ValueError(
                    f"EncryptedJSONField value must be a valid JSON string or dict: {e}"
                )

        if not isinstance(value, dict):
            raise ValueError("EncryptedJSONField value must be a JSON string or dict")
        return json.dumps(value)

    def get_db_prep_value(self, value, connection=None, prepared=False):
        value = self.get_prep_value(value)
        return super(EncryptedJSONField, self).get_db_prep_value(
            value, connection, prepared
        )

    def from_db_value(self, value, *args, **kwargs):
        value = super(EncryptedJSONField, self).from_db_value(value, *args, **kwargs)

        if value is None:
            return value
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return {}