import streamlit as st
import os
import pandas as pd
from controllers.pedido_controller import PedidoController
from views.pedido_view import PedidoView
from views.pedido_historico_view import PedidoHistoricoView
from views.pedido_form_view import PedidoFormView, CacheManager
from views.configuracoes_view import ConfiguracoesView
from views.pedido_dashboard_gerencial import mostrar_dashboard_gerencial
from pathlib import Path

# Caminho do arquivo local correto (usando Path para garantir o caminho correto)
DIRETORIO_BASE = os.path.dirname(os.path.abspath(__file__))
PLANILHA_LOCAL = os.path.join(DIRETORIO_BASE, 'pedidos', 'Versão de Linha YMS_Motor XBB.xlsx')

# Verificar se o arquivo existe e criar mensagem de erro apropriada
if not os.path.exists(PLANILHA_LOCAL):
    st.error(f"""
    ❌ Arquivo de planilha não encontrado!
    
    O sistema está procurando o arquivo em:
    {PLANILHA_LOCAL}
    
    Por favor, verifique se:
    1. O arquivo existe na pasta 'pedidos' do projeto
    2. O nome do arquivo está correto: 'Versão de Linha YMS_Motor XBB.xlsx'
    3. Você tem permissão para acessar o arquivo
    """)
    st.stop()

# Configurar página Streamlit
st.set_page_config(
    page_title="Sistema de Pedidos - Paco",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Forçar tema claro e ajustar layout
st.markdown(
    '''
    <style>
    body, [data-testid="stAppViewContainer"], [data-testid="stSidebar"] {
        background-color: #fff !important;
        color: #222 !important;
    }
    
    /* Layout responsivo */
    .stApp {
        max-width: 100% !important;
    }
    
    [data-testid="stSidebarContent"] {
        min-width: 250px !important;
    }
    
    /* Ajuste para conteúdo principal */
    .main .block-container {
        max-width: 100% !important;
        padding: 2rem 3rem !important;
    }
    
    /* Cards e containers */
    .stSelectbox, .stTextInput, .stTextArea {
        max-width: 100% !important;
    }
    
    /* Tabelas responsivas */
    .dataframe {
        width: 100% !important;
        overflow-x: auto !important;
    }
    
    /* Elementos de formulário */
    div[data-testid="column"] {
        padding: 0.5rem !important;
    }
    
    /* Ajustes para telas menores */
    @media screen and (max-width: 768px) {
        .main .block-container {
            padding: 1rem !important;
        }
    }
    </style>
    ''',
    unsafe_allow_html=True
)

# CSS personalizado

# CSS para remover completamente o cabeçalho do Streamlit
custom_css = """
    <style>
        /* Remove completamente o cabeçalho da aplicação Streamlit 
        header.stAppHeader {
            display: none !important;
            z-index: none !important;
        }*/
    </style>
"""

st.markdown(custom_css, unsafe_allow_html=True)

def estilizar_sidebar():    st.sidebar.markdown("""
    <style>
        [data-testid="stSidebar"] {
            background-color: #f8f9fa;
            padding: 2rem 1rem;
        }
        .sidebar-menu {
            margin-bottom: 2rem;
            text-align: center;
        }
        .sidebar-title {
            font-size: 1.5rem;
            font-weight: bold;
            margin-bottom: 2rem;
            text-align: center;
            color: #1f2937;
        }
        /* Estilo para os botões */
        .stButton button {
            width: 100% !important;
            margin: 0.5rem 0 !important;
            padding: 0.75rem !important;
            border: 1px solid #e5e7eb !important;
            background-color: white !important;
            color: #1f2937 !important;
            font-size: 1rem !important;
            font-weight: 500 !important;
            border-radius: 0.5rem !important;
            transition: all 0.2s ease !important;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05) !important;
        }
        .stButton button:hover {
            background-color: #f3f4f6 !important;
            border-color: #d1d5db !important;
            transform: translateY(-1px) !important;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05) !important;
        }
        .stButton button:active {
            transform: translateY(0) !important;
        }
        /* Botão selecionado/ativo */
        .stButton button[data-selected="true"] {
            background-color: #f3f4f6 !important;
            border-color: #2563eb !important;
            color: #2563eb !important;
        }
        /* Remove o espaço extra entre markdown */
        .sidebar-menu div.stMarkdown {
            margin: 0 !important;
            padding: 0 !important;
        }
        /* Ajuste para espaçamento entre botões */
        .sidebar-menu > div {
            margin-bottom: 0.5rem !important;
        }
    </style>
    """, unsafe_allow_html=True)

def main():
    try:
        # Estilizar sidebar
        estilizar_sidebar()
        
        # Título no sidebar
        st.sidebar.markdown('<div class="sidebar-title">Yazaki<br>Sistema de Requisição</div>', unsafe_allow_html=True)
        
        # Menu com botões separados
        st.sidebar.markdown('<div class="sidebar-menu">', unsafe_allow_html=True)
        
        # Inicializar o estado do menu se não existir
        if 'menu_atual' not in st.session_state:
            # st.session_state.menu_atual = "📝 Novo Pedido"
            st.session_state.menu_atual = "📋 Histórico"
            
        # Inicializar outras variáveis de estado necessárias
        if 'last_code' not in st.session_state:
            st.session_state.last_code = None
        if 'scan_log' not in st.session_state:
            st.session_state.scan_log = []
        if 'posto_selecionado' not in st.session_state:
            st.session_state.posto_selecionado = None
        if 'coordenada_selecionada' not in st.session_state:
            st.session_state.coordenada_selecionada = None
        
        # Botões de navegação
        # if st.sidebar.button("📄 Novo Pedido", use_container_width=True):
        #     st.session_state.menu_atual = "📝 Novo Pedido"
        #     st.rerun()
        
        if st.sidebar.button("📋 Pedidos", use_container_width=True):
            st.session_state.menu_atual = "📋 Histórico"
            st.rerun()
        
        if st.sidebar.button("⚙️ Configurações", use_container_width=True):
            st.session_state.menu_atual = "⚙️ Configurações"
            st.rerun()
        
        st.sidebar.markdown('</div>', unsafe_allow_html=True)
        
        # Informações úteis no sidebar
        # with st.sidebar:
        #     st.markdown("---")
        #     st.markdown("### ℹ️ Informações")
        #     st.markdown("""
        #     # - 📝 **Novo Pedido**: Criar requisição
        #     - 📋 **Histórico**: Ver/Imprimir pedidos
        #     """)
            
        #     st.markdown("---")
        #     st.markdown("### 🔍 Ajuda Rápida")
        #     with st.expander("Como imprimir um pedido?"):
        #         st.markdown("""
        #         1. Vá para "Ver Histórico"
        #         2. Encontre o pedido desejado
        #         3. Clique em "🖨️ Imprimir"
        #         """)
            
        #     with st.expander("Como criar um pedido?"):
        #         st.markdown("""
        #         1. Selecione "Criar Novo Pedido"
        #         2. Escolha o cliente
        #         3. Selecione o RACK
        #         4. Escolha a localização
        #         5. Preencha os dados
        #         """)
        # Inicializar controlador com o arquivo local correto e Google Sheets habilitado
        pedido_controller = PedidoController(PLANILHA_LOCAL, enable_sheets=True)
        # Inicializar views
        pedido_form_view = PedidoFormView(pedido_controller)
        historico_view = PedidoHistoricoView(pedido_controller)
        configuracoes_view = ConfiguracoesView(pedido_controller)
        # Mostrar interface baseado na seleção do menu
        # if "Novo Pedido" in st.session_state.menu_atual:
        #     pedido_form_view.mostrar_interface()
        if "Histórico" in st.session_state.menu_atual:
            st.markdown("## Resumo Pedidos")
            mostrar_dashboard_gerencial(pedido_controller)
            historico_view.mostrar_interface()
        else:
            configuracoes_view.mostrar_interface()
        
    except Exception as e:
        # Mensagem de erro clara para planilha de mapeamento e Google Sheets
        st.error(f"""
        ❌ Erro ao inicializar o sistema
        Verifique se o arquivo local existe: {PLANILHA_LOCAL}
        Detalhes: {str(e)}
        """)

if __name__ == "__main__":
    main()
