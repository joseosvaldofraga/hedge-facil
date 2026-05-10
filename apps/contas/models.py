from django.contrib.auth.models import AbstractUser
from django.db import models


class Produtor(AbstractUser):
    whatsapp = models.CharField(max_length=20, blank=True)
    cidade = models.CharField(max_length=100, blank=True)
    estado = models.CharField(max_length=2, blank=True)
    aceitou_termos_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Produtor"
        verbose_name_plural = "Produtores"
