import networkx as nx

def calcular_prioridade_dfs(grafo, no, memo):
    if no in memo:
        return memo[no]
    
    sucessores = list(grafo.successors(no))
    
    if not sucessores:
        memo[no] = 1
        return 1
        
    max_profundidade = 0
    for suc in sucessores:
        profundidade = calcular_prioridade_dfs(grafo, suc, memo)
        if profundidade > max_profundidade:
            max_profundidade = profundidade
            
    memo[no] = max_profundidade + 1
    return memo[no]

def gerar_planejamento_dfs(grafo_original, max_disciplinas, considerar_oferta, semestre_atual_aluno=1):
    G = grafo_original.copy()
    planejamento = []
    semestre_simulado = semestre_atual_aluno
    memo_dfs = {}

    while G.number_of_nodes() > 0:
        # 1. Identificar disciplinas sem pré-requisitos pendentes
        disponiveis = [n for n, d in G.in_degree() if d == 0]
        
        # 2. Filtrar por semestre de oferta (Caso 1)
        if considerar_oferta:
            tipo_semestre = 1 if semestre_simulado % 2 != 0 else 2
            disponiveis = [
                n for n in disponiveis 
                if G.nodes[n]['semestre_oferta'] == tipo_semestre
            ]
        
        if not disponiveis:
            planejamento.append({
                "semestre": semestre_simulado,
                "disciplinas": [],
                "ch_total": 0,
                "mensagem": "Nenhuma disciplina disponível (aguardando oferta semestral)"
            })
            semestre_simulado += 1
            if semestre_simulado > 30: 
                break
            continue

        # 3. Calcular prioridades via DFS
        prioridades = {}
        for no in disponiveis:
            prioridades[no] = calcular_prioridade_dfs(G, no, memo_dfs)
        
        # Ordena: Prioridade Alta (-), Carga Horária Alta (-), Código Crescente (alfabético normal)
        disponiveis.sort(key=lambda x: (-prioridades[x], -G.nodes[x]['ch'], x))
        
        # 4. Seleção com limite máximo de cadeiras E restrição de UCE Única por Semestre
        selecionadas = []
        tem_uce_no_semestre = False

        for no in disponiveis:
            if len(selecionadas) >= max_disciplinas:
                break
                
            nome_disciplina = G.nodes[no]['nome'].upper()
            
            # Aplicação da nova regra de UCE
            if "UCE" in nome_disciplina:
                if tem_uce_no_semestre:
                    continue  # Pula esta UCE, pois já tem uma alocada para este período
                else:
                    selecionadas.append(no)
                    tem_uce_no_semestre = True
            else:
                selecionadas.append(no)
        
        # Se por travas de UCE/Oferta nada pôde ser selecionado nesta iteração
        if not selecionadas:
            semestre_simulado += 1
            continue

        # 5. Registrar dados do período calculado
        ch_semestre = sum(G.nodes[n]['ch'] for n in selecionadas)
        info_disciplinas = [{"codigo": n, "nome": G.nodes[n]['nome'], "ch": G.nodes[n]['ch']} for n in selecionadas]
        
        planejamento.append({
            "semestre": semestre_simulado,
            "disciplinas": info_disciplinas,
            "ch_total": ch_semestre
        })
        
        # 6. Remover as disciplinas cursadas do grafo para a próxima rodada
        G.remove_nodes_from(selecionadas)
        semestre_simulado += 1

    return planejamento