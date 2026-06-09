from pyvis.network import Network
import networkx as nx

def gerar_visualizacao_grafo(grafo_completo_json, aprovadas, cursando):
    G = nx.DiGraph()
    
    # Adicionando os nós e definindo as cores de status
    for codigo, info in grafo_completo_json.items():
        # Ocultamos os slots genéricos para limpar o mapa
        if codigo.startswith("SLOT_OPT"):
            continue
            
        titulo_hover = f"{codigo}\n{info['nome']}\nCH: {info['ch']}h"
        
        # Definição de cores com contraste de borda
        if codigo in aprovadas:
            cor_fundo = "#10B981"
            cor_borda = "#059669"
            cor_fonte = "#FFFFFF"
        elif codigo in cursando:
            cor_fundo = "#F59E0B"
            cor_borda = "#D97706"
            cor_fonte = "#FFFFFF"
        else:
            cor_fundo = "#F3F4F6"
            cor_borda = "#9CA3AF"
            cor_fonte = "#374151"
            
        G.add_node(
            codigo, 
            label=codigo, 
            title=titulo_hover, 
            color={"background": cor_fundo, "border": cor_borda, "highlight": {"background": cor_fundo, "border": "#FF6B35"}}, 
            shape="box", 
            font={"color": cor_fonte, "face": "Inter", "size": 14, "bold": True}
        )
        
    # Adicionando as arestas (setas de pré-requisitos)
    for codigo, info in grafo_completo_json.items():
        if codigo.startswith("SLOT_OPT"):
            continue
        for pre_req in info["pre_requisitos"]:
            if pre_req in grafo_completo_json and not pre_req.startswith("SLOT_OPT"):
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