import pandas as pd
from datetime import datetime
from models.pedido import Pedido
from typing import List, Optional
import streamlit as st
import os
import shutil
from utils.sheets_pedidos_sync import SheetsPedidosSync
import webbrowser
import pathlib
import base64

class PedidoController:
    def __init__(self, caminho_planilha: str, enable_sheets: bool = False):
        """
        Inicializa o controlador com o caminho da planilha de localizações
        Args:
            caminho_planilha: Caminho da planilha que contém as localizações (definido no .env)
            enable_sheets: Se True, inicializa o SheetsPedidosSync
        """
        # Normalizar o caminho da planilha
        self.caminho_planilha = os.path.abspath(caminho_planilha)
        self.pedidos = []
        
        # Definir caminho do arquivo de pedidos
        self.diretorio_base = os.path.dirname(os.path.abspath(__file__))
        self.diretorio_pedidos = os.path.join(os.path.dirname(self.diretorio_base), 'pedidos')
        self.arquivo_pedidos = os.path.join(self.diretorio_pedidos, 'pedidos.xlsx')
        self.diretorio_backup = os.path.join(self.diretorio_pedidos, 'backup')

        # Criar diretórios se não existirem
        os.makedirs(self.diretorio_pedidos, exist_ok=True)
        os.makedirs(self.diretorio_backup, exist_ok=True)

        # Inicializar Google Sheets Sync
        self.sheets_sync = None
        if enable_sheets:
            from utils.sheets_pedidos_sync import SheetsPedidosSync
            self.sheets_sync = SheetsPedidosSync(enable_sheets=True)

        # Verificar se a planilha existe
        if not os.path.exists(self.caminho_planilha):
            st.error(f"""
            ❌ Arquivo de planilha não encontrado!
            
            O sistema está procurando o arquivo em:
            {self.caminho_planilha}
            
            Por favor, verifique se:
            1. O arquivo existe neste local
            2. O nome do arquivo está correto
            3. Você tem permissão para acessar o arquivo
            """)

    def _carregar_planilha(self, caminho: str) -> List[Pedido]:
        """
        Carrega os dados da planilha SOMENTE do Google Sheets ou do arquivo local, se não for possível conectar.
        """
        try:
            # Verifica se o arquivo existe
            if not os.path.exists(caminho):
                raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")

            # Tenta abrir a planilha local e ler a aba correta
            try:
                # Tenta ler a aba 'Projeto' (ajuste se o nome for diferente)
                df = pd.read_excel(caminho, sheet_name='Projeto', dtype=str)
            except ValueError as ve:
                # Se a aba não existir, mostra as abas disponíveis
                abas = pd.ExcelFile(caminho).sheet_names
                raise Exception(f"Aba 'Projeto' não encontrada. Abas disponíveis: {abas}")
            except Exception as e:
                raise Exception(f"Erro ao ler a planilha: {str(e)}")

            df = df.fillna("")
            # Mapeia os nomes das colunas da planilha (sem Cliente)
            colunas_mapeadas = {
                'RACK': 'rack',
                'CÓD Yazaki': 'cod_yazaki',
                'Codigo Cabo': 'codigo_cabo',
                'Secção': 'seccao',
                'Cor': 'cor',
                'Locação': 'locacao',
                'Projeto': 'projeto',
                'Cod OES': 'cod_oes'
            }
            # Renomeia as colunas para corresponder aos nomes dos atributos da classe
            df = df.rename(columns=colunas_mapeadas)
            # Checa se todas as colunas obrigatórias existem
            obrigatorias = list(colunas_mapeadas.values())
            faltando = [col for col in obrigatorias if col not in df.columns]
            if faltando:
                raise Exception(f"Colunas obrigatórias faltando na planilha: {faltando}")
            # Limpa os dados
            for col in df.columns:
                if df[col].dtype == 'object':
                    df[col] = df[col].fillna('').astype(str).str.strip()
            # Converte o DataFrame para lista de objetos Pedido
            pedidos = [
                Pedido(
                    id=idx + 1,
                    rack=row.get('rack', ''),
                    cod_yazaki=row.get('cod_yazaki', ''),
                    codigo_cabo=row.get('codigo_cabo', ''),
                    seccao=row.get('seccao', ''),
                    cor=row.get('cor', ''),
                    locacao=row.get('locacao', ''),
                    projeto=row.get('projeto', ''),
                    cod_oes=row.get('cod_oes', '')
                )
                for idx, (_, row) in enumerate(df.iterrows())
            ]
            return pedidos
        except Exception as e:
            st.error(f"Erro ao carregar dados da planilha local: {str(e)}")
            return []

    def carregar_dados(self):
        """Carrega os dados usando a função cacheada"""
        self.pedidos = self._carregar_planilha(self.caminho_planilha)
        return self.pedidos

    def _fazer_backup(self):
        """Faz backup do arquivo antes de modificá-lo"""
        try:
            if os.path.exists(self.arquivo_pedidos):
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_path = os.path.join(
                    self.diretorio_backup, 
                    f"pedidos_backup_{timestamp}.xlsx"
                )
                
                # Copiar arquivo atual para backup
                shutil.copy2(self.arquivo_pedidos, backup_path)
                
                # Manter apenas os últimos 10 backups
                backups = sorted([
                    os.path.join(self.diretorio_backup, f) 
                    for f in os.listdir(self.diretorio_backup)
                    if f.endswith('.xlsx')
                ])
                while len(backups) > 10:
                    os.remove(backups.pop(0))
        except Exception as e:
            st.warning(f"Não foi possível fazer backup: {str(e)}")

    def _ler_pedidos(self) -> pd.DataFrame:
        """Lê a aba 'Pedidos' do Google Sheets com cache"""
        try:
            # Verificar cache
            if 'cache_pedidos' in st.session_state:
                return st.session_state['cache_pedidos']

            if self.sheets_sync and self.sheets_sync.client and self.sheets_sync.SPREADSHEET_URL:
                sheet = self.sheets_sync.client.open_by_url(self.sheets_sync.SPREADSHEET_URL)
                worksheet = sheet.worksheet("Pedidos")
                data = worksheet.get_all_records()
                df = pd.DataFrame(data)
                # Garantir que as colunas existam
                if 'Ultima_Atualizacao' not in df.columns:
                    df['Ultima_Atualizacao'] = ""
                if 'Responsavel_Atualizacao' not in df.columns:
                    df['Responsavel_Atualizacao'] = ""
                
                # Salvar no cache
                st.session_state['cache_pedidos'] = df
                return df
            else:
                return pd.DataFrame()
        except Exception as e:
            if "Quota exceeded" in str(e) or "[429]" in str(e):
                # Se tiver cache, usa ele
                if 'cache_pedidos' in st.session_state:
                    return st.session_state['cache_pedidos']
                return pd.DataFrame()
            return pd.DataFrame()

    def _ler_itens(self) -> pd.DataFrame:
        """Lê a aba 'Itens' do Google Sheets com cache"""
        try:
            # Verificar cache
            if 'cache_itens' in st.session_state:
                return st.session_state['cache_itens']

            if self.sheets_sync and self.sheets_sync.client and self.sheets_sync.SPREADSHEET_URL:
                sheet = self.sheets_sync.client.open_by_url(self.sheets_sync.SPREADSHEET_URL)
                worksheet = sheet.worksheet("Itens")
                data = worksheet.get_all_records()
                df = pd.DataFrame(data)
                
                # Salvar no cache
                st.session_state['cache_itens'] = df
                return df
            else:
                return pd.DataFrame()
        except Exception as e:
            if "Quota exceeded" in str(e) or "[429]" in str(e):
                # Se tiver cache, usa ele
                if 'cache_itens' in st.session_state:
                    return st.session_state['cache_itens']
                return pd.DataFrame()
            return pd.DataFrame()

    def _gerar_numero_pedido(self) -> str:
        """Gera um número único para o pedido"""
        try:
            if not os.path.exists(self.arquivo_pedidos):
                return "REQ-001"
            df = pd.read_excel(self.arquivo_pedidos)
            if df.empty or 'Numero_Pedido' not in df.columns:
                return "REQ-001"
            # Garante que pega o último número válido
            numeros = df['Numero_Pedido'].dropna().tolist()
            if not numeros:
                return "REQ-001"
            ultimo_numero = numeros[-1]
            try:
                numero = int(ultimo_numero.split("-")[-1]) + 1
            except Exception:
                numero = len(numeros) + 1
            return f"REQ-{numero:03d}"
        except Exception:
            return "REQ-001"

    def _normalizar_status(self, status: str) -> str:
        """Normaliza o status para maiúsculo e garante que seja um dos valores válidos."""
        status_upper = status.upper()
        if status_upper not in ['PENDENTE', 'PROCESSO', 'CONCLUÍDO']:
            raise ValueError(f"Status inválido: {status}. Status permitidos: PENDENTE, PROCESSO, CONCLUÍDO")
        return status_upper

    def _verificar_serial_mesmo_lote(self, serial: str, maquina: str, posto: str, coordenada: str) -> bool:
        """
        Verifica se já existe um pedido PENDENTE com o mesmo serial, máquina, posto e coordenada
        """
        try:
            if not os.path.exists(self.arquivo_pedidos):
                return False

            df = pd.read_excel(self.arquivo_pedidos)
            if df.empty:
                return False

            # Só bloqueia se já houver um pedido PENDENTE igual
            pedidos_serial = df[
                (df['Serial'] == serial) &
                (df['Status'] == 'PENDENTE') &
                (df['Maquina'] == maquina) &
                (df['Posto'] == posto) &
                (df['Coordenada'] == coordenada)
            ]

            return len(pedidos_serial) > 0
        except Exception as e:
            st.error(f"Erro ao verificar serial: {str(e)}")
            return False

    def salvar_pedido(self, pedido_info: dict) -> str:
        """
        Salva um novo pedido no arquivo Excel e sincroniza com o Google Sheets
        
        Args:
            pedido_info (dict): Dicionário com as informações do pedido
        
        Returns:
            str: Número do pedido criado
        """
        try:
            # Verificar se o arquivo existe
            if not os.path.exists(self.arquivo_pedidos):
                # Criar DataFrame vazio com as colunas corretas
                df = pd.DataFrame(columns=[
                    "Numero_Pedido", "Data", "Serial", "Maquina", "Posto", "Coordenada",
                    "Modelo", "OT", "Semiacabado", "Pagoda", "Solicitante", "Observacoes",
                    "Urgente", "Status", "Ultima_Atualizacao", "Responsavel_Atualizacao"
                ])
                # Salvar arquivo vazio
                df.to_excel(self.arquivo_pedidos, index=False)

            # Verificar se o serial já existe no mesmo lote
            if self._verificar_serial_mesmo_lote(
                pedido_info['serial'],
                pedido_info['maquina'],
                pedido_info['posto'],
                pedido_info['coordenada']
            ):
                raise ValueError("Este serial já existe em um pedido ativo com as mesmas informações de máquina, posto e coordenada.")

            # Gerar número do pedido
            numero_pedido = self._gerar_numero_pedido()

            # Fazer backup antes de modificar
            self._fazer_backup()

            # Ler o arquivo atual
            df = pd.read_excel(self.arquivo_pedidos)

            # Preparar novo pedido
            novo_pedido = {
                "Numero_Pedido": numero_pedido,
                "Data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Serial": pedido_info['serial'],
                "Maquina": pedido_info['maquina'],
                "Posto": pedido_info['posto'],
                "Coordenada": pedido_info['coordenada'],
                "Modelo": pedido_info['modelo'],
                "OT": pedido_info['ot'],
                "Semiacabado": pedido_info['semiacabado'],
                "Pagoda": pedido_info['pagoda'],
                "Solicitante": pedido_info['solicitante'],
                "Observacoes": pedido_info['observacoes'],
                "Urgente": pedido_info['urgente'],
                "Status": "PENDENTE",
                "Ultima_Atualizacao": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Responsavel_Atualizacao": pedido_info['solicitante']
            }

            # Adicionar novo pedido ao DataFrame
            df = pd.concat([df, pd.DataFrame([novo_pedido])], ignore_index=True)

            # Salvar no arquivo local
            df.to_excel(self.arquivo_pedidos, index=False)

            # Sincronizar com Google Sheets se habilitado
            if self.sheets_sync and self.sheets_sync.client:
                try:
                    # Preparar dados para o Google Sheets
                    df_pedidos = df.copy()
                    df_itens = pd.DataFrame([{
                        "Numero_Pedido": numero_pedido,
                        "Serial": pedido_info['serial'],
                        "Quantidade": pedido_info.get('quantidade', 1)
                    }])

                    # Sincronizar com Google Sheets
                    success, message = self.sheets_sync.salvar_pedido_completo(df_pedidos, df_itens)
                    if not success:
                        st.warning(f"Aviso: {message}")
                except Exception as e:
                    st.warning(f"Aviso: Erro ao sincronizar com Google Sheets: {str(e)}")

            return numero_pedido

        except Exception as e:
            st.error(f"Erro ao salvar pedido: {str(e)}")
            raise

    def buscar_pedidos(self, numero_pedido: Optional[str] = None, status: Optional[str] = None) -> pd.DataFrame:
        """
        Busca pedidos com base em filtros opcionais
        """
        try:
            # Se integração com Google Sheets está ativa, lê de lá
            if self.sheets_sync and self.sheets_sync.client and self.sheets_sync.SPREADSHEET_URL:
                df = self._ler_pedidos()
            # Senão, lê do arquivo local
            elif os.path.exists(self.arquivo_pedidos):
                df = pd.read_excel(self.arquivo_pedidos)
            else:
                return pd.DataFrame()

            # Converter a coluna de data para datetime
            if 'Data' in df.columns:
                df['Data'] = pd.to_datetime(df['Data'], errors='coerce')

            # Aplicar filtros se fornecidos
            if numero_pedido:
                df = df[df['Numero_Pedido'] == numero_pedido]
            if status:
                df = df[df['Status'] == status]

            return df
        except Exception as e:
            st.error(f"Erro ao buscar pedidos: {str(e)}")
            return pd.DataFrame()

    def get_pedido_detalhes(self, numero_pedido: str) -> dict:
        """Retorna os detalhes completos de um pedido do arquivo."""
        try:
            if not os.path.exists(self.arquivo_pedidos):
                return {}
            
            # Ler arquivo de pedidos
            df_pedidos = pd.read_excel(self.arquivo_pedidos)
            
            # Buscar pedido específico
            pedido = df_pedidos[df_pedidos["Numero_Pedido"] == numero_pedido].iloc[0]
            
            # Converter pedido para dicionário
            info_dict = {
                "Numero_Pedido": pedido["Numero_Pedido"],
                "Data": pedido["Data"],
                "Serial": pedido["Serial"],
                "Maquina": pedido["Maquina"],
                "Posto": pedido["Posto"],
                "Coordenada": pedido["Coordenada"],
                "Modelo": pedido["Modelo"],
                "OT": pedido["OT"],
                "Semiacabado": pedido["Semiacabado"],
                "Pagoda": pedido["Pagoda"],
                "Status": pedido["Status"],
                "Ultima_Atualizacao": pedido["Ultima_Atualizacao"],
                "Responsavel_Atualizacao": pedido["Responsavel_Atualizacao"]
            }
            return info_dict
        except Exception as e:
            st.error(f"Erro ao buscar detalhes do pedido: {str(e)}")
            return {}

    def atualizar_status_pedido(self, numero_pedido: str, novo_status: str, responsavel: str):
        """Atualiza o status de um pedido no arquivo."""
        try:
            # Normalizar o status para maiúsculo
            novo_status = self._normalizar_status(novo_status)
            
            # Carregar dados do arquivo
            if not os.path.exists(self.arquivo_pedidos):
                raise Exception("Arquivo de pedidos não encontrado")
            
            df_pedidos = pd.read_excel(self.arquivo_pedidos)
            
            # Encontrar o índice do pedido no DataFrame
            pedidos_encontrados = df_pedidos[
                df_pedidos['Numero_Pedido'].astype(str).str.strip().str.upper() == str(numero_pedido).strip().upper()
            ]
            if pedidos_encontrados.empty:
                # Tenta atualizar direto no Google Sheets
                if hasattr(self, 'sheets_sync') and self.sheets_sync:
                    success, message = self.sheets_sync.atualizar_status_pedido_sheets(
                        numero_pedido,
                        novo_status,
                        datetime.now().strftime('%d/%m/%Y %H:%M'),
                        responsavel
                    )
                    if not success:
                        st.error(f"Erro ao atualizar status no Google Sheets: {message}")
                        raise Exception(f"Erro ao atualizar status no Google Sheets: {message}")
                    else:
                        st.success(f"Status do pedido {numero_pedido} atualizado no Google Sheets!")
                        return
                else:
                    raise Exception(f"Pedido com número {numero_pedido} não encontrado localmente nem no Google Sheets.")
            
            idx = pedidos_encontrados.index[0]
            
            # Atualizar status e informações básicas
            ultima_atualizacao = datetime.now().strftime('%d/%m/%Y %H:%M')
            df_pedidos.loc[idx, 'Status'] = novo_status
            df_pedidos.loc[idx, 'Ultima_Atualizacao'] = ultima_atualizacao
            df_pedidos.loc[idx, 'Responsavel_Atualizacao'] = responsavel
            
            # Atualizar informações específicas baseado no status
            if novo_status == "PROCESSO":
                df_pedidos.loc[idx, 'Responsavel_Separacao'] = responsavel
                df_pedidos.loc[idx, 'Data_Separacao'] = ultima_atualizacao
            elif novo_status == "CONCLUÍDO":
                df_pedidos.loc[idx, 'Responsavel_Coleta'] = responsavel
                df_pedidos.loc[idx, 'Data_Coleta'] = ultima_atualizacao
            
            # Salvar alterações
            df_pedidos.to_excel(self.arquivo_pedidos, index=False)
            
            # Se houver integração com Google Sheets, atualizar lá também
            if hasattr(self, 'sheets_sync') and self.sheets_sync:
                success, message = self.sheets_sync.atualizar_status_pedido_sheets(
                    numero_pedido,
                    novo_status,
                    ultima_atualizacao,
                    responsavel
                )
                if not success:
                    st.warning(f"Aviso: {message}")
        except Exception as e:
            st.error(f"Erro ao atualizar status: {str(e)}")
            raise

    @staticmethod
    @st.cache_data
    def filtrar_dados(pedidos: List[Pedido], rack: Optional[str] = None) -> List[Pedido]:
        """Filtra os dados com cache. Cliente é ignorado se não existir."""
        resultado = pedidos
        if rack:
            rack = rack.lower()
            resultado = [p for p in resultado if hasattr(p, 'rack') and p.rack and p.rack.lower() == rack]
        return resultado

    def buscar_por_rack(self, rack: str) -> List[Pedido]:
        """Busca pedidos por rack (case-insensitive)"""
        return self.filtrar_dados(self.pedidos, rack=rack)

    def buscar_por_cliente_e_rack(self, cliente: str, rack: str) -> List[Pedido]:
        """Busca pedidos por rack apenas, ignorando cliente"""
        return self.filtrar_dados(self.pedidos, rack=rack)

    def imprimir_pedido(self, numero_pedido: str, view=None):
        """Gera um PDF do comprovante do pedido (layout texto) e retorna o link de download para o usuário"""
        try:
            # Buscar detalhes do pedido
            detalhes = self.get_pedido_detalhes(numero_pedido)
            if not detalhes:
                return None

            # Gerar texto do comprovante usando o método da view
            if view and hasattr(view, 'formatar_pedido_para_impressao'):
                texto = view.formatar_pedido_para_impressao(detalhes)
            else:
                # Fallback: texto básico se a view não estiver disponível
                texto = f"""
                PEDIDO DE REQUISIÇÃO #{detalhes['info']['Numero_Pedido']}
                Data: {detalhes['info']['Data']}
                
                INFORMAÇÕES DO PEDIDO
                --------------------
                Cliente: {detalhes['info']['Cliente']}
                RACK: {detalhes['info']['RACK']}
                Localização: {detalhes['info']['Localizacao']}
                Solicitante: {detalhes['info']['Solicitante']}
                Status: {detalhes['status']}
                
                ITENS DO PEDIDO
                --------------
                """
                for idx, item in enumerate(detalhes['itens'], 1):
                    texto += f"""
                Item {idx}:
                - CÓD Yazaki: {item['cod_yazaki']}
                - Código Cabo: {item['codigo_cabo']}
                - Seção: {item['seccao']}
                - Cor: {item['cor']}
                - Quantidade: {item['quantidade']}
                """

            # Gerar PDF
            from fpdf import FPDF
            import tempfile
            import base64
            import os
            import time

            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            
            # Ajustar o texto para remover espaços extras no início das linhas
            linhas = [linha.strip() for linha in texto.split('\n')]
            for linha in linhas:
                if linha:  # Só adiciona linhas não vazias
                    pdf.cell(0, 10, txt=linha, ln=True)

            # Salvar PDF temporário
            temp_dir = os.path.join(os.getcwd(), 'temp')
            os.makedirs(temp_dir, exist_ok=True)
            pdf_path = os.path.join(temp_dir, f"comprovante_{numero_pedido}_{int(time.time())}.pdf")
            pdf.output(pdf_path)

            # Ler PDF e gerar link base64
            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()
                b64 = base64.b64encode(pdf_bytes).decode()

            href = f'data:application/pdf;base64,{b64}'
            link_html = (
                f'<a href="{href}" target="_blank" download="comprovante_{numero_pedido}.pdf" '
                'style="font-size:18px;color:#007bff;font-weight:bold;">'
                '🔗 Baixar comprovante em PDF</a>'
            )
            return link_html
        except Exception as e:
            st.error(f"Erro ao gerar comprovante: {str(e)}")
            return None

    def carregar_local_paco(self) -> List[Pedido]:
        """
        Carrega os dados da aba 'Paco' do arquivo local, usando as colunas corretas.
        """
        try:
            df = pd.read_excel(self.caminho_planilha, sheet_name='Paco', dtype=str)
            df = df.fillna("")
            pedidos = [
                Pedido(
                    serial=row.get('Serial', ''),
                    maquina=row.get('Maquina', ''),
                    posto=row.get('Posto', ''),
                    coordenada=row.get('Coordenada', ''),
                    modelo=row.get('Modelo', ''),
                    ot=row.get('OT', ''),
                    semiacabado=row.get('Semiacabado', ''),
                    pagoda=row.get('Pagoda', '')
                )
                for _, row in df.iterrows()
            ]
            self.pedidos = pedidos
            return pedidos
        except Exception as e:
            st.error(f"Erro ao carregar dados da aba Paco: {str(e)}")
            return []

    def listar_maquinas(self) -> List[str]:
        if not self.pedidos:
            self.carregar_local_paco()
        return sorted(set(p.maquina for p in self.pedidos if p.maquina))

    def listar_postos_por_maquina(self, maquina: str) -> List[str]:
        if not self.pedidos:
            self.carregar_local_paco()
        # Garantir que só retorna postos únicos para a máquina
        return sorted(set(p.posto for p in self.pedidos if p.maquina == maquina and p.posto))

    def listar_coordenadas(self, maquina: str, posto: str) -> List[str]:
        if not self.pedidos:
            self.carregar_local_paco()
        return sorted(set(p.coordenada for p in self.pedidos if p.maquina == maquina and p.posto == posto))

    def buscar_pedido_por_maquina_posto_coordenada(self, maquina: str, posto: str, coordenada: str) -> Optional[Pedido]:
        if not self.pedidos:
            self.carregar_local_paco()
        for p in self.pedidos:
            if p.maquina == maquina and p.posto == posto and p.coordenada == coordenada:
                return p
        return None

    def carregar_paco_google_sheets(self) -> List[Pedido]:
        """
        Carrega os dados da aba 'paco' do Google Sheets, usando as colunas corretas e normalizando nomes e valores.
        """
        if not self.sheets_sync or not self.sheets_sync.client:
            st.error("Google Sheets não está configurado!")
            return []
        try:
            df = self.sheets_sync.get_paco_as_dataframe()
            # Normalizar nomes das colunas (remover espaços, capitalizar)
            df.columns = [str(col).strip().title() for col in df.columns]
            df = df.fillna("")
            pedidos = [
                Pedido(
                    serial=str(row.get('Serial', '')).strip(),
                    maquina=str(row.get('Maquina', '')).strip(),
                    posto=str(row.get('Posto', '')).strip(),
                    coordenada=str(row.get('Coordenada', '')).strip(),
                    modelo=str(row.get('Modelo', '')).strip(),
                    ot=str(row.get('Ot', '')).strip(),
                    semiacabado=str(row.get('Semiacabado', '')).strip(),
                    pagoda=str(row.get('Pagoda', '')).strip()
                )
                for _, row in df.iterrows()
            ]
            self.pedidos = pedidos
            return pedidos
        except Exception as e:
            st.error(f"Erro ao carregar dados da aba 'paco' do Google Sheets: {str(e)}")
            return []