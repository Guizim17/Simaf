# SIMAF — Simulador de Autômatos Finitos

Ferramenta didática para desenhar, simular, converter e minimizar autômatos finitos
(AFD e AFN com ε-transições).

## Funcionalidades

- **Editor visual**: crie estados (clique duplo), conecte-os (modo *Conectar*), marque estados
  iniciais/finais, curve setas, zoom e pan.
- **Simulação**: teste uma palavra de uma vez ou **passo a passo**; todas as transições
  percorridas no passo são destacadas, inclusive os vários ramos de um AFN e as ε-transições.
- **Testes em lote**: uma palavra por linha (`ε` = palavra vazia).
- **AFN → AFD**: construção de subconjuntos; os novos estados se chamam `{q0,q1}`.
- **Minimização**: remove estados inalcançáveis, mortos e equivalentes (algoritmo de Moore).
  Se os nomes ficarem longos demais, os estados são renomeados para `q0, q1, …`.
- **Salvar / Abrir** (`Ctrl+S` / `Ctrl+O`): arquivos `.json`, que também podem ser lidos
  pela biblioteca Python.
- **Símbolos com vários caracteres** (ex.: `ab`, `if`, `10`).

### Como a palavra de entrada é dividida em símbolos

- **Com espaços**, cada parte é um símbolo: `if x else` → `if`, `x`, `else`.
- **Sem espaços**, vale sempre o símbolo mais longo do alfabeto que casar:
  com alfabeto `{0, 1, 10}`, `100` → `10`, `0`.
  Use espaços quando quiser outra divisão.

## Estrutura

| Arquivo | Função |
|---|---|
| `app.py` | Abre o editor numa janela (pywebview) e oferece os diálogos de salvar/abrir |
| `editor.html` | Interface: desenho no canvas, painéis e simulação |
| `motor.js` | Núcleo do editor: simulação, tokenização, AFN→AFD, minimização, formato `.json` |
| `automato.py` | Biblioteca Python equivalente (classes `AFD` e `AFN`) |
| `visualizador.py` | Desenha autômatos com matplotlib/networkx (opcional) |
| `main.py` | Demonstração no terminal |
| `testes.py` | Testes unitários, incluindo a comparação `motor.js` × `automato.py` |

`motor.js` e `automato.py` implementam os mesmos algoritmos. O teste
`TestMotorJSIgualAoPython` executa o `motor.js` no Node.js e exige as mesmas respostas
do Python (aceitação de todas as palavras até 5 símbolos, estados do AFD e do AFD mínimo).
Sem Node.js instalado, esse teste é pulado.

## Como usar

Instalar as dependências:

```bash
pip install pywebview pyinstaller
```

Rodar a partir do código (dentro da pasta `simaf`):

```bash
python app.py
```

Rodar os testes:

```bash
python testes.py
```

Gerar o executável (na pasta acima, `C:\Projetos\Simaf`). O resultado fica em `dist\AFSIM.exe`:

```bash
pyinstaller AFSIM.spec --clean -y
```

## Usando arquivos do editor no Python

```python
from automato import carregar_json, salvar_json

automato = carregar_json("meu_automato.json")  # devolve AFD ou AFN
print(automato.processar("aab"))

afd_minimo = automato.para_afd().minimizar() if hasattr(automato, "para_afd") else automato.minimizar()
salvar_json(afd_minimo, "minimo.json")         # abre no editor com o botão Abrir
```

### Formato do arquivo

```json
{
  "formato": "simaf",
  "versao": 1,
  "estados": [
    { "nome": "q0", "x": 300, "y": 400, "inicial": true, "final": false }
  ],
  "transicoes": [
    { "origem": "q0", "destino": "q0", "simbolos": ["a", "b"], "curva": 0 }
  ]
}
```

Os nomes dos estados precisam ser únicos.
