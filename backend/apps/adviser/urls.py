from django.urls import path

from . import ai_views, views

urlpatterns = [
    path("ai/models/", ai_views.AIModels.as_view(), name="ai-models"),
    path("ai/preferences/", ai_views.AIPreferences.as_view(), name="ai-preferences"),
    path("admin/ai-relay/", ai_views.AdminRelay.as_view(), name="ai-relay"),
    path("admin/ai-relay/accounts/", ai_views.AdminAccountAction.as_view(), name="ai-relay-accounts"),
    path("admin/ai-relay/qualifications/", ai_views.AdminQualification.as_view(), name="ai-relay-qualifications"),
    path("conversations/", views.ConversationList.as_view(), name="conversations"),
    path(
        "conversations/<uuid:pk>/", views.ConversationDetail.as_view(), name="conversation-detail"
    ),
    path(
        "conversations/<uuid:pk>/messages/",
        views.ConversationMessages.as_view(),
        name="conversation-messages",
    ),
    path(
        "conversations/<uuid:pk>/profile/",
        views.ConversationProfile.as_view(),
        name="conversation-profile",
    ),
    path(
        "conversations/<uuid:pk>/profile/confirm/",
        views.ConfirmProfile.as_view(),
        name="confirm-profile",
    ),
    path("turns/<uuid:pk>/", views.TurnDetail.as_view(), name="turn-detail"),
    path("turns/<uuid:pk>/cancel/", views.CancelTurn.as_view(), name="turn-cancel"),
    path("turns/<uuid:pk>/retry/", views.RetryTurn.as_view(), name="turn-retry"),
    path("answers/<uuid:pk>/", views.AnswerDetail.as_view(), name="answer-detail"),
    path(
        "recommendations/<uuid:pk>/",
        views.RecommendationDetail.as_view(),
        name="recommendation-detail",
    ),
    path("evidence/<uuid:pk>/", views.EvidenceDetail.as_view(), name="evidence-detail"),
    path("documents/<uuid:pk>/", views.DocumentDetail.as_view(), name="document-detail"),
    path("documents/<uuid:pk>/file/", views.DocumentFile.as_view(), name="document-file"),
    path("catalogue/coverage/", views.CoverageView.as_view(), name="catalogue-coverage"),
    path("readiness/", views.ReadinessView.as_view(), name="readiness"),
]
