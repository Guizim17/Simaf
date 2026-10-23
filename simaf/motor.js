/*
 * Motor de autômatos finitos do SIMAF.
 *
 * Funções puras (sem DOM), usadas pelo editor.html e pelos testes em Python
 * (via Node), garantindo que a interface siga as mesmas regras do automato.py.
 *
 * Modelo esperado:
 *   { states: [{id, label, isFinal}], transitions: [{id, from, to, symbols}], initial }
 * onde `symbols` pode ser um Set ou um array de strings.
 */
(function (global) {
'use strict';

const EPS = 'ε';
const NOME_MAX = 12;  // acima disso, a minimização renomeia os estados

function simbolosDe(t) {
  return t.symbols instanceof Set ? t.symbols : new Set(t.symbols);
}

// mapa[estado][simbolo] = Set(destinos)
function mapaTransicoes(auto) {
  const mapa = new Map();
  for (const s of auto.states) mapa.set(s.id, new Map());
  for (const t of auto.transitions) {
    const saidas = mapa.get(t.from);
    if (!saidas) continue;
    for (const sym of simbolosDe(t)) {
      if (!saidas.has(sym)) saidas.set(sym, new Set());
      saidas.get(sym).add(t.to);
    }
  }
  return mapa;
}

// Alfabeto inferido das transições (ε não faz parte do alfabeto).
function alfabeto(auto) {
  const sigma = new Set();
  for (const t of auto.transitions)
    for (const sym of simbolosDe(t)) if (sym !== EPS) sigma.add(sym);
  return [...sigma].sort();
}

// AFN se houver ε-transição ou dois destinos para o mesmo (estado, símbolo).
function ehAFN(auto) {
  for (const saidas of mapaTransicoes(auto).values())
    for (const [sym, destinos] of saidas)
      if (sym === EPS || destinos.size > 1) return true;
  return false;
}

/*
 * Divide a entrada em símbolos do alfabeto.
 *  - Com espaços: cada palavra separada por espaço é um símbolo ("if x else").
 *  - Sem espaços: casamento guloso pelo símbolo mais longo do alfabeto;
 *    caracteres que não casam viram símbolos isolados (e serão rejeitados).
 */
function tokenizar(entrada, sigma) {
  if (/\s/.test(entrada)) return entrada.split(/\s+/).filter(Boolean);
  const simbolos = [...sigma].sort((a, b) => b.length - a.length);
  const tokens = [];
  let i = 0;
  while (i < entrada.length) {
    const s = simbolos.find(s => entrada.startsWith(s, i));
    if (s) { tokens.push(s); i += s.length; }
    else {
      const ch = String.fromCodePoint(entrada.codePointAt(i));
      tokens.push(ch); i += ch.length;
    }
  }
  return tokens;
}

function fechoEpsilon(conjunto, mapa) {
  const fecho = new Set(conjunto);
  const pilha = [...conjunto];
  while (pilha.length) {
    const s = pilha.pop();
    for (const d of (mapa.get(s)?.get(EPS) || []))
      if (!fecho.has(d)) { fecho.add(d); pilha.push(d); }
  }
  return fecho;
}

function transicoesEpsilonDentro(auto, conjunto, usadas) {
  for (const t of auto.transitions)
    if (conjunto.has(t.from) && simbolosDe(t).has(EPS)) usadas.add(t.id);
}

/*
 * Simula o autômato (AFD ou AFN) mantendo o conjunto de estados ativos.
 * Cada passo guarda todas as transições percorridas, inclusive ε.
 */
function simular(auto, entrada) {
  if (auto.initial === null || auto.initial === undefined) return null;
  const mapa = mapaTransicoes(auto);
  const finais = new Set(auto.states.filter(s => s.isFinal).map(s => s.id));
  const tokens = tokenizar(entrada, alfabeto(auto));

  let atual = fechoEpsilon(new Set([auto.initial]), mapa);
  const usadas0 = new Set();
  transicoesEpsilonDentro(auto, atual, usadas0);
  const steps = [{ activeStates: new Set(atual), symbol: null, usedTransitions: usadas0 }];

  for (const sym of tokens) {
    const prox = new Set();
    const usadas = new Set();
    if (sym !== EPS) {
      for (const t of auto.transitions)
        if (atual.has(t.from) && simbolosDe(t).has(sym)) { prox.add(t.to); usadas.add(t.id); }
    }
    atual = fechoEpsilon(prox, mapa);
    transicoesEpsilonDentro(auto, atual, usadas);
    steps.push({ activeStates: new Set(atual), symbol: sym, usedTransitions: usadas });
  }

  return { accepted: [...atual].some(id => finais.has(id)), steps, tokens, input: entrada };
}

// Agrupa transições (origem, símbolo) → destino em arestas por par de estados.
function agruparArestas(delta) {
  const arestas = new Map();
  for (const [origem, saidas] of delta)
    for (const [sym, destino] of saidas) {
      const k = origem + '>' + destino;
      if (!arestas.has(k)) arestas.set(k, { from: origem, to: destino, symbols: [] });
      arestas.get(k).symbols.push(sym);
    }
  return [...arestas.values()].map((a, i) => ({ id: i, ...a }));
}

/*
 * Construção de subconjuntos: AFN (com ε) → AFD equivalente.
 * Os estados novos se chamam '{q0,q1}', como em automato.py.
 * O conjunto vazio não vira estado (AFD parcial).
 * `depth` é a distância em BFS a partir do inicial, usada para o layout.
 */
function paraAFD(auto) {
  if (auto.initial === null || auto.initial === undefined) return null;
  const mapa = mapaTransicoes(auto);
  const rotulo = new Map(auto.states.map(s => [s.id, s.label]));
  const finais = new Set(auto.states.filter(s => s.isFinal).map(s => s.id));
  const sigma = alfabeto(auto);

  const novos = [];
  const indice = new Map();
  const delta = new Map();
  const fila = [];

  const registrar = (conj, depth) => {
    const chave = [...conj].sort((a, b) => a - b).join(',');
    if (!indice.has(chave)) {
      const id = novos.length;
      indice.set(chave, id);
      novos.push({
        id,
        label: '{' + [...conj].map(x => rotulo.get(x)).sort().join(',') + '}',
        isFinal: [...conj].some(x => finais.has(x)),
        depth,
      });
      delta.set(id, new Map());
      fila.push([id, conj]);
    }
    return indice.get(chave);
  };

  registrar(fechoEpsilon(new Set([auto.initial]), mapa), 0);
  while (fila.length) {
    const [id, conj] = fila.shift();
    for (const sym of sigma) {
      const mov = new Set();
      for (const s of conj) for (const d of (mapa.get(s)?.get(sym) || [])) mov.add(d);
      if (!mov.size) continue;
      const destino = registrar(fechoEpsilon(mov, mapa), novos[id].depth + 1);
      delta.get(id).set(sym, destino);
    }
  }

  return { states: novos, transitions: agruparArestas(delta), initial: 0 };
}

/*
 * Minimização (refinamento de partições de Moore).
 * AFN é convertido antes; estados inalcançáveis são descartados; estados
 * mortos (que nunca chegam a um final) são removidos do resultado.
 * Estados equivalentes fundidos recebem o nome '{a,b}'.
 */
function minimizar(auto) {
  if (auto.initial === null || auto.initial === undefined) return null;
  const afd = ehAFN(auto) ? paraAFD(auto) : auto;
  const sigma = alfabeto(afd);
  const mapa = mapaTransicoes(afd);
  const porId = new Map(afd.states.map(s => [s.id, s]));

  // Estados alcançáveis
  const alc = [afd.initial];
  const vistos = new Set(alc);
  for (let i = 0; i < alc.length; i++)
    for (const destinos of mapa.get(alc[i]).values())
      for (const d of destinos) if (!vistos.has(d)) { vistos.add(d); alc.push(d); }

  // Função total com estado sumidouro
  const SUMIDOURO = '__sumidouro__';
  const prox = (s, a) => {
    if (s === SUMIDOURO) return SUMIDOURO;
    const d = mapa.get(s).get(a);
    return d && d.size ? [...d][0] : SUMIDOURO;
  };
  const todos = [...alc, SUMIDOURO];
  const ehFinal = s => s !== SUMIDOURO && porId.get(s).isFinal;

  let classe = new Map(todos.map(s => [s, ehFinal(s) ? 'F' : 'N']));
  let qtd = new Set(classe.values()).size;
  for (;;) {
    const assinaturas = new Map();
    const nova = new Map();
    for (const s of todos) {
      const sig = classe.get(s) + '|' + sigma.map(a => classe.get(prox(s, a))).join(',');
      if (!assinaturas.has(sig)) assinaturas.set(sig, assinaturas.size);
      nova.set(s, assinaturas.get(sig));
    }
    classe = nova;
    if (assinaturas.size === qtd) break;
    qtd = assinaturas.size;
  }

  const classeMorta = classe.get(SUMIDOURO);
  const classeInicial = classe.get(afd.initial);

  // Linguagem vazia: sobra só o estado inicial, sem transições.
  if (classeInicial === classeMorta) {
    const ini = porId.get(afd.initial);
    return { states: [{ id: 0, label: ini.label, isFinal: false, depth: 0 }], transitions: [], initial: 0 };
  }

  // Renumera as classes em BFS a partir do inicial
  const membros = new Map();
  for (const s of alc) {
    const c = classe.get(s);
    if (c === classeMorta) continue;
    if (!membros.has(c)) membros.set(c, []);
    membros.get(c).push(s);
  }
  const novoId = new Map([[classeInicial, 0]]);
  const ordem = [classeInicial];
  const profundidade = new Map([[classeInicial, 0]]);
  const delta = new Map();
  for (let i = 0; i < ordem.length; i++) {
    const c = ordem[i];
    const rep = membros.get(c)[0];
    const saidas = new Map();
    for (const a of sigma) {
      const d = prox(rep, a);
      const cd = classe.get(d);
      if (cd === classeMorta) continue;
      if (!novoId.has(cd)) {
        novoId.set(cd, ordem.length);
        ordem.push(cd);
        profundidade.set(cd, profundidade.get(c) + 1);
      }
      saidas.set(a, novoId.get(cd));
    }
    delta.set(novoId.get(c), saidas);
  }

  const states = ordem.map(c => {
    const nomes = membros.get(c).map(s => porId.get(s).label).sort();
    return {
      id: novoId.get(c),
      label: nomes.length === 1 ? nomes[0] : '{' + nomes.join(',') + '}',
      isFinal: ehFinal(membros.get(c)[0]),
      depth: profundidade.get(c),
    };
  });
  // Nomes compostos longos ficam ilegíveis: renomeia tudo para q0, q1, ... (ordem BFS)
  if (states.some(s => s.label.length > NOME_MAX)) states.forEach((s, i) => { s.label = 'q' + i; });
  return { states, transitions: agruparArestas(delta), initial: 0 };
}

/*
 * Formato de arquivo .json (compartilhado com automato.py):
 * { formato: "simaf", versao: 1,
 *   estados:    [{nome, x, y, inicial, final}],
 *   transicoes: [{origem, destino, simbolos: [...], curva}] }
 */
function deJSON(obj) {
  if (!obj || obj.formato !== 'simaf' || !Array.isArray(obj.estados) || !Array.isArray(obj.transicoes))
    throw new Error('Arquivo não está no formato do SIMAF.');
  const ids = new Map();
  const states = obj.estados.map((e, i) => {
    if (typeof e.nome !== 'string' || !e.nome) throw new Error(`Estado ${i + 1} sem nome.`);
    if (ids.has(e.nome)) throw new Error(`Estado duplicado: '${e.nome}'.`);
    ids.set(e.nome, i);
    return { id: i, label: e.nome, isFinal: !!e.final, x: e.x, y: e.y };
  });
  const ini = obj.estados.findIndex(e => e.inicial);
  const transitions = obj.transicoes.map((t, i) => {
    if (!ids.has(t.origem) || !ids.has(t.destino))
      throw new Error(`Transição ${i + 1} usa um estado inexistente.`);
    return { id: i, from: ids.get(t.origem), to: ids.get(t.destino),
             symbols: new Set(t.simbolos || []), curve: t.curva || 0 };
  });
  return { states, transitions, initial: ini >= 0 ? ini : null };
}

function paraJSON(auto) {
  const nome = new Map(auto.states.map(s => [s.id, s.label]));
  return {
    formato: 'simaf',
    versao: 1,
    estados: auto.states.map(s => ({
      nome: s.label, x: Math.round(s.x ?? 0), y: Math.round(s.y ?? 0),
      inicial: s.id === auto.initial, final: !!s.isFinal,
    })),
    transicoes: auto.transitions
      .filter(t => simbolosDe(t).size)
      .map(t => ({ origem: nome.get(t.from), destino: nome.get(t.to),
                   simbolos: [...simbolosDe(t)], curva: Math.round(t.curve || 0) })),
  };
}

const Motor = { EPS, alfabeto, ehAFN, tokenizar, fechoEpsilon, mapaTransicoes,
                simular, paraAFD, minimizar, deJSON, paraJSON };

if (typeof module !== 'undefined' && module.exports) module.exports = Motor;
else global.Motor = Motor;
})(typeof window !== 'undefined' ? window : globalThis);
