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


class SafraListaViewTestCase(TestCase):
    def setUp(self):
        self.produtor = Produtor.objects.create_user(
            username="lista_user", email="lista@test.com", password="senha123"
        )
        self.safra1 = Safra.objects.create(
            produtor=self.produtor, cultura="soja", ano_safra="2025/26",
            producao_estimada_sacas=Decimal("1000"), custo_por_saca=Decimal("80"), ativa=True,
        )
        self.safra2 = Safra.objects.create(
            produtor=self.produtor, cultura="milho", ano_safra="2025/26",
            producao_estimada_sacas=Decimal("500"), custo_por_saca=Decimal("60"), ativa=False,
        )
        self.client.force_login(self.produtor)

    def test_lista_requer_login(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse("safra:lista")).status_code, 302)

    def test_lista_retorna_200(self):
        self.assertEqual(self.client.get(reverse("safra:lista")).status_code, 200)

    def test_lista_mostra_safras_do_usuario(self):
        response = self.client.get(reverse("safra:lista"))
        self.assertIn(self.safra1, response.context["safras"])
        self.assertIn(self.safra2, response.context["safras"])

    def test_lista_nao_mostra_safras_de_outros_produtores(self):
        outro = Produtor.objects.create_user(
            username="outro_lista", email="outro_lista@test.com", password="senha123"
        )
        safra_outro = Safra.objects.create(
            produtor=outro, cultura="soja", ano_safra="2025/26",
            producao_estimada_sacas=Decimal("1000"), custo_por_saca=Decimal("80"),
        )
        response = self.client.get(reverse("safra:lista"))
        self.assertNotIn(safra_outro, response.context["safras"])


class SafraAtivarViewTestCase(TestCase):
    def setUp(self):
        self.produtor = Produtor.objects.create_user(
            username="ativar_user", email="ativar@test.com", password="senha123"
        )
        self.safra1 = Safra.objects.create(
            produtor=self.produtor, cultura="soja", ano_safra="2025/26",
            producao_estimada_sacas=Decimal("1000"), custo_por_saca=Decimal("80"), ativa=True,
        )
        self.safra2 = Safra.objects.create(
            produtor=self.produtor, cultura="milho", ano_safra="2025/26",
            producao_estimada_sacas=Decimal("500"), custo_por_saca=Decimal("60"), ativa=False,
        )
        self.client.force_login(self.produtor)

    def test_ativar_requer_login(self):
        self.client.logout()
        url = reverse("safra:ativar", args=[self.safra2.id])
        self.assertEqual(self.client.post(url).status_code, 302)

    def test_ativar_post_muda_safra_ativa(self):
        url = reverse("safra:ativar", args=[self.safra2.id])
        self.client.post(url)
        self.safra1.refresh_from_db()
        self.safra2.refresh_from_db()
        self.assertFalse(self.safra1.ativa)
        self.assertTrue(self.safra2.ativa)

    def test_ativar_redireciona_para_painel(self):
        url = reverse("safra:ativar", args=[self.safra2.id])
        response = self.client.post(url)
        self.assertRedirects(response, reverse("posicao:painel"), fetch_redirect_response=False)

    def test_ativar_rejeita_get(self):
        url = reverse("safra:ativar", args=[self.safra2.id])
        self.assertEqual(self.client.get(url).status_code, 405)

    def test_ativar_impede_acesso_de_outro_produtor(self):
        outro = Produtor.objects.create_user(
            username="outro_ativar", email="outro_ativar@test.com", password="senha123"
        )
        safra_outro = Safra.objects.create(
            produtor=outro, cultura="soja", ano_safra="2025/26",
            producao_estimada_sacas=Decimal("1000"), custo_por_saca=Decimal("80"),
        )
        url = reverse("safra:ativar", args=[safra_outro.id])
        self.assertEqual(self.client.post(url).status_code, 404)
