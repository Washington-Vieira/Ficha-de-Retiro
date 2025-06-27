import streamlit as st
import os
from datetime import datetime
import platform
from utils.sheets_pedidos_sync import SheetsPedidosSync
import json
import subprocess

class ConfiguracoesView:
    def __init__(self, pedido_controller):
        self.controller = pedido_controller
        self.sheets_sync = self.controller.sheets_sync if hasattr(self.controller, 'sheets_sync') else None

        self.base_dir = os.path.join(
            os.path.expanduser("~"),
            "OneDrive - Yazaki",
            "Solicitação",
            "Pedidos"
        )
        self.arquivo_backup = os.path.join(self.base_dir, "backup")
        self.config_path = os.path.join(os.path.dirname(__file__), '..', 'config.json')
        self.config = self._carregar_config()

    def _carregar_config(self):
        """Carrega as configurações do arquivo"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            return {}
        except:
            return {}

    def _salvar_config(self):
        """Salva as configurações no arquivo"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=4)
            return True
        except:
            return False

    def _listar_impressoras(self):
        """Lista todas as impressoras disponíveis no sistema"""
        try:
            if platform.system() == 'Windows':
                # Windows: usar wmic
                try:
                    output = subprocess.check_output('wmic printer get name', shell=True, universal_newlines=True)
                    impressoras = [linha.strip() for linha in output.split('\n')[1:] if linha.strip()]
                    return ['PDF Virtual'] + impressoras  # Adiciona opção de PDF
                except:
                    return ['PDF Virtual']
            else:
                # Linux/Mac: usar lpstat
                try:
                    output = subprocess.check_output(['lpstat', '-p'], universal_newlines=True)
                    impressoras = []
                    for line in output.split('\n'):
                        if line.startswith('printer'):
                            impressoras.append(line.split(' ')[1])
                    return ['PDF Virtual'] + impressoras  # Adiciona opção de PDF
                except:
                    return ['PDF Virtual']
        except:
            return ['PDF Virtual']

    def _inicializar_planilha(self):
        """Inicializa a estrutura da planilha com todas as colunas necessárias"""
        if not self.sheets_sync or not self.sheets_sync.client:
            st.error("Configuração do Google Sheets necessária!")
            return False

        try:
            sheet = self.sheets_sync.client.open_by_url(self.sheets_sync.SPREADSHEET_URL)
            
            # Colunas necessárias para a aba Pedidos
            colunas_pedidos = [
                "Numero_Pedido", "Data", "Serial", "Maquina", "Posto", "Coordenada",
                "Modelo", "OT", "Semiacabado", "Pagoda", "Status", "Urgente",
                "Ultima_Atualizacao", "Responsavel_Atualizacao",
                "Responsavel_Separacao", "Data_Separacao",
                "Responsavel_Coleta", "Data_Coleta"
            ]

            # Verificar/criar aba Pedidos
            try:
                ws_pedidos = sheet.worksheet("Pedidos")
            except:
                ws_pedidos = sheet.add_worksheet("Pedidos", 1000, len(colunas_pedidos))
            
            # Atualizar cabeçalhos
            headers = ws_pedidos.row_values(1)
            if not headers or len(headers) < len(colunas_pedidos):
                ws_pedidos.update('A1', [colunas_pedidos])
                st.success("Estrutura da planilha atualizada com sucesso!")
            return True

        except Exception as e:
            st.error(f"Erro ao inicializar planilha: {str(e)}")
            return False

    def mostrar_interface(self):
        st.markdown("### ⚙️ Configurações do Sistema", unsafe_allow_html=True)
        
        # Proteção por senha
        if 'config_senha_ok' not in st.session_state:
            st.session_state['config_senha_ok'] = False
        if not st.session_state['config_senha_ok']:
            senha = st.text_input("Digite a senha para acessar as configurações:", type="password")
            if st.button("Acessar Configurações"):
                if senha == "pyh#1874":
                    st.session_state['config_senha_ok'] = True
                    st.rerun()
                else:
                    st.error("Senha incorreta! Tente novamente.")
            return
        
        # Tabs para diferentes configurações
        tab1, tab2, tab3, tab4 = st.tabs(["Sistema", "Google Sheets", "Impressão", "Backups"])
        
        with tab1:
            self._mostrar_info_sistema()
            
        with tab2:
            if self.sheets_sync is None:
                from utils.sheets_pedidos_sync import SheetsPedidosSync
                self.sheets_sync = SheetsPedidosSync(enable_sheets=True)
            self._mostrar_config_sheets()
            
        with tab3:
            self._mostrar_config_impressao()
            
        with tab4:
            self._mostrar_backups()

    def _mostrar_info_sistema(self):
        # Informações do Sistema
        st.markdown("#### 💻 Informações do Sistema")
        st.markdown(f"""
        - **Sistema Operacional:** {platform.system()}
        - **Versão Python:** {platform.python_version()}
        - **Ambiente:** {"Streamlit Cloud" if os.getenv('IS_STREAMLIT_CLOUD', '0') == '1' else "Local"}
        """)
        
        st.markdown("---")
        

    def _mostrar_config_sheets(self):
        self.sheets_sync.render_config_page()

    def _mostrar_backups(self):
        # Mostrar backups disponíveis
        st.markdown("#### 💾 Backups Disponíveis")
        
        if not os.path.exists(self.arquivo_backup):
            os.makedirs(self.arquivo_backup, exist_ok=True)
            
        backups = sorted([
            f for f in os.listdir(self.arquivo_backup)
            if f.endswith('.xlsx')
        ], reverse=True)
        
        if not backups:
            st.info("Nenhum backup encontrado")
        else:
            for backup in backups:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.text(backup)
                with col2:
                    if st.button("📥 Restaurar", key=f"restore_{backup}"):
                        try:
                            # Restaurar backup                            backup_path = os.path.join(self.arquivo_backup, backup)
                            os.replace(backup_path, self.arquivo_pedidos)
                            st.success("Backup restaurado com sucesso!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao restaurar backup: {str(e)}")
        
        # Informações sobre backups
        st.markdown("#### ℹ️ Informações")
        st.markdown("""
        - O sistema mantém automaticamente os últimos 10 backups
        - Um novo backup é criado sempre que há alterações nos pedidos
        - Os backups são nomeados com data e hora para fácil identificação
        - Use o botão "Restaurar" para voltar a uma versão anterior dos dados
        """)
        
        # Aviso importante
        st.warning("""
        **⚠️ Atenção!**  
        Ao restaurar um backup, a versão atual dos dados será substituída.
        Certifique-se de que deseja realmente fazer isso antes de prosseguir.
        """)

    def _mostrar_config_impressao(self):
        st.markdown("#### 🖨️ Configurações de Impressão")
        
        # Lista de impressoras disponíveis
        impressoras = self._listar_impressoras()
        impressora_atual = self.config.get('impressora_padrao', impressoras[0] if impressoras else '')
        
        impressora_selecionada = st.selectbox(
            "Selecione a impressora padrão:",
            options=impressoras,
            index=impressoras.index(impressora_atual) if impressora_atual in impressoras else 0,
            help="Selecione 'PDF Virtual' para gerar PDFs em vez de imprimir diretamente"
        )

        # Se selecionou PDF Virtual, mostra campo para diretório
        if impressora_selecionada == 'PDF Virtual':
            diretorio_pdf = self.config.get('diretorio_pdf', os.path.expanduser('~'))
            
            col1, col2 = st.columns([3, 1])
            with col1:
                novo_diretorio = st.text_input(
                    "Diretório para salvar PDFs:",
                    value=diretorio_pdf,
                    help="Digite o caminho completo do diretório onde deseja salvar os PDFs"
                )
            with col2:
                if st.button("📁 Explorar"):
                    # Abrir explorador de arquivos no diretório atual
                    try:
                        if platform.system() == 'Windows':
                            os.startfile(diretorio_pdf)
                        else:
                            subprocess.run(['xdg-open', diretorio_pdf])
                    except:
                        st.error("Não foi possível abrir o explorador de arquivos")
            
            # Validar e criar diretório se não existir
            if novo_diretorio and novo_diretorio != diretorio_pdf:
                try:
                    os.makedirs(novo_diretorio, exist_ok=True)
                    self.config['diretorio_pdf'] = novo_diretorio
                except Exception as e:
                    st.error(f"Erro ao configurar diretório: {str(e)}")

        # Botão para salvar configurações
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("💾 Salvar Configurações"):
                self.config['impressora_padrao'] = impressora_selecionada
                if self._salvar_config():
                    st.success("✅ Configurações salvas com sucesso!")
                else:
                    st.error("❌ Erro ao salvar configurações")

        # Informações adicionais
        st.markdown("---")
        st.markdown("##### ℹ️ Informações")
        if impressora_selecionada == 'PDF Virtual':
            st.info("""
            Com a impressora 'PDF Virtual' selecionada:
            - Os arquivos serão salvos automaticamente no diretório configurado
            - O nome do arquivo será gerado automaticamente com data e hora
            - Você pode acessar os PDFs gerados clicando no botão 'Explorar'
            """)
        else:
            st.info("""
            Com uma impressora física selecionada:
            - As etiquetas serão enviadas diretamente para impressão
            - O tamanho será ajustado automaticamente para 60x30mm
            - Certifique-se que a impressora está configurada corretamente
            """)