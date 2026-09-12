from django.urls import path

from . import views

urlpatterns = [
    path("auth/csrf/", views.csrf_state, name="csrf"),
    path("auth/register/", views.register, name="register"),
    path("auth/login/", views.login_view, name="login"),
    path("auth/logout/", views.logout_view, name="logout"),
    path("auth/session/", views.session_view, name="session"),
    path("auth/password/", views.change_password, name="password"),
    path("account/", views.delete_account, name="delete-account"),
]
