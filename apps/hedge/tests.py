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

    def test_cenarios_contexto_tem_6_cenarios(self):
        response = self.client.get(reverse("hedge:cenarios", args=[self.safra.id]))
        self.assertEqual(len(response.context["cenarios"]), 6)

    def test_simular_cenarios_retorna_6_por_padrao(self):
        from apps.hedge.services import simular_cenarios
        cenarios = simular_cenarios(Decimal("130"))
        self.assertEqual(len(cenarios), 6)

    def test_cenarios_incluem_queda_50_e_alta_30(self):
        from apps.hedge.services import simular_cenarios
        cenarios = simular_cenarios(Decimal("130"))
        variacoes = [c.variacao_percentual for c in cenarios]
        self.assertIn(Decimal("-50"), variacoes)
        self.assertIn(Decimal("30"), variacoes)

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

    def test_cenarios_preco_invalido_retorna_200_com_fallback(self):
        url = reverse("hedge:cenarios", args=[self.safra.id]) + "?preco_atual=abc"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_cenarios_preco_vazio_retorna_200_com_fallback(self):
        url = reverse("hedge:cenarios", args=[self.safra.id]) + "?preco_atual="
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)


class HedgeRedirectTestCase(TestCase):
    def setUp(self):
        self.produtor = Produtor.objects.create_user(
            username="redir_test", email="redir_test@test.com", password="senha123"
        )
        self.client.force_login(self.produtor)

    def test_hedge_redirect_com_safra_redireciona_para_cenarios(self):
        safra = Safra.objects.create(
            produtor=self.produtor,
            cultura="soja",
            ano_safra="2025/26",
            producao_estimada_sacas=Decimal("1000"),
            custo_por_saca=Decimal("80"),
        )
        response = self.client.get(reverse("hedge:redirect"))
        self.assertRedirects(
            response,
            reverse("hedge:cenarios", args=[safra.id]),
            fetch_redirect_response=False,
        )

    def test_hedge_redirect_sem_safra_redireciona_para_nova_safra(self):
        response = self.client.get(reverse("hedge:redirect"))
        self.assertRedirects(
            response,
            reverse("safra:nova"),
            fetch_redirect_response=False,
        )

    def test_hedge_redirect_requer_login(self):
        self.client.logout()
        response = self.client.get(reverse("hedge:redirect"))
        self.assertEqual(response.status_code, 302)
        self.assertNotIn("cenarios", response["Location"])
