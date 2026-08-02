"""
Visualização de autômatos usando networkx e matplotlib.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import networkx as nx


def _construir_grafo(estados, estado_inicial, estados_finais, transicoes_iter):
    """
    Monta um DiGraph a partir dos dados do autômato.
    transicoes_iter: iterável de (origem, simbolo, destino)
    """
    G = nx.MultiDiGraph()
    G.add_nodes_from(estados)

    arestas: dict[tuple[str, str], list[str]] = {}
    for origem, simbolo, destino in transicoes_iter:
        chave = (origem, destino)
        arestas.setdefault(chave, []).append(simbolo)

    for (origem, destino), simbolos in arestas.items():
        label = ", ".join(sorted(simbolos))
        G.add_edge(origem, destino, label=label)

    return G, arestas


def visualizar_afd(afd, titulo="AFD", caminho: list[str] | None = None):
    """Renderiza o AFD. Se caminho for fornecido, destaca os estados percorridos."""
    transicoes = [
        (origem, simbolo, destino)
        for (origem, simbolo), destino in afd.transicoes.items()
    ]
    _renderizar(
        estados=afd.estados,
        estado_inicial=afd.estado_inicial,
        estados_finais=afd.estados_finais,
        transicoes=transicoes,
        titulo=titulo,
        caminho=caminho,
    )


def visualizar_afn(afn, titulo="AFN", caminho: list[frozenset] | None = None):
    """Renderiza o AFN."""
    transicoes = [
        (origem, simbolo, destino)
        for (origem, simbolo), destinos in afn.transicoes.items()
        for destino in destinos
    ]
    # Converte caminho de frozensets para strings para destaque
    caminho_str = None
    if caminho:
        caminho_str = [list(c) for c in caminho]

    _renderizar(
        estados=afn.estados,
        estado_inicial=afn.estado_inicial,
        estados_finais=afn.estados_finais,
        transicoes=transicoes,
        titulo=titulo,
        caminho_afn=caminho_str,
    )


def _renderizar(
    estados,
    estado_inicial,
    estados_finais,
    transicoes,
    titulo="Autômato",
    caminho: list[str] | None = None,
    caminho_afn=None,
):
    G = nx.MultiDiGraph()
    G.add_nodes_from(estados)

    rotulos_arestas: dict[tuple[str, str], str] = {}
    for origem, simbolo, destino in transicoes:
        chave = (origem, destino)
        existente = rotulos_arestas.get(chave, "")
        rotulos_arestas[chave] = f"{existente}, {simbolo}" if existente else simbolo
        if not G.has_edge(origem, destino):
            G.add_edge(origem, destino)

    pos = nx.spring_layout(G, seed=42, k=2.5)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_title(titulo, fontsize=14, fontweight="bold")
    ax.axis("off")

    # Cores dos nós
    cores = []
    for estado in G.nodes():
        if caminho and estado in caminho:
            cores.append("#90EE90")       # verde claro — no caminho
        elif estado in estados_finais:
            cores.append("#FFD700")       # dourado — final
        elif estado == estado_inicial:
            cores.append("#87CEEB")       # azul claro — inicial
        else:
            cores.append("#FFFFFF")       # branco — comum

    nx.draw_networkx_nodes(G, pos, node_color=cores, node_size=1200,
                           edgecolors="black", linewidths=2, ax=ax)
    nx.draw_networkx_labels(G, pos, font_size=10, font_weight="bold", ax=ax)

    # Duplo círculo para estados finais
    final_pos = {e: pos[e] for e in estados_finais if e in pos}
    nx.draw_networkx_nodes(G, final_pos, node_color="none", node_size=1500,
                           edgecolors="black", linewidths=1.5, ax=ax)

    # Arestas
    nx.draw_networkx_edges(G, pos, ax=ax, arrows=True,
                           arrowsize=20, arrowstyle="-|>",
                           connectionstyle="arc3,rad=0.1",
                           edge_color="gray", width=1.5)

    # Rótulos das arestas
    edge_label_pos = {
        (u, v): (
            (pos[u][0] + pos[v][0]) / 2 + 0.05,
            (pos[u][1] + pos[v][1]) / 2 + 0.05,
        )
        for u, v in G.edges()
    }
    for (u, v), label in rotulos_arestas.items():
        if (u, v) in edge_label_pos:
            x, y = edge_label_pos[(u, v)]
            ax.text(x, y, label, fontsize=9, ha="center",
                    bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.8))

    # Seta indicando estado inicial
    if estado_inicial in pos:
        xi, yi = pos[estado_inicial]
        ax.annotate("", xy=(xi - 0.18, yi),
                    xytext=(xi - 0.45, yi),
                    arrowprops=dict(arrowstyle="-|>", color="black", lw=2))

    # Legenda
    legenda = [
        mpatches.Patch(color="#87CEEB", label="Estado inicial"),
        mpatches.Patch(color="#FFD700", label="Estado final"),
        mpatches.Patch(color="#90EE90", label="Caminho percorrido"),
    ]
    ax.legend(handles=legenda, loc="upper right", fontsize=8)

    plt.tight_layout()
    plt.show()
