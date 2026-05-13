from decimal import Decimal

from django.test import TestCase

from apps.contas.models import Produtor
from apps.safra.models import Safra


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


class SafraModelTestCase(TestCase):
    def setUp(self):
        self.produtor = Produtor.objects.create_user(username="fazendeiro", email="f@test.com")

    def test_custo_total_multiplica_producao_por_custo(self):
        safra = Safra(
            producao_estimada_sacas=Decimal("1000"),
            custo_por_saca=Decimal("80"),
        )
        self.assertEqual(safra.custo_total, Decimal("80000"))

    def test_custo_total_usa_decimal(self):
        safra = Safra(
            producao_estimada_sacas=Decimal("1000"),
            custo_por_saca=Decimal("80.50"),
        )
        self.assertIsInstance(safra.custo_total, Decimal)

    def test_str_contem_cultura_e_ano(self):
        safra = Safra(
            cultura="soja",
            ano_safra="2025/26",
            producao_estimada_sacas=Decimal("1000"),
            custo_por_saca=Decimal("80"),
        )
        safra.produtor = self.produtor
        self.assertIn("Soja", str(safra))
        self.assertIn("2025/26", str(safra))

    def test_unique_produtor_cultura_ano(self):
        from django.db import IntegrityError
        Safra.objects.create(
            produtor=self.produtor, cultura="soja", ano_safra="2025/26",
            producao_estimada_sacas=Decimal("1000"), custo_por_saca=Decimal("80"),
        )
        with self.assertRaises(IntegrityError):
            Safra.objects.create(
                produtor=self.produtor, cultura="soja", ano_safra="2025/26",
                producao_estimada_sacas=Decimal("500"), custo_por_saca=Decimal("90"),
            )
