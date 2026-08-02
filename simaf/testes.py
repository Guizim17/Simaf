"""
Testes unitários para AFD e AFN.
Execute: python testes.py
"""

import unittest
from automato import AFD, AFN


class TestAFD(unittest.TestCase):

    def setUp(self):
        # AFD que aceita strings sobre {a,b} que terminam em 'ab'
        self.afd = AFD(
            estados={"q0", "q1", "q2"},
            alfabeto={"a", "b"},
            estado_inicial="q0",
            estados_finais={"q2"},
        )
        self.afd.adicionar_transicao("q0", "a", "q1")
        self.afd.adicionar_transicao("q0", "b", "q0")
        self.afd.adicionar_transicao("q1", "a", "q1")
        self.afd.adicionar_transicao("q1", "b", "q2")
        self.afd.adicionar_transicao("q2", "a", "q1")
        self.afd.adicionar_transicao("q2", "b", "q0")

    def test_aceita_string_valida(self):
        aceito, _ = self.afd.processar("aab")
        self.assertTrue(aceito)

    def test_aceita_string_simples(self):
        aceito, _ = self.afd.processar("ab")
        self.assertTrue(aceito)

    def test_rejeita_string_invalida(self):
        aceito, _ = self.afd.processar("ba")
        self.assertFalse(aceito)

    def test_rejeita_string_vazia(self):
        aceito, _ = self.afd.processar("")
        self.assertFalse(aceito)

    def test_caminho_correto(self):
        _, caminho = self.afd.processar("ab")
        self.assertEqual(caminho, ["q0", "q1", "q2"])

    def test_simbolo_fora_do_alfabeto(self):
        aceito, _ = self.afd.processar("axb")
        self.assertFalse(aceito)

    def test_validacao_sem_erros(self):
        self.assertEqual(self.afd.validar(), [])


class TestAFN(unittest.TestCase):

    def setUp(self):
        # AFN que aceita strings que contêm 'ab' como substring
        self.afn = AFN(
            estados={"q0", "q1", "q2"},
            alfabeto={"a", "b"},
            estado_inicial="q0",
            estados_finais={"q2"},
        )
        self.afn.adicionar_transicao("q0", "a", "q0", "q1")
        self.afn.adicionar_transicao("q0", "b", "q0")
        self.afn.adicionar_transicao("q1", "b", "q2")
        self.afn.adicionar_transicao("q2", "a", "q2")
        self.afn.adicionar_transicao("q2", "b", "q2")

    def test_aceita_com_ab(self):
        aceito, _ = self.afn.processar("bab")
        self.assertTrue(aceito)

    def test_aceita_ab_direto(self):
        aceito, _ = self.afn.processar("ab")
        self.assertTrue(aceito)

    def test_rejeita_sem_ab(self):
        aceito, _ = self.afn.processar("bbb")
        self.assertFalse(aceito)

    def test_rejeita_string_vazia(self):
        aceito, _ = self.afn.processar("")
        self.assertFalse(aceito)


class TestAFNEpsilon(unittest.TestCase):

    def setUp(self):
        # AFN com ε-transição: aceita 'a' ou 'ab'
        self.afn = AFN(
            estados={"q0", "q1", "q2"},
            alfabeto={"a", "b"},
            estado_inicial="q0",
            estados_finais={"q1", "q2"},
        )
        self.afn.adicionar_transicao("q0", "a", "q1")
        self.afn.adicionar_transicao("q1", AFN.EPSILON, "q2")
        # q2 com 'b' não vai a lugar nenhum — usado só para testar ε-fecho

    def test_epsilon_fecho(self):
        fecho = self.afn.epsilon_fecho({"q1"})
        self.assertIn("q2", fecho)

    def test_aceita_via_epsilon(self):
        aceito, _ = self.afn.processar("a")
        self.assertTrue(aceito)


class TestConversaoAFNparaAFD(unittest.TestCase):

    def setUp(self):
        # Mesmo AFN que aceita strings contendo 'ab'
        self.afn = AFN(
            estados={"q0", "q1", "q2"},
            alfabeto={"a", "b"},
            estado_inicial="q0",
            estados_finais={"q2"},
        )
        self.afn.adicionar_transicao("q0", "a", "q0", "q1")
        self.afn.adicionar_transicao("q0", "b", "q0")
        self.afn.adicionar_transicao("q1", "b", "q2")
        self.afn.adicionar_transicao("q2", "a", "q2")
        self.afn.adicionar_transicao("q2", "b", "q2")
        self.afd = self.afn.para_afd()

    def test_afd_aceita_mesmas_strings(self):
        for entrada in ["ab", "bab", "aab", "abab"]:
            aceito_afn, _ = self.afn.processar(entrada)
            aceito_afd, _ = self.afd.processar(entrada)
            self.assertEqual(aceito_afn, aceito_afd, f"Divergência em '{entrada}'")

    def test_afd_rejeita_mesmas_strings(self):
        for entrada in ["b", "bbb", "ba"]:
            aceito_afn, _ = self.afn.processar(entrada)
            aceito_afd, _ = self.afd.processar(entrada)
            self.assertEqual(aceito_afn, aceito_afd, f"Divergência em '{entrada}'")


if __name__ == "__main__":
    unittest.main(verbosity=2)
