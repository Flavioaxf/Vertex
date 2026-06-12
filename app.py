import streamlit as st
import streamlit.components.v1 as components
import os
import graphviz
import base64

from modulos.extrator_pdf import extrair_dados_historico
from grafos.construtor import construir_grafo_aluno
from grafos.algoritmo_dfs import gerar_planejamento_dfs
from grafos.algoritmo_cores import gerar_planejamento_coloracao
from grafos.visualizador import gerar_visualizacao_grafo
from grafos.simulador_whatif import simular_reprovacao

# ==========================================
# Configuração da Página e CSS
# ==========================================
st.set_page_config(page_title="GradPath | Otimizador Curricular", layout="wide", initial_sidebar_state="expanded")

def carregar_css():
    diretorio_atual = os.path.dirname(os.path.abspath(__file__))
    caminho_css = os.path.join(diretorio_atual, 'assets', 'style.css')
    
    if os.path.exists(camincss := caminho_css):
        with open(camincss, encoding='utf-8') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

carregar_css()

def formatar_nome(nome_completo):
    if not nome_completo or nome_completo == "Não identificado":
        return nome_completo
        
    partes = nome_completo.strip().split()
    
    if len(partes) <= 4:
        return nome_completo.title()
        
    primeiro = partes[0].title()
    ultimo = partes[-1].title()
    meio = " ".join([p[0].upper() + "." for p in partes[1:-1] if len(p) > 2])
    
    return f"{primeiro} {meio} {ultimo}"

def get_base64_image(caminho_imagem):
    with open(caminho_imagem, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

# ==========================================
# Menu Lateral (Sidebar Profissional)
# ==========================================
with st.sidebar:
    # Embutindo a imagem diretamente no HTML para alinhamento perfeito (Flexbox)
    diretorio_atual = os.path.dirname(os.path.abspath(__file__))
    caminho_logo = os.path.join(diretorio_atual, 'assets', 'logo.png')
    
    if os.path.exists(caminho_logo):
        img_b64 = get_base64_image(caminho_logo)
        img_html = f'<img src="data:image/png;base64,{img_b64}" style="width: 48px; height: 48px; object-fit: contain;">'
    else:
        img_html = "<div style='width: 48px; height: 48px; background-color: #E5E7EB; border-radius: 8px;'></div>"

    st.markdown(f"""
    <div style="display: flex; flex-direction: column; margin-bottom: 2.5rem; padding-bottom: 1.5rem; border-bottom: 1px solid #E5E7EB;">
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 6px;">
            {img_html}
            <h1 class="logo-gradpath" style="margin: 0; padding-bottom: 4px;">GradPath</h1>
        </div>
        <p style="color: #6B7280; font-size: 0.70rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1.2px; margin: 0;">Otimizador Curricular Avançado</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<p style='font-weight: 700; font-size: 0.8rem; color: #374151; text-transform: uppercase; margin-bottom: 5px; letter-spacing: 0.5px;'>Anexar Histórico do SIGAA</p>", unsafe_allow_html=True)
    arquivo_historico = st.file_uploader("Upload de Histórico", type=["pdf"], label_visibility="collapsed")
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<p style='font-weight: 700; font-size: 0.8rem; color: #374151; text-transform: uppercase; margin-bottom: 5px; letter-spacing: 0.5px;'>Parâmetros de Otimização</p>", unsafe_allow_html=True)
    
    max_disciplinas = st.slider("Cadeiras por período letivo", min_value=5, max_value=7, value=6)
    semestre_atual = st.number_input("Início da projeção (Oferta 1 = Ímpar, 2 = Par)", min_value=1, max_value=2, value=1, format="%d")
    
    caso_selecionado = st.selectbox(
        "Restrição de oferta (semestralidade)",
        options=["Respeitar oferta padrão da grade", "Ignorar oferta (forçar alocação)"]
    )
    considerar_oferta = True if "Respeitar" in caso_selecionado else False
    
    algoritmo_selecionado = st.selectbox(
        "Motor de resolução matemática",
        options=["Busca em profundidade (DFS)", "Coloração de vértices (Greedy)"]
    )
    
    gerar = st.button("Processar malha curricular", type="primary", use_container_width=True)

# ==========================================
# Tela Principal (Main Dashboard)
# ==========================================
if gerar:
    if arquivo_historico is None:
        st.warning("Nenhum documento detectado. Anexe o histórico para continuar.", icon=":material/warning:")
    else:
        with st.spinner('Construindo malha de grafos e resolvendo dependências matemáticas...'):
            try:
                perfil, aprovadas, cursando = extrair_dados_historico(arquivo_historico)
            except ValueError as e:
                st.error(str(e))
                st.stop()
                
            caminho_grade = "data/grade_cc.json"
            grafo_aluno, dados_grade = construir_grafo_aluno(caminho_grade, aprovadas, cursando)
            
            if "DFS" in algoritmo_selecionado:
                planejamento = gerar_planejamento_dfs(
                    grafo_aluno, max_disciplinas, considerar_oferta, semestre_atual_aluno=semestre_atual
                )
            else:
                planejamento = gerar_planejamento_coloracao(
                    grafo_aluno, max_disciplinas, considerar_oferta, semestre_atual
                )
            
            # Armazenar no session_state para persistência entre interações
            st.session_state.perfil = perfil
            st.session_state.aprovadas = aprovadas
            st.session_state.cursando = cursando
            st.session_state.planejamento = planejamento
            st.session_state.dados_grade = dados_grade
            st.session_state.caminho_grade = caminho_grade
            st.session_state.parametros = {
                "max_disciplinas": max_disciplinas,
                "considerar_oferta": considerar_oferta,
                "semestre_atual": semestre_atual,
                "algoritmo_selecionado": algoritmo_selecionado
            }
            # Limpar cache de simulações anteriores ao reprocessar
            st.session_state.pop("sim_reprovadas", None)
            
            st.session_state.processado = True

if not st.session_state.get('processado', False):
    st.header("Painel de Planejamento Integrado")
    st.markdown("Universidade do Estado do Rio Grande do Norte (UERN) | Ciência da Computação")
    st.info("Utilize o menu lateral para anexar o documento em PDF e iniciar a configuração de matrizes.", icon=":material/arrow_back:")

else:
    # Recuperar dados originais do estado
    perfil = st.session_state.perfil
    aprovadas = st.session_state.aprovadas
    cursando = st.session_state.cursando
    planejamento_original = st.session_state.planejamento
    dados_grade = st.session_state.dados_grade
    caminho_grade = st.session_state.caminho_grade
    params = st.session_state.parametros

    # ==========================================
    # LÓGICA DE ESTADO GLOBAL (SIMULAÇÃO DE REPROVAÇÃO)
    # ==========================================
    opcoes_cursando = {dados_grade[c]['nome']: c for c in cursando if c in dados_grade}
    nomes_cursando = list(opcoes_cursando.keys())
    
    # Pega os valores que o utilizador selecionou na aba de simulação (pela key do widget)
    selecionadas_nomes = st.session_state.get("sim_reprovadas", [])
    reprovadas_simuladas = [opcoes_cursando[nome] for nome in selecionadas_nomes if nome in opcoes_cursando]
    
    # Remove as reprovadas da lista de "cursando" para que o grafo fique cinza (pendente)
    cursando_ativo = [c for c in cursando if c not in reprovadas_simuladas]
    
    # Calcula o planeamento ativo que vai ser injetado em toda a tela
    if reprovadas_simuladas:
        resultado_sim = simular_reprovacao(
            caminho_grade, aprovadas, cursando, reprovadas_simuladas,
            params["max_disciplinas"], params["considerar_oferta"],
            params["semestre_atual"], params["algoritmo_selecionado"]
        )
        planejamento_ativo = resultado_sim["planejamento"]
        bloqueios = resultado_sim["bloqueios"]
    else:
        planejamento_ativo = planejamento_original
        bloqueios = {}

    # ==========================================
    # RENDERIZAÇÃO DO DASHBOARD SUPERIOR
    # ==========================================
    st.markdown("<p style='font-size: 0.85rem; text-transform: uppercase; color: #6B7280; font-weight: 700; letter-spacing: 1px; margin-bottom: -15px;'>Perfil Acadêmico</p>", unsafe_allow_html=True)
    
    nome_formatado = formatar_nome(perfil["nome"])
    st.markdown(f"<h1 style='color: #7C3AED; font-size: 3.2rem; font-weight: 900; letter-spacing: -1.5px; margin-bottom: 25px;'>{nome_formatado}</h1>", unsafe_allow_html=True)
    
    col_p1, col_p2, col_p3 = st.columns(3)
    col_p1.metric(label="Matrícula", value=perfil["matricula"])
    col_p2.metric(label="Índice de Rendimento (IRA)", value=perfil["ira"])
    
    semestres_necessarios = len([p for p in planejamento_ativo if p['disciplinas']])
    col_p3.metric(label="Projeção de conclusão", value=f"{semestres_necessarios} Semestres")
    
    st.write("") 
    
    with st.expander("Registro de Componentes Lidos do SIGAA", expanded=False):
        st.write(f"**Validados ({len(aprovadas)}):** {', '.join(aprovadas) if aprovadas else 'Nenhum'}")
        st.write(f"**Em Andamento Ativos ({len(cursando_ativo)}):** {', '.join(cursando_ativo) if cursando_ativo else 'Nenhum'}")
    
    st.markdown("---")
    st.markdown(f"### Matriz de Integralização Projetada")
    
    # ==========================================
    # RENDERIZAÇÃO DAS ABAS INTEGRADAS
    # ==========================================
    aba_lista, aba_grafo, aba_simulacao = st.tabs([
        "Matriz Projetada (Estrutural)", 
        "Mapa de Dependências (Grafo)",
        "Simulação What-If"
    ])
    
    with aba_lista:
        st.markdown("<br>", unsafe_allow_html=True)
        # O planeamento agora é desenhado com base no planejamento_ativo (que muda se houver simulação)
        for periodo in planejamento_ativo:
            sem = periodo['semestre']
            discs = periodo['disciplinas']
            ch_total = periodo['ch_total']
            tipo_semestre = "Ímpar" if sem % 2 != 0 else "Par"
            
            titulo_expander = f"Período Letivo {sem} (Oferta {tipo_semestre}) — {len(discs)} Componentes — {ch_total}h Totais"
            
            with st.expander(titulo_expander, expanded=True):
                if not discs:
                    st.info(periodo.get('mensagem', 'Bloqueio de alocação por dependência de oferta semestral.'), icon=":material/lock:")
                else:
                    for d in discs:
                        st.markdown(f"- `{d['codigo']}` | **{d['nome']}** *(CH: {d['ch']}h)*")
                        
    with aba_grafo:
        st.markdown("""
        <div style="display: flex; gap: 15px; margin-bottom: 15px;">
            <span style="color: #7C3AED; font-weight: bold;">■ Integralizado</span>
            <span style="color: #DB2777; font-weight: bold;">■ Em Andamento</span>
            <span style="color: #9CA3AF; font-weight: bold;">■ Pendente</span>
        </div>
        """, unsafe_allow_html=True)
        
        # O grafo agora é gerado usando cursando_ativo (as matérias reprovadas ficarão cinza/pendentes)
        net = gerar_visualizacao_grafo(dados_grade, aprovadas, cursando_ativo)
        arquivo_html = "grafo_curricular.html"
        net.save_graph(arquivo_html)
        
        with open(arquivo_html, 'r', encoding='utf-8') as f:
            codigo_html = f.read()
            
        components.html(codigo_html, height=620, scrolling=False)

        # Atualizando a exportação PDF/SVG para usar o cursando_ativo
        st.markdown("<br>", unsafe_allow_html=True)
        col_exp1, col_exp2 = st.columns(2)

        def gerar_svg_pdf(formato):
            dot = graphviz.Digraph(comment='Mapa de Dependências GradPath', format=formato)
            dot.attr(rankdir='TB', size='12,12')
            dot.attr('node', shape='box', style='filled', fontname='Arial', fontsize='10')

            COR_APROVADA = "#4CAF50"
            COR_CURSANDO = "#FFC107"
            COR_PENDENTE = "#9E9E9E"

            for codigo, info in dados_grade.items():
                cor = COR_PENDENTE
                if codigo in aprovadas:
                    cor = COR_APROVADA
                elif codigo in cursando_ativo:
                    cor = COR_CURSANDO
                
                label = f"{codigo}\n{info['nome']}"
                dot.node(codigo, label=label, fillcolor=cor, fontcolor='white', color=cor)

            for codigo, info in dados_grade.items():
                for pre_req in info.get("pre_requisitos", []):
                    if pre_req in dados_grade:
                        dot.edge(pre_req, codigo)
            
            return dot.pipe()

        try:
            with col_exp1:
                st.download_button(
                    label="⬇ Exportar SVG",
                    data=gerar_svg_pdf('svg'),
                    file_name="mapa_dependencias_gradpath.svg",
                    mime="image/svg+xml",
                    use_container_width=True
                )
            with col_exp2:
                st.download_button(
                    label="⬇ Exportar PDF",
                    data=gerar_svg_pdf('pdf'),
                    file_name="mapa_dependencias_gradpath.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
        except Exception as e:
            st.error(f"Erro ao gerar exportação: Verifique se o Graphviz está instalado no sistema. {e}")
        st.info("Para exportação funcionar, instale o Graphviz em: https://graphviz.org/download/")

    with aba_simulacao:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### Simulador de Impacto de Reprovação")
        st.markdown("Selecione abaixo as disciplinas que você está cursando. Ao fazer a seleção, o sistema reescreverá a matriz estrutural e atualizará o grafo matemático instantaneamente.")
        
        # A Mágica: ao selecionar aqui, a chave "sim_reprovadas" é ativada e o código roda novamente desde o topo!
        st.multiselect(
            "Selecione disciplinas para simular reprovação:",
            options=nomes_cursando,
            key="sim_reprovadas",
            help="Disciplinas que constam como 'Em Andamento' no seu histórico."
        )
        
        if reprovadas_simuladas:
            semestres_original = len([p for p in planejamento_original if p['disciplinas']])
            diferenca = semestres_necessarios - semestres_original
            
            st.markdown("<br>", unsafe_allow_html=True)
            m1, m2, m3 = st.columns(3)
            
            m1.metric("Planejamento ORIGINAL", f"{semestres_original} semestres")
            m2.metric("Planejamento SIMULADO", f"{semestres_necessarios} semestres")
            
            if diferenca > 0:
                m3.metric("Diferença Estimada", f"+{diferenca} semestre(s)", delta=f"{diferenca} atraso", delta_color="inverse")
                st.error(f"A reprovação nestas disciplinas vai atrasar a sua formatura em **{diferenca} semestre(s)**. Verifique as abas de Matriz e Grafo para visualizar o impacto.", icon=":material/warning:")
            else:
                m3.metric("Diferença Estimada", "Sem impacto", delta="0", delta_color="normal")
                st.success("Segundo a simulação matemática, estas reprovações não alteram o seu semestre final de conclusão (existe folga na grade).", icon=":material/check_circle:")
            
            st.markdown("#### Cadeias de Dependência Bloqueadas")
            for cod, info in bloqueios.items():
                if info["bloqueia"]:
                    lista_bloqueios = ", ".join(info["bloqueia"])
                    st.warning(f"**{info['nome']}** ({cod}) → Trancou as seguintes inscrições: {lista_bloqueios}")
                else:
                    st.info(f"**{info['nome']}** ({cod}) → Isolada (Não possui dependentes diretos).")
        else:
            st.info("Nenhuma simulação ativa. O sistema está a espelhar a sua matriz real.")