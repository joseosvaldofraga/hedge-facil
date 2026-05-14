from django.urls import path
from . import views

app_name = "contas"

urlpatterns = [
    path("", views.login_view, name="login"),
    path("registro/", views.register_view, name="registro"),
    path("logout/", views.logout_view, name="logout"),
]
