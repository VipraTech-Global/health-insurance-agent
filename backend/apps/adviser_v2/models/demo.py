"""Local retrieval-demo releases and encrypted, cancellable customer work."""

import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q
from pgvector.django import VectorField


class DemoPlanIndex(models.Model):
    """Content-addressed public source bundle; never rewrite a published version."""

    id = models.CharField(primary_key=True, max_length=64)
    plan_key = models.CharField(max_length=160)
    insurer = models.CharField(max_length=160)
    name = models.CharField(max_length=250)
    variant = models.CharField(max_length=120, default="Default")
    plan_type = models.CharField(max_length=32, default="unresolved")
    uin = models.CharField(max_length=100, blank=True)
    edition = models.CharField(max_length=200, blank=True)
    bundle_path = models.TextField()
    card = models.JSONField(default=dict)
    coverage = models.JSONField(default=dict)
    models_used = models.JSONField(default=list)
    revoked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["plan_key", "id"], name="demo_plan_version_uq")
        ]


class DemoSectionVector(models.Model):
    """No HNSW: exact cosine only inside one immutable plan index."""

    index = models.ForeignKey(DemoPlanIndex, on_delete=models.CASCADE)
    section_id = models.CharField(max_length=64)
    embedding = VectorField(dimensions=1024)
    text_sha256 = models.CharField(max_length=64)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["index", "section_id"], name="demo_section_vector_uq")
        ]


class DemoRelease(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    label = models.CharField(max_length=32, default="retrieval_demo")
    method = models.CharField(max_length=1, choices=[("H", "H"), ("P", "P")])
    manifest_sha256 = models.CharField(max_length=64)
    bakeoff = models.JSONField()
    indexes = models.ManyToManyField(DemoPlanIndex)
    fact_cards = models.ManyToManyField("DemoFactCard", blank=True)
    active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["active"], condition=Q(active=True), name="demo_one_active_release"
            )
        ]


class DemoSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    profile_revision = models.PositiveIntegerField(default=1)
    profile_ciphertext = models.BinaryField()
    created_at = models.DateTimeField(auto_now_add=True)


class DemoQuestion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(DemoSession, on_delete=models.CASCADE)
    release = models.ForeignKey(DemoRelease, on_delete=models.PROTECT)
    profile_revision = models.PositiveIntegerField()
    erasure_generation = models.PositiveIntegerField()
    input_ciphertext = models.BinaryField()
    state = models.CharField(max_length=24, default="queued")
    cancelled_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    execution_token = models.UUIDField(null=True, editable=False)
    heartbeat_at = models.DateTimeField(null=True, editable=False)
    # Answers never read the profile; a chat question stays readable after it changes.
    profile_bound = models.BooleanField(default=True)


class DemoPlanAnswer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.ForeignKey(DemoQuestion, on_delete=models.CASCADE, related_name="answers")
    index = models.ForeignKey(DemoPlanIndex, on_delete=models.PROTECT)
    state = models.CharField(max_length=24, default="queued")
    result_ciphertext = models.BinaryField(null=True)
    model = models.CharField(max_length=80, blank=True)
    total_ms = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["question", "index"], name="demo_plan_answer_uq")
        ]


class DemoTopicAnswer(models.Model):
    """The engine's validated answer to one canonical topic question for one plan index.

    Holds policy wording and the canonical question only, never customer text, so
    every conversation can reuse it instead of searching the documents again."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    index = models.ForeignKey(DemoPlanIndex, on_delete=models.PROTECT)
    topic = models.CharField(max_length=40)
    method = models.CharField(max_length=1)
    status = models.CharField(max_length=24)
    validator = models.CharField(max_length=80)
    draft = models.CharField(max_length=80)
    result_ciphertext = models.BinaryField()
    model = models.CharField(max_length=80, blank=True)
    total_ms = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["index", "topic", "method"], name="demo_topic_answer_uq"
            )
        ]
