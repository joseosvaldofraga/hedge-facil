from django.shortcuts import render, redirect
from django.core.mail import send_mail
from sesame.utils import get_query_string
from .models import Produtor


def solicitar_login(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        if email:
            produtor, _ = Produtor.objects.get_or_create(
                email=email,
                defaults={"username": email},
            )
            link = request.build_absolute_uri("/painel/") + get_query_string(produtor)
            send_mail(
                "Acesso HedgeFácil",
                f"Acesse: {link}",
                "no-reply@hedgefacil.com.br",
                [email],
            )
        return redirect("contas:email_enviado")
    return render(request, "contas/login.html")


def email_enviado(request):
    return render(request, "contas/email_enviado.html")
