from django.urls import path

from . import chat_views, fact_views, views

urlpatterns = [
    path("conversations/", chat_views.Conversations.as_view()),
    path("conversations/<uuid:pk>/", chat_views.ConversationDetail.as_view()),
    path("fact-cards/<str:card_id>/citation/", fact_views.FactCitation.as_view()),
    path("fact-prices/<str:card_id>/citation/", fact_views.FactPriceCitation.as_view()),
    path("health/", views.Health.as_view()),
    path("catalogue/", views.Catalogue.as_view()),
    path("coverage/", views.Coverage.as_view()),
    path("fit/", views.Fit.as_view()),
    path("questions/", views.Questions.as_view()),
    path("questions/<uuid:pk>/", views.QuestionDetail.as_view()),
    path("questions/<uuid:pk>/events/", views.Events.as_view()),
    path("questions/<uuid:pk>/cancel/", views.Cancel.as_view()),
    path("prices/<str:index_id>/", views.Price.as_view()),
    path("prices/<str:index_id>/citation/", views.PriceCitation.as_view()),
    path("citations/<uuid:answer_id>/<int:position>/", views.CitationDetail.as_view()),
    path("cards/<str:index_id>/citation/", views.CardCitation.as_view()),
    path("documents/<str:index_id>/<str:sha>/", views.Document.as_view()),
]
