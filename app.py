import streamlit as st
import streamlit.components.v1 as components
import os

from modulos.extrator_pdf import extrair_dados_historico
from grafos.construtor import construir_grafo_aluno
from grafos.algoritmo_dfs import gerar_planejamento_dfs
from grafos.algoritmo_cores import gerar_planejamento_coloracao
from grafos.visualizador import gerar_visualizacao_grafo

# ==========================================
# Configuração da Página e CSS
# ==========================================
st.set_page_config(page_title="Vertex | Otimizador Curricular", layout="wide", initial_sidebar_state="expanded")

def carregar_css():
    diretorio_atual = os.path.dirname(os.path.abspath(__file__))
    caminho_css = os.path.join(diretorio_atual, 'assets', 'style.css')
    
    if os.path.exists(camincss := caminho_css):
        with open(camincss) as f:
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

# ==========================================
# Menu Lateral (Sidebar Profissional)
# ==========================================
with st.sidebar:
    # Identidade Visual do Sistema (Logo Tipográfica)
    st.markdown("""
    <div style="margin-bottom: 2.5rem; padding-bottom: 1.5rem; border-bottom: 1px solid #E5E7EB;">
        <h1 style="color: #FF6B35; font-size: 2.8rem; font-weight: 900; letter-spacing: -1.5px; margin: 0; line-height: 1;">VERTEX</h1>
        <p style="color: #6B7280; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1.2px; margin: 8px 0 0 0;">Otimizador Curricular Avançado</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<p style='font-weight: 700; font-size: 0.8rem; color: #374151; text-transform: uppercase; margin-bottom: 5px; letter-spacing: 0.5px;'>Anexar Histórico do SIGAA</p>", unsafe_allow_html=True)
    arquivo_historico = st.file_uploader("Upload de Histórico", type=["pdf"], label_visibility="collapsed")
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<p style='font-weight: 700; font-size: 0.8rem; color: #374151; text-transform: uppercase; margin-bottom: 5px; letter-spacing: 0.5px;'>Parâmetros de Otimização</p>", unsafe_allow_html=True)
    
    max_disciplinas = st.slider("Cadeiras por período letivo", min_value=4, max_value=8, value=6)
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
if not gerar:
    st.header("Painel de Planejamento Integrado")
    st.markdown("Universidade do Estado do Rio Grande do Norte (UERN) | Ciência da Computação")
    st.info("Utilize o menu lateral para anexar o documento em PDF e iniciar a configuração de matrizes.", icon=":material/arrow_back:")

else:
    if arquivo_historico is None:
        st.warning("Nenhum documento detectado. Anexe o histórico para continuar.", icon=":material/warning:")
    else:
        with st.spinner('Construindo malha de grafos e resolvendo dependências matemáticas...'):
            
            perfil, aprovadas, cursando = extrair_dados_historico(arquivo_historico)
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
            
            st.markdown("<p style='font-size: 0.85rem; text-transform: uppercase; color: #6B7280; font-weight: 700; letter-spacing: 1px; margin-bottom: -15px;'>Perfil Acadêmico</p>", unsafe_allow_html=True)
            
            nome_formatado = formatar_nome(perfil["nome"])
            st.markdown(f"<h1 style='color: #FF6B35; font-size: 3.2rem; font-weight: 900; letter-spacing: -1.5px; margin-bottom: 25px;'>{nome_formatado}</h1>", unsafe_allow_html=True)
            
            col_p1, col_p2, col_p3 = st.columns(3)
            col_p1.metric(label="Matrícula", value=perfil["matricula"])
            col_p2.metric(label="Índice de Rendimento (IRA)", value=perfil["ira"])
            col_p3.metric(label="Projeção de conclusão", value=f"{len([p for p in planejamento if p['disciplinas']])} Semestres")
            
            st.write("") 
            
            with st.expander("Registro de Componentes Lidos do SIGAA", expanded=False):
                st.write(f"**Validados ({len(aprovadas)}):** {', '.join(aprovadas) if aprovadas else 'Nenhum'}")
                st.write(f"**Em Andamento ({len(cursando)}):** {', '.join(cursando) if cursando else 'Nenhum'}")
            
            st.markdown("---")
            
            st.markdown(f"### Matriz de Integralização Projetada")
            
            # Divisão do conteúdo em Abas de visualização
            aba_lista, aba_grafo = st.tabs(["Matriz Projetada (Estrutural)", "Mapa de Dependências (Grafo)"])
            
            with aba_lista:
                st.markdown("<br>", unsafe_allow_html=True)
                for periodo in planejamento:
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
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("""
                <div style="display: flex; gap: 15px; margin-bottom: 15px;">
                    <span style="color: #10B981; font-weight: bold;">■ Integralizado</span>
                    <span style="color: #F59E0B; font-weight: bold;">■ Em Andamento</span>
                    <span style="color: #9CA3AF; font-weight: bold;">■ Pendente</span>
                </div>
                """, unsafe_allow_html=True)
                
                # Gera o arquivo HTML com o mapa de grafos
                net = gerar_visualizacao_grafo(dados_grade, aprovadas, cursando)
                
                # Salva e lê o arquivo localmente
                arquivo_html = "grafo_curricular.html"
                net.save_graph(arquivo_html)
                
                with open(arquivo_html, 'r', encoding='utf-8') as f:
                    codigo_html = f.read()
                    
                # Injeta a visualização na tela do Streamlit
                components.html(codigo_html, height=620, scrolling=False)