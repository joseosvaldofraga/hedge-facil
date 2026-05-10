from django.test import TestCase
from apps.contas.models import Produtor


class ProdutorModelTestCase(TestCase):
    def test_produtor_tem_campo_whatsapp(self):
        p = Produtor.objects.create_user(username="ze", email="ze@test.com")
        self.assertEqual(p.whatsapp, "")

    def test_produtor_tem_campo_cidade(self):
        p = Produtor.objects.create_user(username="ze2", email="ze2@test.com")
        self.assertEqual(p.cidade, "")

    def test_produtor_tem_campo_estado(self):
        p = Produtor.objects.create_user(username="ze3", email="ze3@test.com")
        self.assertEqual(p.estado, "")

    def test_aceitou_termos_nulo_por_padrao(self):
        p = Produtor.objects.create_user(username="ze4", email="ze4@test.com")
        self.assertIsNone(p.aceitou_termos_em)

    def test_produtor_str_retorna_username(self):
        p = Produtor(username="fazendeiro")
        self.assertEqual(str(p), "fazendeiro")
