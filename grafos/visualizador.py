from pyvis.network import Network
import networkx as nx

def gerar_visualizacao_grafo(grafo_completo_json, aprovadas, cursando):
    G = nx.DiGraph()
    
    # Identificar optativas reais que foram aprovadas ou estão sendo cursadas
    # (Códigos que não estão no JSON original ou estão mas são do tipo 'optativa')
    obrigatorias = {cod for cod, info in grafo_completo_json.items() if info.get("tipo") == "obrigatória"}
    
    optativas_reais_aprovadas = [cod for cod in aprovadas if cod not in obrigatorias]
    optativas_reais_cursando = [cod for cod in cursando if cod not in obrigatorias]
    
    # Mapeamento de slots de optativas
    slots_optativos = sorted([cod for cod in grafo_completo_json.keys() if cod.startswith("SLOT_OPT")])
    mapeamento_slots = {}
    
    # Preencher slots com optativas aprovadas primeiro, depois cursando
    idx_slot = 0
    for cod_real in optativas_reais_aprovadas:
        if idx_slot < len(slots_optativos):
            mapeamento_slots[slots_optativos[idx_slot]] = {"codigo": cod_real, "status": "aprovada"}
            idx_slot += 1
            
    for cod_real in optativas_reais_cursando:
        if idx_slot < len(slots_optativos):
            # Evitar duplicata se por algum motivo o mesmo código estiver em ambas as listas
            if not any(m["codigo"] == cod_real for m in mapeamento_slots.values()):
                mapeamento_slots[slots_optativos[idx_slot]] = {"codigo": cod_real, "status": "cursando"}
                idx_slot += 1

    # Adicionando os nós e definindo as cores de status
    for codigo, info in grafo_completo_json.items():
        # Lógica especial para slots de optativas
        label_exibicao = codigo
        status_final = "pendente"
        
        if codigo in mapeamento_slots:
            label_exibicao = mapeamento_slots[codigo]["codigo"]
            status_final = mapeamento_slots[codigo]["status"]
        elif codigo in aprovadas:
            status_final = "aprovada"
        elif codigo in cursando:
            status_final = "cursando"
            
        titulo_hover = f"{label_exibicao}\n{info['nome']}\nCH: {info['ch']}h"
        
        # Definição de cores com contraste de borda
        if status_final == "aprovada":
            cor_fundo = "#10B981" # Verde (Integralizado)
            cor_borda = "#059669"
            cor_fonte = "#FFFFFF"
        elif status_final == "cursando":
            cor_fundo = "#F59E0B" # Amarelo/Âmbar (Em Andamento)
            cor_borda = "#D97706"
            cor_fonte = "#FFFFFF"
        else:
            cor_fundo = "#F3F4F6"
            cor_borda = "#9CA3AF"
            cor_fonte = "#374151"
            
        G.add_node(
            codigo, 
            label=label_exibicao, 
            title=titulo_hover, 
            color={"background": cor_fundo, "border": cor_borda, "highlight": {"background": cor_fundo, "border": "#FF6B35"}}, 
            shape="box", 
            font={"color": cor_fonte, "face": "Inter", "size": 14, "bold": True}
        )
        
    # Adicionando as arestas (setas de pré-requisitos)
    for codigo, info in grafo_completo_json.items():
        for pre_req in info["pre_requisitos"]:
            if pre_req in grafo_completo_json:
                G.add_edge(pre_req, codigo)
                
    # Configuração do renderizador de rede
    net = Network(height="620px", width="100%", directed=True, bgcolor="#FFFFFF")
    net.from_nx(G)
    
    # Motor de física Barnes-Hut para modelagem orgânica
    net.set_options("""
    var options = {
      "nodes": {
        "borderWidth": 2,
        "borderWidthSelected": 4,
        "margin": 10
      },
      "edges": {
        "arrows": {
          "to": {
            "enabled": true,
            "scaleFactor": 0.6
          }
        },
        "color": {
          "color": "#D1D5DB",
          "highlight": "#FF6B35",
          "hover": "#FF6B35"
        },
        "smooth": {
          "type": "continuous"
        }
      },
      "physics": {
        "enabled": true,
        "barnesHut": {
          "gravitationalConstant": -2500,
          "centralGravity": 0.2,
          "springLength": 180,
          "springConstant": 0.05,
          "damping": 0.09,
          "avoidOverlap": 0.5
        },
        "stabilization": {
          "enabled": true,
          "iterations": 200
        }
      },
      "interaction": {
        "hover": true,
        "navigationButtons": true,
        "zoomView": true,
        "dragView": true
      }
    }
    """)
    
    return net