from django.test import TestCase
from django.urls import reverse
from django.core import mail
from apps.contas.models import Produtor


class LoginMagicoTestCase(TestCase):
    def test_get_login_retorna_200(self):
        response = self.client.get(reverse("contas:login"))
        self.assertEqual(response.status_code, 200)

    def test_post_login_cria_produtor_se_nao_existe(self):
        self.client.post(reverse("contas:login"), {"email": "novo@test.com"})
        self.assertTrue(Produtor.objects.filter(email="novo@test.com").exists())

    def test_post_login_nao_duplica_produtor_existente(self):
        Produtor.objects.create_user(username="ze@test.com", email="ze@test.com")
        self.client.post(reverse("contas:login"), {"email": "ze@test.com"})
        self.assertEqual(Produtor.objects.filter(email="ze@test.com").count(), 1)

    def test_post_login_envia_email(self):
        self.client.post(reverse("contas:login"), {"email": "ze@test.com"})
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("ze@test.com", mail.outbox[0].to)

    def test_post_login_redireciona_para_confirmacao(self):
        response = self.client.post(reverse("contas:login"), {"email": "ze@test.com"})
        self.assertRedirects(response, reverse("contas:email_enviado"))

    def test_email_enviado_retorna_200(self):
        response = self.client.get(reverse("contas:email_enviado"))
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
