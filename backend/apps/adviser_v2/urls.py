from django.urls import path

from . import views

urlpatterns = [
    path("conversations/", views.ConversationList.as_view(), name="v2-conversation-list"),
    path(
        "conversations/<uuid:pk>/",
        views.ConversationDetail.as_view(),
        name="v2-conversation-detail",
    ),
    path(
        "conversations/<uuid:pk>/messages/",
        views.ConversationMessages.as_view(),
        name="v2-conversation-messages",
    ),
    path(
        "conversations/<uuid:pk>/profile/",
        views.ConversationProfile.as_view(),
        name="v2-conversation-profile",
    ),
    path("turns/<uuid:pk>/", views.TurnDetail.as_view(), name="v2-turn-detail"),
    path("turns/<uuid:pk>/events/", views.TurnEvents.as_view(), name="v2-turn-events"),
    path("turns/<uuid:pk>/cancel/", views.TurnCancel.as_view(), name="v2-turn-cancel"),
    path("turns/<uuid:pk>/retry/", views.TurnRetry.as_view(), name="v2-turn-retry"),
    path(
        "recommendations/<uuid:pk>/",
        views.RecommendationDetail.as_view(),
        name="v2-recommendation-detail",
    ),
    path("evidence/<uuid:pk>/", views.EvidenceDetail.as_view(), name="v2-evidence-detail"),
    path("documents/<uuid:pk>/file/", views.DocumentFile.as_view(), name="v2-document-file"),
    path(
        "conversations/<uuid:conversation_id>/uploads/",
        views.CustomerUploadList.as_view(),
        name="v2-customer-upload",
    ),
    path(
        "uploads/<uuid:pk>/file/",
        views.CustomerUploadFile.as_view(),
        name="v2-customer-upload-file",
    ),
    path("catalogue/", views.CatalogueReadiness.as_view(), name="v2-catalogue"),
    path("knowledge/readiness/", views.KnowledgeReadiness.as_view(), name="v2-readiness"),
]
