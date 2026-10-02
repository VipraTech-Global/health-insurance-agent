from django.urls import path

from . import views

urlpatterns = [
    path("catalogue/", views.Catalogue.as_view()),
    path("coverage/", views.Coverage.as_view()),
    path("fit/", views.Fit.as_view()),
    path("questions/", views.Questions.as_view()),
    path("questions/<uuid:pk>/", views.QuestionDetail.as_view()),
    path("questions/<uuid:pk>/events/", views.Events.as_view()),
    path("questions/<uuid:pk>/cancel/", views.Cancel.as_view()),
    path("prices/<str:index_id>/", views.Price.as_view()),
    path("citations/<uuid:answer_id>/<int:position>/", views.CitationDetail.as_view()),
    path("documents/<str:index_id>/<str:sha>/", views.Document.as_view()),
]
