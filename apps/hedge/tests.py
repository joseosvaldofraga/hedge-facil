from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from apps.contas.models import Produtor
from apps.safra.models import Safra


class HedgeViewsTestCase(TestCase):
    def setUp(self):
        self.produtor = Produtor.objects.create_user(
            username="ze", email="ze@test.com", password="senha123"
        )
        self.safra = Safra.objects.create(
            produtor=self.produtor,
            cultura="soja",
            ano_safra="2025/26",
            producao_estimada_sacas=Decimal("1000"),
            custo_por_saca=Decimal("80"),
        )
        self.client.force_login(self.produtor)

    def test_cenarios_retorna_200(self):
        response = self.client.get(reverse("hedge:cenarios", args=[self.safra.id]))
        self.assertEqual(response.status_code, 200)

    def test_cenarios_requer_login(self):
        self.client.logout()
        response = self.client.get(reverse("hedge:cenarios", args=[self.safra.id]))
        self.assertEqual(response.status_code, 302)

    def test_cenarios_contexto_tem_3_cenarios(self):
        response = self.client.get(reverse("hedge:cenarios", args=[self.safra.id]))
        self.assertEqual(len(response.context["cenarios"]), 3)

    def test_cenarios_contexto_tem_safra(self):
        response = self.client.get(reverse("hedge:cenarios", args=[self.safra.id]))
        self.assertEqual(response.context["safra"], self.safra)

    def test_cenarios_404_para_safra_de_outro_produtor(self):
        outro = Produtor.objects.create_user(username="outro", email="outro@test.com")
        safra_outro = Safra.objects.create(
            produtor=outro, cultura="milho", ano_safra="2025/26",
            producao_estimada_sacas=Decimal("500"), custo_por_saca=Decimal("60"),
        )
        response = self.client.get(reverse("hedge:cenarios", args=[safra_outro.id]))
        self.assertEqual(response.status_code, 404)

    def test_proteger_retorna_200(self):
        response = self.client.get(reverse("hedge:proteger", args=[self.safra.id]))
        self.assertEqual(response.status_code, 200)

    def test_proteger_requer_login(self):
        self.client.logout()
        response = self.client.get(reverse("hedge:proteger", args=[self.safra.id]))
        self.assertEqual(response.status_code, 302)
