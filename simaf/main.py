"""
Demonstração interativa do simulador de autômatos.
Execute: python main.py
"""

from automato import AFD, AFN

try:
    from visualizador import visualizar_afd, visualizar_afn
    VISUALIZACAO = True
except ImportError:
    VISUALIZACAO = False
    print("[Aviso] matplotlib/networkx não instalados. Visualização desativada.")
    print("        Instale com: pip install matplotlib networkx\n")


# ─────────────────────────────────────────────
# Exemplo 1: AFD que aceita strings terminadas em 'ab'
# ─────────────────────────────────────────────
def exemplo_afd():
    print("=" * 50)
    print("EXEMPLO 1 — AFD: strings terminadas em 'ab'")
    print("=" * 50)

    afd = AFD(
        estados={"q0", "q1", "q2"},
        alfabeto={"a", "b"},
        estado_inicial="q0",
        estados_finais={"q2"},
    )
    afd.adicionar_transicao("q0", "a", "q1")
    afd.adicionar_transicao("q0", "b", "q0")
    afd.adicionar_transicao("q1", "a", "q1")
    afd.adicionar_transicao("q1", "b", "q2")
    afd.adicionar_transicao("q2", "a", "q1")
    afd.adicionar_transicao("q2", "b", "q0")

    erros = afd.validar()
    if erros:
        print("Erros encontrados:", erros)
        return

    print("\nTabela de transições:")
    print(afd.tabela_transicoes())

    testes = ["ab", "aab", "bab", "ba", "b", "aabb", ""]
    print("\nTestes:")
    for entrada in testes:
        aceito, caminho = afd.processar(entrada)
        resultado = "ACEITO" if aceito else "REJEITADO"
        exibir = repr(entrada) if entrada else "'ε' (vazia)"
        print(f"  {exibir:<12} → {resultado}  | Caminho: {' → '.join(caminho)}")

    if VISUALIZACAO:
        _, caminho = afd.processar("aab")
        visualizar_afd(afd, titulo="AFD — strings terminadas em 'ab'", caminho=caminho)

    return afd


# ─────────────────────────────────────────────
# Exemplo 2: AFN com ε-transições
# ─────────────────────────────────────────────
def exemplo_afn():
    print("\n" + "=" * 50)
    print("EXEMPLO 2 — AFN: strings que contêm 'ab'")
    print("=" * 50)

    afn = AFN(
        estados={"q0", "q1", "q2"},
        alfabeto={"a", "b"},
        estado_inicial="q0",
        estados_finais={"q2"},
    )
    afn.adicionar_transicao("q0", "a", "q0", "q1")
    afn.adicionar_transicao("q0", "b", "q0")
    afn.adicionar_transicao("q1", "b", "q2")
    afn.adicionar_transicao("q2", "a", "q2")
    afn.adicionar_transicao("q2", "b", "q2")

    erros = afn.validar()
    if erros:
        print("Erros encontrados:", erros)
        return

    testes = ["ab", "bab", "aab", "bbb", "ba", "abab", ""]
    print("\nTestes:")
    for entrada in testes:
        aceito, caminho = afn.processar(entrada)
        resultado = "ACEITO" if aceito else "REJEITADO"
        exibir = repr(entrada) if entrada else "'ε' (vazia)"
        conjuntos = " → ".join("{" + ",".join(sorted(c)) + "}" for c in caminho)
        print(f"  {exibir:<12} → {resultado}  | Conjuntos ativos: {conjuntos}")

    print("\nConvertendo AFN → AFD...")
    afd_equiv = afn.para_afd()
    print(f"  Estados do AFD equivalente: {sorted(afd_equiv.estados)}")
    print(f"  Estado inicial: {afd_equiv.estado_inicial}")
    print(f"  Estados finais: {sorted(afd_equiv.estados_finais)}")

    print("\nTabela de transições do AFD equivalente:")
    print(afd_equiv.tabela_transicoes())

    if VISUALIZACAO:
        visualizar_afn(afn, titulo="AFN — strings que contêm 'ab'")
        visualizar_afd(afd_equiv, titulo="AFD equivalente (via construção de subconjuntos)")

    return afn, afd_equiv


# ─────────────────────────────────────────────
# Modo interativo
# ─────────────────────────────────────────────
def modo_interativo():
    print("\n" + "=" * 50)
    print("MODO INTERATIVO")
    print("=" * 50)
    print("Usando o AFD do Exemplo 1 (strings terminadas em 'ab').")
    print("Digite 'sair' para encerrar.\n")

    afd = AFD(
        estados={"q0", "q1", "q2"},
        alfabeto={"a", "b"},
        estado_inicial="q0",
        estados_finais={"q2"},
    )
    afd.adicionar_transicao("q0", "a", "q1")
    afd.adicionar_transicao("q0", "b", "q0")
    afd.adicionar_transicao("q1", "a", "q1")
    afd.adicionar_transicao("q1", "b", "q2")
    afd.adicionar_transicao("q2", "a", "q1")
    afd.adicionar_transicao("q2", "b", "q0")

    while True:
        entrada = input("Digite uma string (ou 'sair'): ").strip()
        if entrada.lower() == "sair":
            break
        aceito, caminho = afd.processar(entrada)
        resultado = "ACEITO" if aceito else "REJEITADO"
        print(f"  → {resultado}")
        print(f"  Caminho: {' → '.join(caminho)}\n")


if __name__ == "__main__":
    exemplo_afd()
    exemplo_afn()
    modo_interativo()
