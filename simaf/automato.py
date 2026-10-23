"""
Biblioteca para o uso dos automatos finitos
Define as classes AFD e AFN com simulação, validação e conversão.
"""

import json
from collections import deque
from dataclasses import dataclass, field

EPSILON = "ε"
NOME_MAX = 12  # acima disso, a minimização renomeia os estados para q0, q1, ...


def tokenizar(entrada: str, alfabeto: set[str]) -> list[str]:
    """
    Divide a entrada em símbolos do alfabeto (mesma regra do motor.js do editor).
    - Com espaços: cada palavra separada por espaço é um símbolo ("if x else").
    - Sem espaços: casamento guloso pelo símbolo mais longo do alfabeto;
      caracteres que não casam viram símbolos isolados (e serão rejeitados).
    """
    if any(c.isspace() for c in entrada):
        return entrada.split()
    simbolos = sorted(alfabeto, key=len, reverse=True)
    tokens = []
    i = 0
    while i < len(entrada):
        s = next((s for s in simbolos if entrada.startswith(s, i)), None)
        if s:
            tokens.append(s)
            i += len(s)
        else:
            tokens.append(entrada[i])
            i += 1
    return tokens


def _nome_conjunto(nomes) -> str:
    return "{" + ",".join(sorted(nomes)) + "}"


@dataclass
class AFD:
    """Autômato Finito Determinístico."""

    estados: set[str]
    alfabeto: set[str]
    estado_inicial: str
    estados_finais: set[str]
    # transicoes[(estado, simbolo)] = proximo_estado
    transicoes: dict[tuple[str, str], str] = field(default_factory=dict)

    def validar(self) -> list[str]:
        erros = []
        if self.estado_inicial not in self.estados:
            erros.append(f"Estado inicial '{self.estado_inicial}' não está no conjunto de estados.")
        for ef in self.estados_finais:
            if ef not in self.estados:
                erros.append(f"Estado final '{ef}' não está no conjunto de estados.")
        for (estado, simbolo), destino in self.transicoes.items():
            if estado not in self.estados:
                erros.append(f"Transição com estado inválido: '{estado}'.")
            if simbolo not in self.alfabeto:
                erros.append(f"Transição com símbolo inválido: '{simbolo}'.")
            if destino not in self.estados:
                erros.append(f"Transição com destino inválido: '{destino}'.")
        return erros

    def processar(self, entrada: str) -> tuple[bool, list[str]]:
        """
        Simula o AFD sobre a string de entrada.
        Retorna (aceito, caminho_percorrido).
        """
        estado_atual = self.estado_inicial
        caminho = [estado_atual]

        for simbolo in tokenizar(entrada, self.alfabeto):
            if simbolo not in self.alfabeto:
                return False, caminho
            chave = (estado_atual, simbolo)
            if chave not in self.transicoes:
                return False, caminho
            estado_atual = self.transicoes[chave]
            caminho.append(estado_atual)

        aceito = estado_atual in self.estados_finais
        return aceito, caminho

    def adicionar_transicao(self, origem: str, simbolo: str, destino: str):
        self.transicoes[(origem, simbolo)] = destino

    def tabela_transicoes(self) -> str:
        """Retorna a tabela de transições formatada como texto."""
        simbolos = sorted(self.alfabeto)
        estados_ord = sorted(self.estados)

        header = f"{'Estado':<12}" + "".join(f"{s:<12}" for s in simbolos)
        linhas = [header, "-" * len(header)]

        for estado in estados_ord:
            marcador = ""
            if estado == self.estado_inicial:
                marcador += "->"
            if estado in self.estados_finais:
                marcador += "*"
            label = f"{marcador}{estado}"
            linha = f"{label:<12}"
            for simbolo in simbolos:
                destino = self.transicoes.get((estado, simbolo), "-")
                linha += f"{destino:<12}"
            linhas.append(linha)

        return "\n".join(linhas)

    def minimizar(self) -> "AFD":
        """
        Retorna o AFD mínimo equivalente (refinamento de partições de Moore).
        Remove estados inalcançáveis e mortos; estados equivalentes fundidos
        recebem o nome '{a,b}'. Mesmo algoritmo do motor.js do editor.
        """
        simbolos = sorted(self.alfabeto)

        # Estados alcançáveis a partir do inicial
        alcancaveis = [self.estado_inicial]
        vistos = {self.estado_inicial}
        for estado in alcancaveis:
            for simbolo in simbolos:
                destino = self.transicoes.get((estado, simbolo))
                if destino is not None and destino not in vistos:
                    vistos.add(destino)
                    alcancaveis.append(destino)

        # Função total com um estado sumidouro
        sumidouro = object()

        def prox(estado, simbolo):
            if estado is sumidouro:
                return sumidouro
            return self.transicoes.get((estado, simbolo), sumidouro)

        todos = alcancaveis + [sumidouro]
        eh_final = lambda e: e is not sumidouro and e in self.estados_finais

        classe = {e: ("F" if eh_final(e) else "N") for e in todos}
        qtd = len(set(classe.values()))
        while True:
            assinaturas: dict[tuple, int] = {}
            nova = {}
            for e in todos:
                sig = (classe[e],) + tuple(classe[prox(e, a)] for a in simbolos)
                nova[e] = assinaturas.setdefault(sig, len(assinaturas))
            classe = nova
            if len(assinaturas) == qtd:
                break
            qtd = len(assinaturas)

        classe_morta = classe[sumidouro]
        classe_inicial = classe[self.estado_inicial]

        # Linguagem vazia: sobra só o estado inicial, sem transições.
        if classe_inicial == classe_morta:
            return AFD({self.estado_inicial}, set(self.alfabeto), self.estado_inicial, set())

        membros: dict[int, list[str]] = {}
        for e in alcancaveis:
            if classe[e] != classe_morta:
                membros.setdefault(classe[e], []).append(e)

        # Ordem BFS das classes a partir do inicial (a mesma do motor.js)
        ordem = [classe_inicial]
        for c in ordem:
            for a in simbolos:
                cd = classe[prox(membros[c][0], a)]
                if cd != classe_morta and cd not in ordem:
                    ordem.append(cd)

        nomes_compostos = {
            c: (ms[0] if len(ms) == 1 else _nome_conjunto(ms))
            for c, ms in membros.items()
        }
        # Nomes compostos longos ficam ilegíveis: renomeia tudo para q0, q1, ...
        if any(len(n) > NOME_MAX for n in nomes_compostos.values()):
            nomes_compostos = {c: f"q{i}" for i, c in enumerate(ordem)}

        def nome(c):
            return nomes_compostos[c]

        transicoes = {}
        for c, nomes in membros.items():
            for a in simbolos:
                cd = classe[prox(nomes[0], a)]
                if cd != classe_morta:
                    transicoes[(nome(c), a)] = nome(cd)

        return AFD(
            estados={nome(c) for c in membros},
            alfabeto=set(self.alfabeto),
            estado_inicial=nome(classe_inicial),
            estados_finais={nome(c) for c, nomes in membros.items() if eh_final(nomes[0])},
            transicoes=transicoes,
        )


@dataclass
class AFN:
    """
    Autômato Finito Não-Determinístico com suporte a ε-transições.
    Use 'ε' (ou a constante EPSILON) como símbolo para transições vazias.
    """

    estados: set[str]
    alfabeto: set[str]
    estado_inicial: str
    estados_finais: set[str]
    # transicoes[(estado, simbolo)] = conjunto de próximos estados
    transicoes: dict[tuple[str, str], set[str]] = field(default_factory=dict)

    EPSILON = "ε"

    def validar(self) -> list[str]:
        erros = []
        if self.estado_inicial not in self.estados:
            erros.append(f"Estado inicial '{self.estado_inicial}' não está no conjunto de estados.")
        for ef in self.estados_finais:
            if ef not in self.estados:
                erros.append(f"Estado final '{ef}' não está no conjunto de estados.")
        for (estado, simbolo), destinos in self.transicoes.items():
            if estado not in self.estados:
                erros.append(f"Transição com estado inválido: '{estado}'.")
            if simbolo != self.EPSILON and simbolo not in self.alfabeto:
                erros.append(f"Transição com símbolo inválido: '{simbolo}'.")
            for d in destinos:
                if d not in self.estados:
                    erros.append(f"Transição com destino inválido: '{d}'.")
        return erros

    def adicionar_transicao(self, origem: str, simbolo: str, *destinos: str):
        chave = (origem, simbolo)
        if chave not in self.transicoes:
            self.transicoes[chave] = set()
        self.transicoes[chave].update(destinos)

    def epsilon_fecho(self, estados: set[str]) -> frozenset[str]:
        """Calcula o ε-fecho de um conjunto de estados."""
        fecho = set(estados)
        pilha = list(estados)
        while pilha:
            estado = pilha.pop()
            for destino in self.transicoes.get((estado, self.EPSILON), set()):
                if destino not in fecho:
                    fecho.add(destino)
                    pilha.append(destino)
        return frozenset(fecho)

    def mover(self, estados: frozenset[str], simbolo: str) -> frozenset[str]:
        """Retorna todos os estados alcançáveis a partir de um conjunto via um símbolo."""
        resultado = set()
        for estado in estados:
            resultado.update(self.transicoes.get((estado, simbolo), set()))
        return frozenset(resultado)

    def processar(self, entrada: str) -> tuple[bool, list[frozenset[str]]]:
        """
        Simula o AFN sobre a string de entrada usando BFS (subconjuntos ativos).
        Retorna (aceito, lista_de_conjuntos_ativos).
        """
        estados_atuais = self.epsilon_fecho({self.estado_inicial})
        caminho = [estados_atuais]

        for simbolo in tokenizar(entrada, self.alfabeto):
            if simbolo not in self.alfabeto:
                return False, caminho
            proximos = self.mover(estados_atuais, simbolo)
            estados_atuais = self.epsilon_fecho(proximos)
            caminho.append(estados_atuais)
            if not estados_atuais:
                return False, caminho

        aceito = bool(estados_atuais & self.estados_finais)
        return aceito, caminho

    def para_afd(self) -> AFD:
        """
        Converte o AFN em AFD equivalente pelo algoritmo de construção de subconjuntos.
        Os novos estados do AFD são nomeados como '{q0,q1,...}'.
        """
        nome_estado = _nome_conjunto

        estado_inicial_afd = self.epsilon_fecho({self.estado_inicial})
        fila = [estado_inicial_afd]
        visitados: set[frozenset[str]] = set()
        transicoes_afd: dict[tuple[str, str], str] = {}
        estados_finais_afd: set[str] = set()

        while fila:
            atual = fila.pop(0)
            if atual in visitados:
                continue
            visitados.add(atual)

            nome_atual = nome_estado(atual)
            if atual & self.estados_finais:
                estados_finais_afd.add(nome_atual)

            for simbolo in sorted(self.alfabeto):
                proximos = self.epsilon_fecho(self.mover(atual, simbolo))
                if proximos:
                    transicoes_afd[(nome_atual, simbolo)] = nome_estado(proximos)
                    if proximos not in visitados:
                        fila.append(proximos)

        estados_afd = {nome_estado(s) for s in visitados}

        return AFD(
            estados=estados_afd,
            alfabeto=set(self.alfabeto),
            estado_inicial=nome_estado(estado_inicial_afd),
            estados_finais=estados_finais_afd,
            transicoes=transicoes_afd,
        )


# ─────────────────────────────────────────────
# Arquivos .json do editor (formato compartilhado com motor.js)
# ─────────────────────────────────────────────

def de_dict(dados: dict) -> "AFD | AFN":
    """
    Constrói um AFD ou AFN a partir do formato de arquivo do SIMAF:
    { formato: "simaf", versao: 1,
      estados:    [{nome, x, y, inicial, final}],
      transicoes: [{origem, destino, simbolos: [...], curva}] }
    Retorna AFD quando não há ε nem não-determinismo; caso contrário, AFN.
    """
    if dados.get("formato") != "simaf":
        raise ValueError("Arquivo não está no formato do SIMAF.")

    estados = [e["nome"] for e in dados["estados"]]
    if len(set(estados)) != len(estados):
        raise ValueError("Há estados com nomes duplicados.")
    iniciais = [e["nome"] for e in dados["estados"] if e.get("inicial")]
    if not iniciais:
        raise ValueError("O autômato não tem estado inicial.")
    finais = {e["nome"] for e in dados["estados"] if e.get("final")}

    destinos: dict[tuple[str, str], set[str]] = {}
    for t in dados["transicoes"]:
        for simbolo in t["simbolos"]:
            destinos.setdefault((t["origem"], simbolo), set()).add(t["destino"])
    alfabeto = {s for (_, s) in destinos if s != EPSILON}

    deterministico = all(s != EPSILON and len(d) == 1 for (_, s), d in destinos.items())
    if deterministico:
        transicoes = {k: next(iter(d)) for k, d in destinos.items()}
        return AFD(set(estados), alfabeto, iniciais[0], finais, transicoes)
    return AFN(set(estados), alfabeto, iniciais[0], finais, destinos)


def para_dict(automato: "AFD | AFN") -> dict:
    """Converte um AFD/AFN no formato de arquivo do editor, com layout em colunas (BFS)."""
    def destinos_de(valor):
        return valor if isinstance(valor, set) else {valor}

    # Profundidade BFS para posicionar os estados
    profundidade = {automato.estado_inicial: 0}
    fila = deque([automato.estado_inicial])
    while fila:
        e = fila.popleft()
        for (origem, _), valor in automato.transicoes.items():
            if origem == e:
                for d in destinos_de(valor):
                    if d not in profundidade:
                        profundidade[d] = profundidade[e] + 1
                        fila.append(d)
    colunas: dict[int, list[str]] = {}
    for e in sorted(automato.estados):
        colunas.setdefault(profundidade.get(e, max(profundidade.values()) + 1), []).append(e)

    estados = []
    for d, col in sorted(colunas.items()):
        for i, e in enumerate(col):
            estados.append({
                "nome": e,
                "x": 200 + d * 190,
                "y": round(800 + (i - (len(col) - 1) / 2) * 150),
                "inicial": e == automato.estado_inicial,
                "final": e in automato.estados_finais,
            })

    arestas: dict[tuple[str, str], list[str]] = {}
    for (origem, simbolo), valor in automato.transicoes.items():
        for d in destinos_de(valor):
            arestas.setdefault((origem, d), []).append(simbolo)

    return {
        "formato": "simaf",
        "versao": 1,
        "estados": estados,
        "transicoes": [
            {"origem": o, "destino": d, "simbolos": sorted(s), "curva": 0}
            for (o, d), s in sorted(arestas.items())
        ],
    }


def carregar_json(caminho: str) -> "AFD | AFN":
    """Abre um autômato salvo pelo editor (botão Salvar)."""
    with open(caminho, encoding="utf-8") as f:
        return de_dict(json.load(f))


def salvar_json(automato: "AFD | AFN", caminho: str) -> None:
    """Salva um autômato para ser aberto no editor (botão Abrir)."""
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(para_dict(automato), f, ensure_ascii=False, indent=2)
