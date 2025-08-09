import unittest
from main import SistemaDoacoes

class TestSistemaDoacoes(unittest.TestCase):
    def setUp(self):
        self.s = SistemaDoacoes()
        # criar doadores e doações iniciais
        self.d1 = self.s.cadastrar_doador("Teste Doador", "contato")
        self.i1 = self.s.registrar_doacao("Arroz", "Alimentos", 5, self.d1.id)
        self.i2 = self.s.registrar_doacao("Feijão", "Alimentos", 3, self.d1.id)
        # criar pedido
        self.p1 = self.s.cadastrar_pedido("Fam A", "Alimentos", 4, prioridade='alta')

    def test_cadastro_doador(self):
        doadores = self.s.listar_doadores()
        self.assertTrue(any(d['nome'] == "Teste Doador" for d in doadores))

    def test_estoque_pos_doacoes(self):
        estoque = self.s.ver_estoque()
        self.assertIn("Alimentos", estoque)
        total_qtd = sum(it['qtd'] for it in estoque['Alimentos'])
        self.assertEqual(total_qtd, 8)

    def test_pedido_atendido_automatico(self):
        # após setUp, cadastro do pedido deve ter desencadeado alocação
        pedido = self.s.pedidos[self.p1.id]
        # pedido de 4 deve ter sido atendido parcialmente/totalmente (depende da ordem)
        self.assertTrue(pedido.atendido or pedido.quantidade < 4)

    def test_desfazer_alocacao(self):
        qtd_historico_before = len(self.s.historico_alocacoes)
        # se nenhuma alocacao, tenta registrar doacao para forçar alocacao
        if qtd_historico_before == 0:
            self.s.registrar_doacao("Farinha", "Alimentos", 2)
        self.assertTrue(len(self.s.historico_alocacoes) > 0)
        result = self.s.desfazer_ultima_alocacao()
        self.assertTrue(result)

if __name__ == '__main__':
    unittest.main()
