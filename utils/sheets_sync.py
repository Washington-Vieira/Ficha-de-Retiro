import os
import json
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
import streamlit as st
from datetime import datetime

class SheetsPedidosSync:
    def __init__(self):
        self.config_file = "config.json"
        self.SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
        self.SPREADSHEET_ID = '13iIYn9cPLfYZHn3BIgfUEHd4rS2j2_e6QyCIY8uwRqQ'
        self.load_config()

    def load_config(self):
        """Carrega ou cria configuração padrão"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
                # Adiciona a chave sheets_credentials se não existir
                if 'sheets_credentials' not in self.config:
                    self.config['sheets_credentials'] = None
                    self.save_config()
        else:
            self.config = {
                'local_mapeamento': 'pedidos/Mapeamento de Racks - Cabos.xlsx',
                'sheets_credentials': None
            }
            self.save_config()

    def save_config(self):
        """Salva configuração atual"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=4)

    def _get_service(self):
        """Cria serviço autenticado do Google Sheets"""
        try:
            if not self.config.get('credentials'):
                return None

            credentials = service_account.Credentials.from_service_account_info(
                self.config['credentials'],
                scopes=self.SCOPES
            )
            
            return build('sheets', 'v4', credentials=credentials)
        except Exception as e:
            st.error(f"Erro ao criar serviço do Google Sheets: {str(e)}")
            return None

    def sync_files(self):
        """Sincroniza arquivos com Google Sheets"""
        try:
            service = self._get_service()
            if not service:
                return False, "Credenciais do Google Sheets não configuradas. Configure nas configurações."

            # Ler arquivos locais
            mapeamento_df = pd.read_excel(self.config['local_mapeamento'])

            # Converter DataFrame para lista para API do Google Sheets
            mapeamento_values = [mapeamento_df.columns.values.tolist()] + mapeamento_df.values.tolist()

            # Atualizar planilha
            batch_update = service.spreadsheets().values().batchUpdate(
                spreadsheetId=self.SPREADSHEET_ID,
                body={
                    'valueInputOption': 'USER_ENTERED',
                    'data': [
                        {
                            'range': 'Mapeamento!A1',
                            'values': mapeamento_values
                        }
                    ]
                }
            ).execute()

            return True, "Sincronização com Google Sheets concluída com sucesso!"

        except Exception as e:
            error_msg = f"Erro na sincronização: {str(e)}"
            st.error(error_msg)
            return False, error_msg

    def render_config_page(self):
        """Renderiza página de configuração"""
        st.title("⚙️ Configuração de Sincronização")

        # Configuração das Credenciais do Google Sheets
        st.markdown("### Credenciais do Google Sheets")
        
        # Mostrar status atual das credenciais
        if self.config.get('credentials'):
            st.success("✅ Credenciais do Google Sheets estão configuradas")
            if st.button("🔄 Alterar Credenciais"):
                self.config['credentials'] = None
                self.save_config()
                st.rerun()
        else:
            st.warning("⚠️ Credenciais do Google Sheets não estão configuradas")
            st.markdown("""
            Para configurar as credenciais:
            1. Acesse o [Google Cloud Console](https://console.cloud.google.com)
            2. Crie um projeto (ou selecione um existente)
            3. Habilite a API do Google Sheets
            4. Crie uma conta de serviço e baixe o arquivo JSON de credenciais
            """)
            
            credentials_json = st.text_area(
                "Cole o conteúdo do arquivo JSON de credenciais aqui",
                help="Conteúdo do arquivo de credenciais da conta de serviço"
            )
            
            if st.button("💾 Salvar Credenciais") and credentials_json:
                try:
                    self.config['credentials'] = json.loads(credentials_json)
                    self.save_config()
                    st.success("✅ Credenciais salvas com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar credenciais: {str(e)}")

        st.markdown("### Configurações Locais")
        local_map = st.text_input(
            "Caminho do Arquivo de Mapeamento",
            value=self.config['local_mapeamento']
        )

        if st.button("💾 Salvar Configurações"):
            self.config.update({
                'local_mapeamento': local_map
            })
            self.save_config()
            st.success("✅ Configurações salvas com sucesso!")

        if st.button("🔄 Sincronizar Agora"):
            success, message = self.sync_files()
            if success:
                st.success(message)
            else:
                st.error(message)
