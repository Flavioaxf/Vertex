from pyvis.network import Network
import networkx as nx

def gerar_visualizacao_grafo(grafo_completo_json, aprovadas, cursando):
    G = nx.DiGraph()
    
    # 0. Limpeza de strings (garante que espaços vindos do PDF não quebrem a leitura)
    aprovadas_clean = [str(c).strip().upper() for c in aprovadas]
    cursando_clean = [str(c).strip().upper() for c in cursando]
    
    # 1. Expandir a grade
    grade_expandida = grafo_completo_json.copy()
    
    # Forçar que qualquer UCE que já exista no JSON seja tratada como obrigatória (nó próprio)
    for cod, info in grade_expandida.items():
        if "UCE" in cod.upper():
            info["tipo"] = "obrigatória"
            
    # Adicionar dinamicamente as UCEs e extras que não estão no JSON
    for cod in (aprovadas_clean + cursando_clean):
        if cod not in grade_expandida and not cod.startswith("SLOT_OPT"):
            is_uce = "UCE" in cod
            grade_expandida[cod] = {
                "nome": "Unidade Curricular de Extensão" if is_uce else "Componente Extracurricular",
                "ch": 60,
                "pre_requisitos": [],
                "tipo": "obrigatória" if is_uce else "optativa"
            }

    # 2. Identificar optativas reais (garantindo que as UCEs não se misturam)
    obrigatorias = {cod for cod, info in grade_expandida.items() if info.get("tipo", "").lower() == "obrigatória"}
    
    optativas_reais_aprovadas = [cod for cod in aprovadas_clean if cod not in obrigatorias and "UCE" not in cod]
    optativas_reais_cursando = [cod for cod in cursando_clean if cod not in obrigatorias and "UCE" not in cod]
    
    # 3. Mapeamento de slots de optativas genéricas
    slots_optativos = sorted([cod for cod in grade_expandida.keys() if cod.startswith("SLOT_OPT")])
    mapeamento_slots = {}
    
    idx_slot = 0
    for cod_real in optativas_reais_aprovadas:
        if idx_slot < len(slots_optativos):
            mapeamento_slots[slots_optativos[idx_slot]] = {"codigo": cod_real, "status": "aprovada"}
            idx_slot += 1
            
    for cod_real in optativas_reais_cursando:
        if idx_slot < len(slots_optativos):
            if not any(m["codigo"] == cod_real for m in mapeamento_slots.values()):
                mapeamento_slots[slots_optativos[idx_slot]] = {"codigo": cod_real, "status": "cursando"}
                idx_slot += 1

    # 4. Adicionando os nós e definindo as cores de status
    for codigo, info in grade_expandida.items():
        codigo_upper = codigo.upper()
        label_exibicao = codigo
        status_final = "pendente"
        
        # Determinar Status Real
        if codigo_upper in mapeamento_slots:
            label_exibicao = mapeamento_slots[codigo_upper]["codigo"]
            status_final = mapeamento_slots[codigo_upper]["status"]
        elif codigo_upper in aprovadas_clean:
            status_final = "aprovada"
        elif codigo_upper in cursando_clean:
            status_final = "cursando"
            
        # Pular optativas que já foram encaixadas num slot
        if not codigo_upper.startswith("SLOT_OPT") and codigo_upper in (optativas_reais_aprovadas + optativas_reais_cursando):
            alocado = any(m["codigo"] == codigo_upper for m in mapeamento_slots.values())
            if alocado:
                continue
                
        titulo_hover = f"{label_exibicao}\n{info.get('nome', '')}\nCH: {info.get('ch', 0)}h"
        
        # Cores alinhadas com a identidade visual do GradPath (Roxo e Rosa)
        if status_final == "aprovada":
            cor_fundo = "#7C3AED" 
            cor_borda = "#5B21B6"
            cor_fonte = "#FFFFFF"
        elif status_final == "cursando":
            cor_fundo = "#DB2777" 
            cor_borda = "#BE185D"
            cor_fonte = "#FFFFFF"
        else:
            cor_fundo = "#F3F4F6" 
            cor_borda = "#CBD5E1"
            cor_fonte = "#475569"
            
        G.add_node(
            codigo, 
            label=label_exibicao, 
            title=titulo_hover, 
            color={"background": cor_fundo, "border": cor_borda, "highlight": {"background": cor_fundo, "border": "#4F46E5"}}, 
            shape="box", 
            font={"color": cor_fonte, "face": "Inter", "size": 14, "bold": True}
        )
        
    # 5. Adicionando as arestas
    for codigo, info in grade_expandida.items():
        for pre_req in info.get("pre_requisitos", []):
            if pre_req in grade_expandida:
                G.add_edge(pre_req, codigo)
                
    # Configuração do renderizador
    net = Network(height="620px", width="100%", directed=True, bgcolor="#FFFFFF")
    net.from_nx(G)
    
    # Motor de física revertido para o espaçamento largo original
    net.set_options("""
    var options = {
      "nodes": {
        "borderWidth": 2,
        "borderWidthSelected": 4,
        "margin": 10
      },
      "edges": {
        "arrows": {
          "to": { "enabled": true, "scaleFactor": 0.6 }
        },
        "color": {
          "color": "#E2E8F0",
          "highlight": "#7C3AED",
          "hover": "#7C3AED"
        },
        "smooth": { "type": "continuous" }
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
        "stabilization": { "enabled": true, "iterations": 200 }
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