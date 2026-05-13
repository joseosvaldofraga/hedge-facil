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

    def test_htmx_post_valido_retorna_fragmento(self):
        data = {
            "tipo": "balcao",
            "contraparte": "Cargill",
            "sacas": "300",
            "preco_por_saca": "120.50",
            "data_negociacao": "2025-03-01",
        }
        response = self.client.post(
            reverse("vendas:nova", args=[self.safra.id]),
            data,
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "vendas/_lista.html")

    def test_htmx_post_valido_nao_redireciona(self):
        data = {
            "tipo": "balcao",
            "contraparte": "Cargill",
            "sacas": "300",
            "preco_por_saca": "120.50",
            "data_negociacao": "2025-03-01",
        }
        response = self.client.post(
            reverse("vendas:nova", args=[self.safra.id]),
            data,
            HTTP_HX_REQUEST="true",
        )
        self.assertNotEqual(response.status_code, 302)

    def test_post_normal_redireciona_nao_retorna_fragmento(self):
        data = {
            "tipo": "balcao",
            "contraparte": "Cargill",
            "sacas": "300",
            "preco_por_saca": "120.50",
            "data_negociacao": "2025-03-01",
        }
        response = self.client.post(reverse("vendas:nova", args=[self.safra.id]), data)
        self.assertEqual(response.status_code, 302)


class VendaEditarTestCase(TestCase):
    def setUp(self):
        self.produtor = Produtor.objects.create_user(
            username="edit_user", email="edit@test.com", password="senha123"
        )
        self.safra = Safra.objects.create(
            produtor=self.produtor,
            cultura="soja",
            ano_safra="2025/26",
            producao_estimada_sacas=Decimal("1000"),
            custo_por_saca=Decimal("80"),
        )
        self.venda = Venda.objects.create(
            safra=self.safra,
            tipo="balcao",
            contraparte="Cargill",
            sacas=Decimal("300"),
            preco_por_saca=Decimal("120"),
            data_negociacao="2025-03-01",
        )
        self.client.force_login(self.produtor)

    def test_editar_requer_login(self):
        self.client.logout()
        url = reverse("vendas:editar", args=[self.venda.id])
        self.assertEqual(self.client.get(url).status_code, 302)

    def test_editar_get_retorna_200(self):
        url = reverse("vendas:editar", args=[self.venda.id])
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_editar_get_404_para_venda_de_outro_produtor(self):
        outro = Produtor.objects.create_user(
            username="outro_edit", email="outro_edit@test.com", password="senha123"
        )
        self.client.force_login(outro)
        url = reverse("vendas:editar", args=[self.venda.id])
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_editar_post_valido_atualiza_venda(self):
        url = reverse("vendas:editar", args=[self.venda.id])
        self.client.post(url, {
            "tipo": "balcao",
            "contraparte": "Bunge",
            "sacas": "300",
            "preco_por_saca": "130.00",
            "data_negociacao": "2025-03-01",
        })
        self.venda.refresh_from_db()
        self.assertEqual(self.venda.contraparte, "Bunge")
        self.assertEqual(self.venda.preco_por_saca, Decimal("130.00"))

    def test_editar_post_valido_redireciona_para_lista(self):
        url = reverse("vendas:editar", args=[self.venda.id])
        response = self.client.post(url, {
            "tipo": "balcao",
            "contraparte": "Bunge",
            "sacas": "300",
            "preco_por_saca": "130.00",
            "data_negociacao": "2025-03-01",
        })
        self.assertRedirects(
            response,
            reverse("vendas:lista", args=[self.safra.id]),
            fetch_redirect_response=False,
        )

    def test_editar_post_invalido_retorna_200_com_erros(self):
        url = reverse("vendas:editar", args=[self.venda.id])
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors)
