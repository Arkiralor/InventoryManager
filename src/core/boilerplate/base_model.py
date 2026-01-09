from django.db import models
from uuid import uuid4

from core import logger

class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean_text_attribute(self, attribute: str, lower:bool=False) -> None:
        value = getattr(self, attribute, None)
        if not isinstance(value, str):
            logger.error(f"Attribute {attribute} is not a string.")
            return
        if value and isinstance(value, str):
            cleaned_value = value.lstrip().rstrip()
            if lower:
                cleaned_value = cleaned_value.lower()
            setattr(self, attribute, cleaned_value)

    class Meta:
        abstract = True