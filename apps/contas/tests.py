from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from apps.contas.models import Produtor


class LoginViewTestCase(TestCase):
    def setUp(self):
        self.produtor = Produtor.objects.create_user(
            username="fazendeiro", email="f@test.com", password="senha123"
        )

    def test_login_get_200(self):
        response = self.client.get(reverse("contas:login"))
        self.assertEqual(response.status_code, 200)

    def test_login_post_valido_autentica(self):
        self.client.post(reverse("contas:login"), {
            "username": "fazendeiro", "password": "senha123"
        })
        response = self.client.get(reverse("posicao:painel"))
        self.assertEqual(response.wsgi_request.user.username, "fazendeiro")

    def test_login_post_valido_redireciona_para_painel(self):
        response = self.client.post(reverse("contas:login"), {
            "username": "fazendeiro", "password": "senha123"
        })
        self.assertRedirects(response, reverse("posicao:painel"),
                             fetch_redirect_response=False)

    def test_login_post_invalido_retorna_200(self):
        response = self.client.post(reverse("contas:login"), {
            "username": "fazendeiro", "password": "errada"
        })
        self.assertEqual(response.status_code, 200)


class RegisterViewTestCase(TestCase):
    def _dados_validos(self):
        return {
            "username": "novoprodutor",
            "email": "novo@test.com",
            "password1": "senhaSegura99",
            "password2": "senhaSegura99",
        }

    def test_registro_get_200(self):
        response = self.client.get(reverse("contas:registro"))
        self.assertEqual(response.status_code, 200)

    def test_registro_post_valido_cria_produtor(self):
        self.client.post(reverse("contas:registro"), self._dados_validos())
        self.assertTrue(Produtor.objects.filter(username="novoprodutor").exists())

    def test_registro_post_valido_faz_login_automatico(self):
        response = self.client.post(reverse("contas:registro"), self._dados_validos())
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_registro_post_invalido_retorna_200(self):
        response = self.client.post(reverse("contas:registro"), {
            "username": "x", "email": "x@test.com",
            "password1": "abc", "password2": "diferente",
        })
        self.assertEqual(response.status_code, 200)


class LogoutViewTestCase(TestCase):
    def setUp(self):
        self.produtor = Produtor.objects.create_user(
            username="ze_logout", email="ze_logout@test.com", password="senha123"
        )
        self.client.force_login(self.produtor)

    def test_logout_post_desloga_usuario(self):
        response = self.client.post(reverse("contas:logout"))
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_logout_post_redireciona_para_login(self):
        response = self.client.post(reverse("contas:logout"))
        self.assertRedirects(response, reverse("contas:login"))

    def test_logout_get_nao_permitido(self):
        response = self.client.get(reverse("contas:logout"))
        self.assertEqual(response.status_code, 405)
