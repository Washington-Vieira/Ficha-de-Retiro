import os
import json
import pandas as pd
try:
    import streamlit as st
except ImportError:
    st = None
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import re

class SheetsPedidosSync:
    def __init__(self, enable_sheets=True, config_file="config.json"):
        self.config_file = config_file
        self.SPREADSHEET_URL = None
        self.client = None
        self.enable_sheets = enable_sheets
        self.load_config()
        if self.enable_sheets:
            self.initialize_client()

    def load_config(self):
        """Carrega as credenciais do Google Sheets"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
                    # Só sobrescreve se não veio do secrets
                    if not self.SPREADSHEET_URL:
                        self.SPREADSHEET_URL = self.config.get('sheets_url', '')
            else:
                self.config = {
                    'sheets_credentials': None,
                    'sheets_url': ''
                }
                if not self.SPREADSHEET_URL:
                    self.SPREADSHEET_URL = self.config['sheets_url']
                self.save_config()
        except Exception as e:
            if st:
                st.error(f"Erro ao carregar configurações: {str(e)}")
            else:
                print(f"Erro ao carregar configurações: {str(e)}")
            self.config = {'sheets_credentials': None}
            if not self.SPREADSHEET_URL:
                self.SPREADSHEET_URL = ''

    def save_config(self):
        """Salva configuração atual"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            if st:
                st.error(f"Erro ao salvar configurações: {str(e)}")
            else:
                print(f"Erro ao salvar configurações: {str(e)}")

    def initialize_client(self):
        """Inicializa o cliente do Google Sheets"""
        try:
            # Usar apenas as credenciais do config.json
            creds = self.config.get('sheets_credentials')
            
            if creds:
                if not creds.get('client_email'):
                    if st:
                        st.warning('Credenciais do Google Sheets inválidas: falta o campo "client_email".')
                    self.client = None
                    return
                self.client = gspread.authorize(ServiceAccountCredentials.from_json_keyfile_dict(
                    creds,
                    scopes=['https://spreadsheets.google.com/feeds', 
                           'https://www.googleapis.com/auth/drive']
                ))
                # Testar conexão
                try:
                    self.client.open_by_url(self.SPREADSHEET_URL)
                except Exception as e:
                    if st:
                        st.warning(f"Erro ao acessar planilha: {str(e)}")
                    else:
                        print(f"Erro ao acessar planilha: {str(e)}")
                    self.client = None
            else:
                if st:
                    st.error('Credenciais do Google Sheets não encontradas no config.json.')
                else:
                    print('Credenciais do Google Sheets não encontradas no config.json.')
                self.client = None
        except Exception as e:
            if st:
                st.error(f"Erro ao inicializar cliente do Google Sheets: {str(e)}")
            else:
                print(f"Erro ao inicializar cliente do Google Sheets: {str(e)}")
            self.client = None

    def _get_or_create_worksheet(self, sheet, name, rows=100, cols=20):
        """Obtém ou cria uma aba na planilha"""
        try:
            return sheet.worksheet(name)
        except gspread.exceptions.WorksheetNotFound:
            return sheet.add_worksheet(title=name, rows=rows, cols=cols)

    def salvar_pedido_completo(self, df_pedidos: pd.DataFrame, df_itens: pd.DataFrame) -> tuple[bool, str]:
        """Salva pedidos e itens em abas separadas no Google Sheets"""
        try:
            if not self.client:
                raise ValueError("Cliente do Google Sheets não configurado. Verifique as credenciais.")

            if not self.SPREADSHEET_URL:
                raise ValueError("URL da planilha não configurada.")

            # Abrir a planilha pelo URL
            try:
                sheet = self.client.open_by_url(self.SPREADSHEET_URL)
            except Exception as e:
                raise ValueError(f"Erro ao abrir planilha: {str(e)}")

            # Padronizar cabeçalho da aba Pedidos
            pedidos_padrao = [
                "Numero_Pedido", "Data", "Serial", "Maquina", "Posto", "Coordenada", "Modelo", "OT", "Semiacabado", "Pagoda", "Status", "Urgente", "Ultima_Atualizacao", "Responsavel_Atualizacao", "Responsavel_Separacao", "Data_Separacao", "Responsavel_Coleta", "Data_Coleta", "Solicitante", "Observacoes"
            ]
            worksheet_pedidos = self._get_or_create_worksheet(sheet, "Pedidos")
            headers = worksheet_pedidos.row_values(1)
            if headers != pedidos_padrao:
                worksheet_pedidos.update('A1', [pedidos_padrao])

            # Preparar os dados dos pedidos
            df_pedidos = df_pedidos.fillna("")
            pedidos_values = [df_pedidos.columns.tolist()] + df_pedidos.values.tolist()
            pedidos_values = [[str(cell) if pd.notna(cell) else "" for cell in row] for row in pedidos_values]

            # Preparar os dados dos itens
            df_itens = df_itens.fillna("")
            itens_values = [df_itens.columns.tolist()] + df_itens.values.tolist()
            itens_values = [[str(cell) if pd.notna(cell) else "" for cell in row] for row in itens_values]

            # Atualizar aba de Pedidos (APENAS ADICIONAR, NÃO LIMPAR)
            existing_rows_pedidos = worksheet_pedidos.get_all_values()
            if existing_rows_pedidos:
                # Se já existe cabeçalho, não adicionar de novo
                pedidos_to_append = pedidos_values[1:]
            else:
                # Se está vazio, adicionar tudo (incluindo cabeçalho)
                pedidos_to_append = pedidos_values
            if pedidos_to_append:
                worksheet_pedidos.append_rows(pedidos_to_append, value_input_option="USER_ENTERED")

            # Atualizar aba de Itens (APENAS ADICIONAR, NÃO LIMPAR)
            worksheet_itens = self._get_or_create_worksheet(sheet, "Itens")
            existing_rows = worksheet_itens.get_all_values()
            if existing_rows:
                itens_to_append = itens_values[1:]
            else:
                itens_to_append = itens_values
            if itens_to_append:
                worksheet_itens.append_rows(itens_to_append, value_input_option="USER_ENTERED")

            # Formatar as abas
            self._format_worksheets(sheet)

            return True, "Pedido salvo com sucesso no Google Sheets!"
        except Exception as e:
            return False, f"Erro ao salvar no Google Sheets: {str(e)}"

    def _format_worksheets(self, sheet):
        """Aplica formatação básica nas abas"""
        try:
            # Formatar aba de Pedidos
            ws_pedidos = sheet.worksheet("Pedidos")
            ws_pedidos.format('A1:Z1', {
                "backgroundColor": {"red": 0.8, "green": 0.8, "blue": 0.8},
                "horizontalAlignment": "CENTER",
                "textFormat": {"bold": True}
            })
            ws_pedidos.freeze(rows=1)

            # Formatar aba de Itens
            ws_itens = sheet.worksheet("Itens")
            ws_itens.format('A1:Z1', {
                "backgroundColor": {"red": 0.8, "green": 0.8, "blue": 0.8},
                "horizontalAlignment": "CENTER",
                "textFormat": {"bold": True}
            })
            ws_itens.freeze(rows=1)
        except Exception as e:
            if st:
                st.warning(f"Aviso: Não foi possível aplicar a formatação: {str(e)}")
            else:
                print(f"Aviso: Não foi possível aplicar a formatação: {str(e)}")

    def sincronizar_mapeamento(self, arquivo_mapeamento: str) -> tuple[bool, str]:
        """Sincroniza o arquivo de mapeamento com o Google Sheets"""
        try:
            if not self.client:
                raise ValueError("Cliente do Google Sheets não configurado. Verifique as credenciais.")

            if not self.SPREADSHEET_URL:
                raise ValueError("URL da planilha não configurada.")

            # Ler o arquivo de mapeamento
            try:
                df = pd.read_excel(
                    arquivo_mapeamento,
                    sheet_name='Projeto',
                    dtype={
                        'RACK': str,
                        'CÓD Yazaki': str,
                        'Codigo Cabo': str,
                        'Secção': str,
                        'Cor': str,
                        'Cliente': str,
                        'Locação': str,
                        'Projeto': str,
                        'Cod OES': str
                    }
                )
            except Exception as e:
                raise ValueError(f"Erro ao ler arquivo de mapeamento: {str(e)}")

            # Abrir a planilha do Google Sheets
            try:
                sheet = self.client.open_by_url(self.SPREADSHEET_URL)
            except Exception as e:
                raise ValueError(f"Erro ao abrir planilha: {str(e)}")

            # Preparar os dados
            df = df.fillna("")
            values = [df.columns.tolist()] + df.values.tolist()
            values = [[str(cell) if pd.notna(cell) else "" for cell in row] for row in values]

            # Atualizar ou criar a aba Projeto
            worksheet = self._get_or_create_worksheet(sheet, "Projeto", rows=len(values)+100, cols=len(values[0])+5)
            worksheet.clear()
            worksheet.append_rows(values, value_input_option="USER_ENTERED")

            # Formatar a aba
            worksheet.format('A1:Z1', {
                "backgroundColor": {"red": 0.8, "green": 0.8, "blue": 0.8},
                "horizontalAlignment": "CENTER",
                "textFormat": {"bold": True}
            })
            worksheet.freeze(rows=1)

            return True, "Mapeamento sincronizado com sucesso!"
        except Exception as e:
            return False, f"Erro ao sincronizar mapeamento: {str(e)}"

    def sincronizar_paco(self, arquivo_local: str) -> tuple[bool, str]:
        """Sincroniza a planilha local para a aba 'paco' no Google Sheets"""
        try:
            if not self.client:
                raise ValueError("Cliente do Google Sheets não configurado. Verifique as credenciais.")
            if not self.SPREADSHEET_URL:
                raise ValueError("URL da planilha não configurada.")

            # Ler a planilha local
            try:
                df = pd.read_excel(arquivo_local)
            except Exception as e:
                raise ValueError(f"Erro ao ler arquivo local: {str(e)}")

            # Abrir a planilha do Google Sheets
            try:
                sheet = self.client.open_by_url(self.SPREADSHEET_URL)
            except Exception as e:
                raise ValueError(f"Erro ao abrir planilha: {str(e)}")

            # Preparar os dados
            df = df.fillna("")
            values = [df.columns.tolist()] + df.values.tolist()
            values = [[str(cell) if pd.notna(cell) else "" for cell in row] for row in values]

            # Atualizar ou criar a aba 'paco'
            worksheet = self._get_or_create_worksheet(sheet, "paco", rows=len(values)+100, cols=len(values[0])+5)
            worksheet.clear()
            worksheet.append_rows(values, value_input_option="USER_ENTERED")

            # Formatar a aba
            worksheet.format('A1:Z1', {
                "backgroundColor": {"red": 0.8, "green": 0.8, "blue": 0.8},
                "horizontalAlignment": "CENTER",
                "textFormat": {"bold": True}
            })
            worksheet.freeze(rows=1)

            return True, "Planilha local sincronizada com sucesso na aba 'paco'!"
        except Exception as e:
            return False, f"Erro ao sincronizar aba 'paco': {str(e)}"

    def sincronizar_layout(self, arquivo_local: str) -> tuple[bool, str]:
        """Sincroniza apenas o layout (colunas) do arquivo local para a aba 'layout' no Google Sheets"""
        try:
            if not self.client:
                raise ValueError("Cliente do Google Sheets não configurado. Verifique as credenciais.")
            if not self.SPREADSHEET_URL:
                raise ValueError("URL da planilha não configurada.")

            # Ler apenas o header do arquivo local
            try:
                df = pd.read_excel(arquivo_local, nrows=0)
            except Exception as e:
                raise ValueError(f"Erro ao ler arquivo local: {str(e)}")

            # Abrir a planilha do Google Sheets
            try:
                sheet = self.client.open_by_url(self.SPREADSHEET_URL)
            except Exception as e:
                raise ValueError(f"Erro ao abrir planilha: {str(e)}")

            # Preparar os dados (apenas header)
            values = [list(df.columns)]

            # Atualizar ou criar a aba 'layout'
            worksheet = self._get_or_create_worksheet(sheet, "layout", rows=10, cols=len(values[0])+5)
            worksheet.clear()
            worksheet.append_rows(values, value_input_option="USER_ENTERED")

            # Formatar a aba
            worksheet.format('A1:Z1', {
                "backgroundColor": {"red": 0.8, "green": 0.8, "blue": 0.8},
                "horizontalAlignment": "CENTER",
                "textFormat": {"bold": True}
            })
            worksheet.freeze(rows=1)

            return True, "Layout do arquivo local sincronizado com sucesso na aba 'layout'!"
        except Exception as e:
            return False, f"Erro ao sincronizar aba 'layout': {str(e)}"

    def render_config_page(self):
        """Renderiza página de configuração do Google Sheets"""
        st.title("")

        # URL da planilha
        st.markdown("### URL da Planilha")
        sheets_url = st.text_input(
            "URL da Planilha do Google Sheets",
            value=self.SPREADSHEET_URL or ""
        )
        if st.button("💾 Salvar URL") and sheets_url:
            self.config['sheets_url'] = sheets_url
            self.SPREADSHEET_URL = sheets_url
            self.save_config()
            st.success("✅ URL salva com sucesso!")
            st.rerun()

        # Status da conexão
        st.markdown("### Status da Conexão")
        if self.client:
            st.success("✅ Conectado ao Google Sheets")
            if st.button("🔄 Testar Conexão"):
                try:
                    self.client.open_by_url(self.SPREADSHEET_URL)
                    st.success("✅ Conexão testada com sucesso!")
                except Exception as e:
                    st.error(f"❌ Erro na conexão: {str(e)}")


            # Botão para importar arquivo Excel e atualizar aba 'paco'
            st.markdown("### Importar SCs atualizadas")
            arquivo_xlsx = st.file_uploader("Selecione o arquivo Excel para importar e atualizar aba 'paco'", type=["xlsx"], key="importar_atualizar_paco")
            if st.button("⬆️ Importar layout"):
                if arquivo_xlsx is not None:
                    temp_path = "temp_importar_atualizar_paco.xlsx"
                    with open(temp_path, "wb") as f:
                        f.write(arquivo_xlsx.read())
                    with st.spinner("Importando Layout"):
                        success, message = self.importar_e_atualizar_paco(temp_path)
                        if success:
                            st.success(message)
                        else:
                            st.error(message)
                else:
                    st.warning("Por favor, selecione um arquivo Excel antes de importar.")
        else:
            st.error("❌ Não conectado ao Google Sheets. Verifique as credenciais e a URL.")

    def get_pedido_detalhes(self, numero_pedido: str) -> dict:
        """Busca os detalhes de um pedido pelo número diretamente do Google Sheets."""
        try:
            if not self.client:
                st.warning("Por favor, recarregue a página e aguarde um minuto antes de tentar novamente.")
                return {}
            if not self.SPREADSHEET_URL:
                st.warning("Por favor, recarregue a página e aguarde um minuto antes de tentar novamente.")
                return {}
            
            sheet = self.client.open_by_url(self.SPREADSHEET_URL)
            ws_pedidos = sheet.worksheet("Pedidos")
            ws_itens = sheet.worksheet("Itens")
            
            # Buscar pedido na aba Pedidos
            pedidos_data = ws_pedidos.get_all_records()
            pedido = next((p for p in pedidos_data if p.get("Numero_Pedido") == numero_pedido), None)
            if not pedido:
                return {}
            
            # Buscar itens na aba Itens
            itens_data = ws_itens.get_all_records()
            itens = [item for item in itens_data if item.get("Numero_Pedido") == numero_pedido]
            
            # Converter pedido para dicionário
            info_dict = {
                "Numero_Pedido": pedido.get("Numero_Pedido", ""),
                "Data": pedido.get("Data", ""),
                "Cliente": pedido.get("Cliente", ""),
                "RACK": pedido.get("RACK", ""),
                "Localizacao": pedido.get("Localizacao", ""),
                "Solicitante": pedido.get("Solicitante", ""),
                "Observacoes": pedido.get("Observacoes", ""),
                "Ultima_Atualizacao": pedido.get("Ultima_Atualizacao", ""),
                "Responsavel_Atualizacao": pedido.get("Responsavel_Atualizacao", "")
            }
            
            return {
                "info": info_dict,
                "itens": itens,
                "status": pedido.get("Status", "")
            }
        except Exception as e:
            if "Quota exceeded" in str(e) or "[429]" in str(e):
                st.warning("Por favor, recarregue a página e aguarde um minuto antes de tentar novamente.")
            return {}

    def atualizar_status_pedido_sheets(self, numero_pedido: str, novo_status: str, ultima_atualizacao: str, responsavel: str, urgente_para_concluido_urgente: bool = False) -> tuple[bool, str]:
        """Atualiza o status de um pedido diretamente no Google Sheets."""
        try:
            if not self.client:
                return False, "Cliente do Google Sheets não configurado."
            if not self.SPREADSHEET_URL:
                return False, "URL da planilha não configurada."

            sheet = self.client.open_by_url(self.SPREADSHEET_URL)
            ws_pedidos = sheet.worksheet("Pedidos")

            # Encontrar a linha do pedido pelo Numero_Pedido (tolerante a espaços e case)
            numeros_pedidos_col = ws_pedidos.col_values(1)
            numero_pedido_norm = numero_pedido.strip().upper()
            col_norm = [str(x).strip().upper() for x in numeros_pedidos_col[1:]]
            try:
                row_index = col_norm.index(numero_pedido_norm) + 2
            except ValueError:
                return False, f"Pedido '{numero_pedido}' não encontrado na coluna 'Numero_Pedido' da aba Pedidos no Google Sheets."

            # Encontrar índices das colunas
            headers = ws_pedidos.row_values(1)
            try:
                status_col_index = headers.index("Status") + 1
                ultima_atualizacao_col_index = headers.index("Ultima_Atualizacao") + 1
                responsavel_atualizacao_col_index = headers.index("Responsavel_Atualizacao") + 1
                responsavel_separacao_col_index = headers.index("Responsavel_Separacao") + 1
                data_separacao_col_index = headers.index("Data_Separacao") + 1
                responsavel_coleta_col_index = headers.index("Responsavel_Coleta") + 1
                data_coleta_col_index = headers.index("Data_Coleta") + 1
                urgente_col_index = headers.index("Urgente") + 1 if urgente_para_concluido_urgente else None
            except ValueError as e:
                return False, f"Colunas necessárias não encontradas na aba Pedidos: {e}"

            # Atualizar as células básicas
            ws_pedidos.update_cell(row_index, status_col_index, novo_status)
            ws_pedidos.update_cell(row_index, ultima_atualizacao_col_index, ultima_atualizacao)
            ws_pedidos.update_cell(row_index, responsavel_atualizacao_col_index, responsavel)

            # Atualizar informações específicas baseado no status
            if novo_status == "Em Separação":
                ws_pedidos.update_cell(row_index, responsavel_separacao_col_index, responsavel)
                ws_pedidos.update_cell(row_index, data_separacao_col_index, ultima_atualizacao)
            elif novo_status == "Em Coleta":
                ws_pedidos.update_cell(row_index, responsavel_coleta_col_index, responsavel)
                ws_pedidos.update_cell(row_index, data_coleta_col_index, ultima_atualizacao)

            if urgente_para_concluido_urgente and urgente_col_index:
                ws_pedidos.update_cell(row_index, urgente_col_index, "Concluido Urgente")

            return True, "Status atualizado com sucesso no Google Sheets!"
        except Exception as e:
            return False, f"Erro ao atualizar status no Google Sheets: {str(e)}"

    def importar_e_atualizar_paco(self, arquivo_importado: str) -> tuple[bool, str]:
        """Importa um arquivo Excel e sobrescreve toda a aba 'paco' do Google Sheets com o conteúdo do arquivo."""
        try:
            if not self.client:
                raise ValueError("Cliente do Google Sheets não configurado. Verifique as credenciais.")
            if not self.SPREADSHEET_URL:
                raise ValueError("URL da planilha não configurada.")

            import pandas as pd
            # Ler arquivo importado
            df_import = pd.read_excel(arquivo_importado)
            df_import = df_import.fillna("")

            # Abrir a planilha do Google Sheets
            sheet = self.client.open_by_url(self.SPREADSHEET_URL)

            # Preparar os dados para sobrescrever
            values = [df_import.columns.tolist()] + df_import.values.tolist()
            values = [[str(cell) if pd.notna(cell) else "" for cell in row] for row in values]

            # Atualizar ou criar a aba 'paco'
            worksheet = self._get_or_create_worksheet(sheet, "paco", rows=len(values)+100, cols=len(values[0])+5)
            worksheet.clear()
            worksheet.append_rows(values, value_input_option="USER_ENTERED")
            worksheet.format('A1:Z1', {
                "backgroundColor": {"red": 0.8, "green": 0.8, "blue": 0.8},
                "horizontalAlignment": "CENTER",
                "textFormat": {"bold": True}
            })
            worksheet.freeze(rows=1)

            return True, "Aba 'paco' sobrescrita com sucesso com o conteúdo do arquivo importado!"
        except Exception as e:
            return False, f"Erro ao importar e sobrescrever aba 'paco': {str(e)}"

    def get_paco_as_dataframe(self) -> pd.DataFrame:
        """Lê a aba 'paco' do Google Sheets e retorna como DataFrame."""
        try:
            if not self.client:
                raise ValueError("Cliente do Google Sheets não configurado. Verifique as credenciais.")
            if not self.SPREADSHEET_URL:
                raise ValueError("URL da planilha não configurada.")

            sheet = self.client.open_by_url(self.SPREADSHEET_URL)
            ws_paco = sheet.worksheet("paco")
            data = ws_paco.get_all_records()
            df = pd.DataFrame(data)
            return df
        except Exception as e:
            if st:
                st.error(f"Erro ao ler a aba 'paco' do Google Sheets: {str(e)}")
            else:
                print(f"Erro ao ler a aba 'paco' do Google Sheets: {str(e)}")
            return pd.DataFrame()

    def get_proximo_numero_pedido(self, prefixo="REQ-") -> int:
        """
        Busca o maior número de pedido já existente na aba 'Pedidos' e retorna o próximo número disponível.
        Considera apenas pedidos no formato REQ-XXX (três dígitos).
        """
        try:
            if not self.client or not self.SPREADSHEET_URL:
                return 1
            sheet = self.client.open_by_url(self.SPREADSHEET_URL)
            ws_pedidos = sheet.worksheet("Pedidos")
            pedidos = ws_pedidos.col_values(1)  # Coluna Numero_Pedido
            max_num = 0
            padrao = re.compile(rf"{prefixo}(\d{{3}})$")
            for p in pedidos[1:]:  # Ignorar cabeçalho
                m = padrao.match(p.strip())
                if m:
                    num = int(m.group(1))
                    if num > max_num:
                        max_num = num
            return max_num + 1
        except Exception as e:
            if st:
                st.warning(f"Não foi possível buscar o próximo número de pedido: {str(e)}")
            else:
                print(f"Não foi possível buscar o próximo número de pedido: {str(e)}")
            return 1
