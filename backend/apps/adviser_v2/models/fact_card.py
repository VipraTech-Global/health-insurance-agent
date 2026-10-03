"""Content addressed, immutable public fact cards; source indexes are reused."""

from django.core.exceptions import ValidationError
from django.db import models


class DemoFactCard(models.Model):
    id = models.CharField(primary_key=True, max_length=64)
    index = models.ForeignKey("DemoPlanIndex", on_delete=models.PROTECT)
    card = models.JSONField()
    audit_path = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("Fact cards are immutable; create a new version.")
        return super().save(*args, **kwargs)
