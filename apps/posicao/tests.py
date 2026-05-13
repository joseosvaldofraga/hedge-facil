from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from apps.contas.models import Produtor
from apps.safra.models import Safra
from apps.posicao.services import get_cotacao_atual


class PainelViewTestCase(TestCase):
    def setUp(self):
        self.produtor = Produtor.objects.create_user(
            username="ze", email="ze@test.com", password="senha123"
        )
        self.client.force_login(self.produtor)

    def test_painel_requer_login(self):
        self.client.logout()
        response = self.client.get(reverse("posicao:painel"))
        self.assertEqual(response.status_code, 302)

    def test_painel_sem_safra_redireciona_para_nova_safra(self):
        response = self.client.get(reverse("posicao:painel"))
        self.assertRedirects(response, reverse("safra:nova"))

    def test_painel_com_safra_retorna_200(self):
        Safra.objects.create(
            produtor=self.produtor,
            cultura="soja",
            ano_safra="2025/26",
            producao_estimada_sacas=Decimal("1000"),
            custo_por_saca=Decimal("80"),
        )
        response = self.client.get(reverse("posicao:painel"))
        self.assertEqual(response.status_code, 200)

    def test_painel_contexto_tem_posicao(self):
        Safra.objects.create(
            produtor=self.produtor,
            cultura="soja",
            ano_safra="2025/26",
            producao_estimada_sacas=Decimal("1000"),
            custo_por_saca=Decimal("80"),
        )
        response = self.client.get(reverse("posicao:painel"))
        self.assertIn("posicao", response.context)

    def test_painel_contexto_tem_safra(self):
        safra = Safra.objects.create(
            produtor=self.produtor,
            cultura="soja",
            ano_safra="2025/26",
            producao_estimada_sacas=Decimal("1000"),
            custo_por_saca=Decimal("80"),
        )
        response = self.client.get(reverse("posicao:painel"))
        self.assertEqual(response.context["safra"], safra)

    def test_painel_nao_mostra_safra_de_outro_produtor(self):
        outro = Produtor.objects.create_user(username="outro", email="outro@test.com")
        Safra.objects.create(
            produtor=outro,
            cultura="milho",
            ano_safra="2025/26",
            producao_estimada_sacas=Decimal("500"),
            custo_por_saca=Decimal("60"),
        )
        response = self.client.get(reverse("posicao:painel"))
        self.assertRedirects(response, reverse("safra:nova"))


class CotacaoAtualTestCase(TestCase):
    def setUp(self):
        self.produtor = Produtor.objects.create_user(
            username="cot_test", email="cot_test@test.com", password="senha123"
        )
        self.safra = Safra.objects.create(
            produtor=self.produtor,
            cultura="soja",
            ano_safra="2025/26",
            producao_estimada_sacas=Decimal("1000"),
            custo_por_saca=Decimal("80"),
        )
        self.client.force_login(self.produtor)

    def test_get_cotacao_atual_retorna_decimal(self):
        self.assertIsInstance(get_cotacao_atual(), Decimal)

    def test_get_cotacao_atual_retorna_valor_positivo(self):
        self.assertGreater(get_cotacao_atual(), Decimal("0"))

    def test_painel_contexto_tem_cotacao(self):
        response = self.client.get(reverse("posicao:painel"))
        self.assertIn("cotacao", response.context)

    def test_painel_cotacao_e_decimal(self):
        response = self.client.get(reverse("posicao:painel"))
        self.assertIsInstance(response.context["cotacao"], Decimal)


class PosicaoPdfTestCase(TestCase):
    def setUp(self):
        self.produtor = Produtor.objects.create_user(
            username="pdf_user", email="pdf_user@test.com", password="senha123"
        )
        self.safra = Safra.objects.create(
            produtor=self.produtor,
            cultura="soja",
            ano_safra="2025/26",
            producao_estimada_sacas=Decimal("1000"),
            custo_por_saca=Decimal("80"),
        )
        self.client.force_login(self.produtor)

    def test_pdf_retorna_200(self):
        self.assertEqual(self.client.get(reverse("posicao:pdf")).status_code, 200)

    def test_pdf_content_type_application_pdf(self):
        self.assertEqual(
            self.client.get(reverse("posicao:pdf"))["Content-Type"],
            "application/pdf",
        )

    def test_pdf_requer_login(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse("posicao:pdf")).status_code, 302)

    def test_pdf_sem_safra_redireciona_para_nova_safra(self):
        self.safra.delete()
        response = self.client.get(reverse("posicao:pdf"))
        self.assertRedirects(response, reverse("safra:nova"), fetch_redirect_response=False)
