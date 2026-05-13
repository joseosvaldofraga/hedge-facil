from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from apps.contas.models import Produtor
from apps.safra.models import Safra


class SafraNovaViewTestCase(TestCase):
    def setUp(self):
        self.produtor = Produtor.objects.create_user(
            username="ze_safra", email="ze_safra@test.com", password="senha123"
        )
        self.client.force_login(self.produtor)

    def _dados_validos(self):
        return {
            "cultura": "soja",
            "ano_safra": "2025/26",
            "producao_estimada_sacas": "1000",
            "custo_por_saca": "80.00",
        }

    def test_nova_safra_requer_login(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse("safra:nova")).status_code, 302)

    def test_nova_safra_get_retorna_200(self):
        self.assertEqual(self.client.get(reverse("safra:nova")).status_code, 200)

    def test_nova_safra_post_valido_cria_safra(self):
        self.client.post(reverse("safra:nova"), self._dados_validos())
        self.assertEqual(Safra.objects.count(), 1)

    def test_nova_safra_post_valido_vincula_ao_usuario(self):
        self.client.post(reverse("safra:nova"), self._dados_validos())
        self.assertEqual(Safra.objects.first().produtor, self.produtor)

    def test_nova_safra_post_valido_redireciona_para_painel(self):
        response = self.client.post(reverse("safra:nova"), self._dados_validos())
        self.assertRedirects(response, reverse("posicao:painel"))

    def test_nova_safra_post_invalido_permanece_no_formulario(self):
        response = self.client.post(reverse("safra:nova"), {})
        self.assertEqual(response.status_code, 200)
        self.assertIn("form", response.context)

    def test_nova_safra_post_invalido_nao_cria_safra(self):
        self.client.post(reverse("safra:nova"), {})
        self.assertEqual(Safra.objects.count(), 0)

    def test_nova_safra_post_invalido_form_tem_erros(self):
        response = self.client.post(reverse("safra:nova"), {})
        self.assertTrue(response.context["form"].errors)

    def test_nova_safra_mostra_onboarding_para_primeiro_acesso(self):
        # produtor from setUp has no safras
        response = self.client.get(reverse("safra:nova"))
        self.assertTrue(response.context.get("primeiro_acesso"))

    def test_nova_safra_nao_mostra_onboarding_se_ja_tem_safra(self):
        Safra.objects.create(
            produtor=self.produtor,
            cultura="soja",
            ano_safra="2025/26",
            producao_estimada_sacas=Decimal("1000"),
            custo_por_saca=Decimal("80"),
        )
        response = self.client.get(reverse("safra:nova"))
        self.assertFalse(response.context.get("primeiro_acesso"))
