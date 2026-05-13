from django.urls import path
from . import views

app_name = "contas"

urlpatterns = [
    path("", views.solicitar_login, name="login"),
    path("email-enviado/", views.email_enviado, name="email_enviado"),
    path("logout/", views.logout_view, name="logout"),
]
