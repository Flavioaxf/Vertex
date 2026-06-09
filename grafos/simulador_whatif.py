import networkx as nx
from grafos.construtor import construir_grafo_aluno, carregar_grade
from grafos.algoritmo_dfs import gerar_planejamento_dfs
from grafos.algoritmo_cores import gerar_planejamento_coloracao

def simular_reprovacao(caminho_grade, aprovadas, cursando, reprovadas_simuladas, max_disciplinas, considerar_oferta, semestre_atual, algoritmo_selecionado):
    """
    Simula o impacto de reprovações no planejamento acadêmico.
    
    Args:
        caminho_grade (str): Caminho para o JSON da grade.
        aprovadas (list): Lista de códigos de disciplinas já aprovadas.
        cursando (list): Lista de códigos de disciplinas sendo cursadas atualmente.
        reprovadas_simuladas (list): Lista de códigos (subconjunto de cursando) para simular reprovação.
        max_disciplinas (int): Limite de disciplinas por semestre.
        considerar_oferta (bool): Se deve respeitar o semestre de oferta (Par/Ímpar).
        semestre_atual (int): Semestre de início da projeção.
        algoritmo_selecionado (str): Nome do algoritmo a ser utilizado.
        
    Returns:
        dict: Resultado da simulação contendo o novo planejamento e dados de impacto.
    """
    # Para simular a reprovação, as disciplinas em 'reprovadas_simuladas' 
    # NÃO devem ser passadas como 'cursando' para o construtor do grafo.
    # Assim, elas permanecerão no grafo como pendentes.
    cursando_efetivo = [c for c in cursando if c not in reprovadas_simuladas]
    
    # Reconstrói o grafo para o cenário de simulação
    grafo_simulacao, dados_grade = construir_grafo_aluno(caminho_grade, aprovadas, cursando_efetivo)
    
    # Executa o algoritmo selecionado
    if "DFS" in algoritmo_selecionado:
        planejamento_simulado = gerar_planejamento_dfs(
            grafo_simulacao, max_disciplinas, considerar_oferta, semestre_atual_aluno=semestre_atual
        )
    else:
        planejamento_simulado = gerar_planejamento_coloracao(
            grafo_simulacao, max_disciplinas, considerar_oferta, semestre_atual
        )
        
    # Identifica bloqueios (sucessores diretos) para cada disciplina reprovada
    # Precisamos do grafo completo para ver as dependências
    G_completo = nx.DiGraph()
    for codigo, info in dados_grade.items():
        G_completo.add_node(codigo, nome=info["nome"])
        for pre_req in info["pre_requisitos"]:
            if pre_req in dados_grade:
                G_completo.add_edge(pre_req, codigo)
    
    bloqueios = {}
    for codigo in reprovadas_simuladas:
        nome_base = dados_grade.get(codigo, {}).get("nome", codigo)
        sucessores = list(G_completo.successors(codigo))
        nomes_sucessores = [dados_grade.get(s, {}).get("nome", s) for s in sucessores]
        bloqueios[codigo] = {
            "nome": nome_base,
            "bloqueia": nomes_sucessores
        }
        
    return {
        "planejamento": planejamento_simulado,
        "bloqueios": bloqueios
    }
