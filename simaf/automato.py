"""
Módulo base para autômatos finitos.
Define as classes AFD e AFN com simulação, validação e conversão.
"""

from dataclasses import dataclass, field
from typing import Optional


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

        for simbolo in entrada:
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

        for simbolo in entrada:
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
        def nome_estado(conj: frozenset[str]) -> str:
            return "{" + ",".join(sorted(conj)) + "}"

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
