import networkx as nx

def gerar_planejamento_coloracao(grafo_original, max_disciplinas, considerar_oferta, semestre_atual_aluno=1):
    """
    Gera o planejamento usando a técnica de Coloração de Grafos.
    As "cores" são representações numéricas dos semestres.
    """
    G = grafo_original.copy()
    
    # 1. Ordenação Topológica: garante que avaliaremos as dependências antes dos alvos
    try:
        ordem_topologica = list(nx.topological_sort(G))
    except nx.NetworkXUnfeasible:
        # Se a grade tiver algum ciclo impossível, o sistema não quebra
        return [{"semestre": 0, "disciplinas": [], "ch_total": 0, "mensagem": "Erro: Ciclo detectado na grade."}]

    cor_do_no = {}           # Nó -> Cor (Ex: NCC0222 -> Semestre 3)
    contagem_por_cor = {}    # Cor -> Quantidade de cadeiras já alocadas
    uces_por_cor = {}        # Cor -> Booleano (Já existe UCE nesta cor?)

    for no in ordem_topologica:
        nome_disciplina = G.nodes[no]['nome'].upper()
        eh_uce = "UCE" in nome_disciplina
        
        # A cor mínima possível é o semestre em que o aluno está entrando
        cor_candidata = semestre_atual_aluno
        
        # Regra 1: A cor DEVE ser maior que a cor de todos os pré-requisitos já processados
        for pre_req in G.predecessors(no):
            if pre_req in cor_do_no:
                cor_candidata = max(cor_candidata, cor_do_no[pre_req] + 1)
        
        # Agora, buscamos o "balde de tinta" (semestre) perfeito iterando a partir da cor candidata
        while True:
            # Regra 2: Respeitar a Oferta Semestral (Par/Ímpar) - Caso 1
            if considerar_oferta:
                tipo_oferta_no = G.nodes[no]['semestre_oferta']
                tipo_cor = 1 if cor_candidata % 2 != 0 else 2
                
                if tipo_cor != tipo_oferta_no and not no.startswith("SLOT_OPT_"):
                    cor_candidata += 1
                    continue

            # Regra 3: Limite máximo daquela cor
            if contagem_por_cor.get(cor_candidata, 0) >= max_disciplinas:
                cor_candidata += 1
                continue
                
            # Regra 4: UCE Única
            if eh_uce and uces_por_cor.get(cor_candidata, False):
                cor_candidata += 1
                continue
                
            # Sobreviveu a todas as regras! Essa é a cor definitiva da disciplina.
            break
            
        # Pinta o nó e atualiza as capacidades das cores
        cor_do_no[no] = cor_candidata
        contagem_por_cor[cor_candidata] = contagem_por_cor.get(cor_candidata, 0) + 1
        if eh_uce:
            uces_por_cor[cor_candidata] = True

    # 2. Reempacotar os dados para exibir na tela no mesmo formato da DFS
    planejamento = []
    if cor_do_no:
        max_cor = max(cor_do_no.values())
        for cor in range(semestre_atual_aluno, max_cor + 1):
            disciplinas_da_cor = [no for no, c in cor_do_no.items() if c == cor]
            
            info_disciplinas = []
            ch_semestre = 0
            for no in disciplinas_da_cor:
                ch = G.nodes[no]['ch']
                ch_semestre += ch
                info_disciplinas.append({"codigo": no, "nome": G.nodes[no]['nome'], "ch": ch})
            
            # Ordena alfabeticamente para ficar limpo visualmente
            info_disciplinas.sort(key=lambda x: x['codigo'])
            
            planejamento.append({
                "semestre": cor,
                "disciplinas": info_disciplinas,
                "ch_total": ch_semestre
            })
            
    return planejamento