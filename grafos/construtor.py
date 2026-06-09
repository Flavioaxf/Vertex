import json
import networkx as nx

def carregar_grade(caminho_json):
    with open(caminho_json, 'r', encoding='utf-8') as f:
        return json.load(f)

def construir_grafo_aluno(caminho_json, disciplinas_aprovadas, disciplinas_cursando):
    dados_grade = carregar_grade(caminho_json)
    G = nx.DiGraph()

    # 1. Monta os nós da grade base
    for codigo, info in dados_grade.items():
        G.add_node(
            codigo,
            nome=info["nome"],
            ch=info["ch"],
            tipo=info["tipo"],
            periodo_ideal=info["periodo_ideal"],
            semestre_oferta=info["semestre_oferta"]
        )

    # 2. Monta as setas de dependências
    for codigo, info in dados_grade.items():
        for pre_req in info["pre_requisitos"]:
            if pre_req in dados_grade: 
                G.add_edge(pre_req, codigo)

    # Unifica tudo o que o aluno já superou ou está cursando agora
    todas_vencidas = set(disciplinas_aprovadas + disciplinas_cursando)

    obrigatorias_concluidas = []
    qtd_optativas_concluidas = 0

    for codigo in todas_vencidas:
        # Se está mapeado no JSON e não é um marcador genérico, remove como obrigatória
        if codigo in dados_grade and not codigo.startswith("SLOT_OPT_"):
            obrigatorias_concluidas.append(codigo)
        else:
            # Se for um código de optativa da lista da UERN (como CAN0073, CAN0065, CAN0062),
            # incrementa o contador para eliminar um slot em aberto
            qtd_optativas_concluidas += 1

    # 4. Remove obrigatórias do grafo
    for codigo in obrigatorias_concluidas:
        if G.has_node(codigo):
            G.remove_node(codigo)

    # 5. Elimina os slots de optativas em aberto na ordem estrita (I, II, III...)
    slots_optativas_no_grafo = [n for n in G.nodes() if n.startswith("SLOT_OPT_")]
    
    # Ao ordenar alfabeticamente pela chave (SLOT_OPT_1, SLOT_OPT_2, etc), 
    # garantimos que a Optativa I saia antes da Optativa II
    slots_optativas_no_grafo.sort()

    for _ in range(qtd_optativas_concluidas):
        if slots_optativas_no_grafo:
            slot_a_remover = slots_optativas_no_grafo.pop(0)
            G.remove_node(slot_a_remover)

    return G, dados_grade