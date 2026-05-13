from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from apps.contas.models import Produtor
from apps.safra.models import Safra
from apps.vendas.models import Venda


class VendasViewsTestCase(TestCase):
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

    def test_lista_vendas_retorna_200(self):
        response = self.client.get(reverse("vendas:lista", args=[self.safra.id]))
        self.assertEqual(response.status_code, 200)

    def test_lista_vendas_requer_login(self):
        self.client.logout()
        response = self.client.get(reverse("vendas:lista", args=[self.safra.id]))
        self.assertEqual(response.status_code, 302)

    def test_nova_venda_get_retorna_200(self):
        response = self.client.get(reverse("vendas:nova", args=[self.safra.id]))
        self.assertEqual(response.status_code, 200)

    def test_nova_venda_post_valido_cria_venda(self):
        data = {
            "tipo": "balcao",
            "contraparte": "Cargill",
            "sacas": "300",
            "preco_por_saca": "120.50",
            "data_negociacao": "2025-03-01",
        }
        self.client.post(reverse("vendas:nova", args=[self.safra.id]), data)
        self.assertEqual(Venda.objects.count(), 1)

    def test_nova_venda_post_valido_redireciona(self):
        data = {
            "tipo": "balcao",
            "contraparte": "Cargill",
            "sacas": "300",
            "preco_por_saca": "120.50",
            "data_negociacao": "2025-03-01",
        }
        response = self.client.post(reverse("vendas:nova", args=[self.safra.id]), data)
        self.assertRedirects(response, reverse("posicao:painel"))

    def test_nova_venda_post_invalido_nao_cria_venda(self):
        response = self.client.post(reverse("vendas:nova", args=[self.safra.id]), {})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Venda.objects.exists())

    def test_lista_nao_mostra_vendas_de_outros_produtores(self):
        outro = Produtor.objects.create_user(username="outro", email="outro@test.com")
        safra_outro = Safra.objects.create(
            produtor=outro, cultura="milho", ano_safra="2025/26",
            producao_estimada_sacas=Decimal("500"), custo_por_saca=Decimal("60"),
        )
        Venda.objects.create(
            safra=safra_outro, tipo="balcao", contraparte="Bunge",
            sacas=Decimal("100"), preco_por_saca=Decimal("50"),
            data_negociacao="2025-01-01",
        )
        response = self.client.get(reverse("vendas:lista", args=[self.safra.id]))
        self.assertNotContains(response, "Bunge")
