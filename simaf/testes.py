"""
Testes unitários para AFD e AFN.
Execute: python testes.py
"""

import itertools
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from automato import AFD, AFN, tokenizar, de_dict, para_dict, carregar_json, salvar_json

PASTA = os.path.dirname(os.path.abspath(__file__))


def palavras(alfabeto, max_len=5):
    """Todas as palavras sobre o alfabeto com até max_len símbolos."""
    for n in range(max_len + 1):
        for p in itertools.product(sorted(alfabeto), repeat=n):
            yield "".join(p)


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


class TestTokenizacao(unittest.TestCase):

    def test_simbolos_de_um_caractere(self):
        self.assertEqual(tokenizar("aab", {"a", "b"}), ["a", "a", "b"])

    def test_simbolo_mais_longo_primeiro(self):
        self.assertEqual(tokenizar("10ab0", {"0", "1", "10", "ab"}), ["10", "ab", "0"])

    def test_espacos_separam_simbolos(self):
        self.assertEqual(tokenizar("if x  else", {"if", "x", "else"}), ["if", "x", "else"])

    def test_afd_com_simbolos_de_varios_caracteres(self):
        # Aceita sequências de "ab" e "cd" que terminam em "cd"
        afd = AFD({"q0", "q1"}, {"ab", "cd"}, "q0", {"q1"})
        afd.adicionar_transicao("q0", "ab", "q0")
        afd.adicionar_transicao("q0", "cd", "q1")
        afd.adicionar_transicao("q1", "ab", "q0")
        afd.adicionar_transicao("q1", "cd", "q1")
        self.assertTrue(afd.processar("abcd")[0])
        self.assertTrue(afd.processar("ab cd")[0])
        self.assertFalse(afd.processar("cdab")[0])
        self.assertFalse(afd.processar("abc")[0])


class TestMinimizacao(unittest.TestCase):

    def test_funde_estados_equivalentes(self):
        # Termina em 'b', com q1/q2 equivalentes e q3 inalcançável
        afd = AFD({"q0", "q1", "q2", "q3"}, {"a", "b"}, "q0", {"q1", "q2"})
        for origem, a, b in [("q0", "q0", "q1"), ("q1", "q0", "q2"),
                             ("q2", "q0", "q1"), ("q3", "q0", "q0")]:
            afd.adicionar_transicao(origem, "a", a)
            afd.adicionar_transicao(origem, "b", b)
        minimo = afd.minimizar()
        self.assertEqual(len(minimo.estados), 2)
        self.assertIn("{q1,q2}", minimo.estados)
        for w in palavras({"a", "b"}):
            self.assertEqual(afd.processar(w)[0], minimo.processar(w)[0], w)

    def test_remove_estado_morto(self):
        afd = AFD({"q0", "q1", "morto"}, {"a", "b"}, "q0", {"q1"})
        afd.adicionar_transicao("q0", "a", "q1")
        afd.adicionar_transicao("q0", "b", "morto")
        afd.adicionar_transicao("morto", "a", "morto")
        afd.adicionar_transicao("morto", "b", "morto")
        minimo = afd.minimizar()
        self.assertEqual(minimo.estados, {"q0", "q1"})

    def test_linguagem_vazia(self):
        afd = AFD({"q0", "q1"}, {"a"}, "q0", {"q1"})
        afd.adicionar_transicao("q0", "a", "q0")
        minimo = afd.minimizar()
        self.assertEqual(minimo.estados, {"q0"})
        self.assertEqual(minimo.estados_finais, set())


class TestArquivoJSON(unittest.TestCase):

    def test_ida_e_volta(self):
        afn = AFN({"q0", "q1", "q2"}, {"a", "b"}, "q0", {"q2"})
        afn.adicionar_transicao("q0", "a", "q0", "q1")
        afn.adicionar_transicao("q0", "b", "q0")
        afn.adicionar_transicao("q1", AFN.EPSILON, "q2")
        with tempfile.TemporaryDirectory() as pasta:
            caminho = os.path.join(pasta, "afn.json")
            salvar_json(afn, caminho)
            lido = carregar_json(caminho)
        self.assertIsInstance(lido, AFN)
        self.assertEqual(lido.transicoes, afn.transicoes)
        self.assertEqual(lido.estados_finais, afn.estados_finais)

    def test_deterministico_vira_afd(self):
        dados = {"formato": "simaf", "versao": 1,
                 "estados": [{"nome": "p", "inicial": True}, {"nome": "q", "final": True}],
                 "transicoes": [{"origem": "p", "destino": "q", "simbolos": ["x"]}]}
        self.assertIsInstance(de_dict(dados), AFD)

    def test_rejeita_formato_desconhecido(self):
        with self.assertRaises(ValueError):
            de_dict({"estados": [], "transicoes": []})


def _afd_exemplo():
    afd = AFD({"q0", "q1", "q2"}, {"a", "b"}, "q0", {"q2"})
    for origem, a, b in [("q0", "q1", "q0"), ("q1", "q1", "q2"), ("q2", "q1", "q0")]:
        afd.adicionar_transicao(origem, "a", a)
        afd.adicionar_transicao(origem, "b", b)
    return afd


def _afn_exemplo():
    afn = AFN({"q0", "q1", "q2", "q3"}, {"a", "b"}, "q0", {"q3"})
    afn.adicionar_transicao("q0", "a", "q0", "q1")
    afn.adicionar_transicao("q0", "b", "q0")
    afn.adicionar_transicao("q1", "b", "q2")
    afn.adicionar_transicao("q2", AFN.EPSILON, "q3")
    afn.adicionar_transicao("q3", "a", "q3")
    return afn


def _afd_redundante():
    afd = AFD({"A", "B", "C", "D", "E"}, {"0", "1"}, "A", {"C", "E"})
    for origem, z, u in [("A", "B", "D"), ("B", "B", "C"), ("C", "B", "C"),
                         ("D", "B", "E"), ("E", "B", "E")]:
        afd.adicionar_transicao(origem, "0", z)
        afd.adicionar_transicao(origem, "1", u)
    return afd


@unittest.skipUnless(shutil.which("node"), "Node.js não instalado")
class TestMotorJSIgualAoPython(unittest.TestCase):
    """
    O editor usa motor.js; a biblioteca usa automato.py.
    Estes testes rodam o motor.js no Node e exigem as mesmas respostas.
    """

    SCRIPT = r"""
const Motor = require(process.argv[1]);
const casos = JSON.parse(require('fs').readFileSync(0, 'utf8'));
const aceita = (auto, ws) => ws.map(w => Motor.simular(auto, w).accepted);
console.log(JSON.stringify(casos.map(c => {
  const auto = Motor.deJSON(c.automato);
  const afd = Motor.paraAFD(auto), min = Motor.minimizar(auto);
  return {
    ehAFN: Motor.ehAFN(auto),
    original: aceita(auto, c.palavras),
    afd: { estados: afd.states.map(s => s.label).sort(), aceita: aceita(afd, c.palavras) },
    min: { estados: min.states.map(s => s.label).sort(), aceita: aceita(min, c.palavras) },
  };
})));
"""

    def test_mesmos_resultados(self):
        automatos = [_afd_exemplo(), _afn_exemplo(), _afd_redundante()]
        casos = [{"automato": para_dict(a), "palavras": list(palavras(a.alfabeto))}
                 for a in automatos]
        saida = subprocess.run(
            ["node", "-e", self.SCRIPT, os.path.join(PASTA, "motor.js")],
            input=json.dumps(casos, ensure_ascii=False), capture_output=True,
            text=True, encoding="utf-8", check=True)
        resultados = json.loads(saida.stdout)

        for automato, caso, js in zip(automatos, casos, resultados):
            with self.subTest(automato=type(automato).__name__, estados=sorted(automato.estados)):
                afd = automato.para_afd() if isinstance(automato, AFN) else automato
                minimo = afd.minimizar()
                py_original = [automato.processar(w)[0] for w in caso["palavras"]]

                self.assertEqual(js["ehAFN"], isinstance(automato, AFN))
                self.assertEqual(js["original"], py_original)
                self.assertEqual(js["min"]["estados"], sorted(minimo.estados))
                self.assertEqual(js["min"]["aceita"], py_original)
                self.assertEqual(js["afd"]["aceita"], py_original)
                if isinstance(automato, AFN):
                    self.assertEqual(js["afd"]["estados"], sorted(afd.estados))


if __name__ == "__main__":
    unittest.main(verbosity=2)
