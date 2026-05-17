from django.urls import path
from . import views

app_name = "contas"

urlpatterns = [
    path("", views.landing_view, name="landing"),
    path("entrar/", views.login_view, name="login"),
    path("registro/", views.register_view, name="registro"),
    path("logout/", views.logout_view, name="logout"),
]
