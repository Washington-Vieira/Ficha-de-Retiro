import streamlit as st
from controllers.pedido_controller import PedidoController
from datetime import datetime, timedelta
import time
import pandas as pd
import os
from pathlib import Path
from fpdf import FPDF
from utils.print_manager import PrintManager
import base64
import platform
import json
import tempfile
import subprocess
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from io import BytesIO

class PedidoHistoricoView:
    def __init__(self, controller: PedidoController):
        self.controller = controller
        self.config_path = os.path.join(os.path.dirname(__file__), '..', 'config.json')
        self._aplicar_estilos()

    def _aplicar_estilos(self):
        """Aplica estilos CSS personalizados"""
        st.markdown("""
        <style>
            /* Status tags */
            .status-pendente {
                background-color: #ffeb3b;
                color: black;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }
            
            .status-processo {
                background-color: #2196f3;
                color: white;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }
            
            .status-concluido {
                background-color: #4caf50;
                color: white;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }
            
            /* Tabela responsiva */
            .table-container {
                width: 100%;
                overflow-x: auto;
                margin-top: 1rem;
            }
            
            .dataframe {
                width: 100% !important;
                margin-bottom: 1rem;
                border-collapse: collapse;
                font-size: 14px;
                min-width: 1200px;
            }
            
            .dataframe th {
                background-color: #f8f9fa;
                font-weight: 600;
                text-align: left;
                padding: 8px 12px;
                border-bottom: 2px solid #dee2e6;
                white-space: nowrap;
                font-size: 13px;
            }
            
            .dataframe td {
                padding: 6px 12px;
                border-bottom: 1px solid #e9ecef;
                line-height: 1.2;
                white-space: nowrap;
                font-size: 13px;
            }
            
            .dataframe tr:hover {
                background-color: #f8f9fa;
            }
        </style>
        """, unsafe_allow_html=True)

    def _gerar_opcoes_status(self, status_atual):
        """Gera o HTML para o dropdown de status"""
        status_validos = ['Pendente', 'Processo', 'Concluído']
        options = [f'<option value="{s}"{" selected" if s == status_atual else ""}>{s}</option>' for s in status_validos]
        return '\n'.join(options)

    def _formatar_status_com_acao(self, row):
        """Formata o status com um dropdown para alteração"""
        numero_pedido = row['Número']
        status_atual = row['Status'].upper() if row['Status'] else ""
        
        # Formatar o status atual com as cores
        classe_status = {
            'PENDENTE': 'status-pendente',
            'PROCESSO': 'status-processo',
            'CONCLUÍDO': 'status-concluido'
        }.get(status_atual, '')
        
        # Gerar o HTML com o dropdown e botão
        html = f'''
        <div style="display: flex; align-items: center; gap: 8px;">
            <span class="{classe_status}">{status_atual}</span>
            <select id="status_{numero_pedido}" style="padding: 2px 4px; border-radius: 4px; border: 1px solid #ccc; height: 28px;">
                <option value="PENDENTE"{" selected" if status_atual == "PENDENTE" else ""}>PENDENTE</option>
                <option value="PROCESSO"{" selected" if status_atual == "PROCESSO" else ""}>PROCESSO</option>
                <option value="CONCLUÍDO"{" selected" if status_atual == "CONCLUÍDO" else ""}>CONCLUÍDO</option>
            </select>
            <button onclick="alterarStatus('{numero_pedido}')" 
                style="padding: 2px 8px; border-radius: 4px; background-color: #007bff; color: white; border: none; cursor: pointer; font-size: 12px; height: 28px;">
                Salvar
            </button>
        </div>'''
        return html

    def _listar_impressoras(self):
        """Lista todas as impressoras disponíveis no sistema"""
        try:
            if platform.system() == 'Windows':
                # Windows: usar wmic
                try:
                    output = subprocess.check_output('wmic printer get name', shell=True, universal_newlines=True)
                    impressoras = [linha.strip() for linha in output.split('\n')[1:] if linha.strip()]
                    return impressoras
                except:
                    return []
            else:
                # Linux/Mac: usar lpstat
                try:
                    output = subprocess.check_output(['lpstat', '-p'], universal_newlines=True)
                    impressoras = []
                    for line in output.split('\n'):
                        if line.startswith('printer'):
                            impressoras.append(line.split(' ')[1])
                    return impressoras
                except:
                    return []
        except:
            return []

    def _carregar_impressora_padrao(self):
        """Carrega a impressora padrão das configurações"""
        try:
            config = self._carregar_config()
            return config.get('impressora_padrao', '')
        except:
            return ''

    def _salvar_impressora_padrao(self, impressora):
        """Salva a impressora padrão nas configurações"""
        try:
            config = self._carregar_config()
            config['impressora_padrao'] = impressora
            
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=4)
            
            return True
        except:
            return False

    def _carregar_config(self):
        """Carrega as configurações do arquivo"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            return {}
        except:
            return {}

    def _imprimir_arquivo(self, arquivo_path, impressora):
        """Imprime um arquivo usando comandos do sistema operacional"""
        if impressora == 'PDF Virtual':
            return False  # Indica que deve usar o download
            
        try:
            if platform.system() == 'Windows':
                # Primeiro tenta com SumatraPDF
                sumatra_path = r"C:\Program Files\SumatraPDF\SumatraPDF.exe"
                if os.path.exists(sumatra_path):
                    cmd = [sumatra_path, "-print-to", impressora, arquivo_path]
                    subprocess.run(cmd, check=True)
                    return True
                else:
                    # Se não tem SumatraPDF, tenta com impressão via powershell
                    ps_command = f'(New-Object -ComObject Shell.Application).Namespace(0).ParseName("{arquivo_path}").InvokeVerb("Print")'
                    subprocess.run(['powershell', '-Command', ps_command], check=True)
                    return True
            else:
                # Linux/Mac usando lpr
                cmd = ["lpr", "-P", impressora, arquivo_path]
                subprocess.run(cmd, check=True)
                return True
        except:
            return False

    def _gerar_packlist_pdf(self, pedidos):
        """Gera o PDF com as etiquetas dos pedidos"""
        buffer = BytesIO()
        
        # Configurações da página
        largura_etiqueta = 60 * mm  # 60mm
        altura_etiqueta = 30 * mm   # 30mm
        margem = 0 * mm             # sem margem
        
        # Criar o PDF
        c = canvas.Canvas(buffer, pagesize=landscape((largura_etiqueta + 2*margem, altura_etiqueta + 2*margem)))
        
        for pedido in pedidos:
            # Configurar fonte e tamanho
            c.setFont("Helvetica", 8)
            
            # Posições Y para cada linha (de baixo para cima)
            y_pos = [25, 19, 13, 7]  # em mm
            
            # Linha 1: Número do Pedido + Data
            texto = f"{pedido['Numero_Pedido']} - {pedido['Data']}"
            c.drawString(margem + 2*mm, y_pos[0]*mm, texto)
            
            # Linha 2: Máquina
            texto = f"Máquina: {pedido['Maquina']}"
            c.drawString(margem + 2*mm, y_pos[1]*mm, texto)
            
            # Linha 3: Posto + Coordenada
            texto = f"Posto: {pedido['Posto']} - Coord: {pedido['Coordenada']}"
            c.drawString(margem + 2*mm, y_pos[2]*mm, texto)
            
            # Linha 4: Pagoda + Semiacabado
            texto = f"Pagoda: {pedido['Pagoda']} - {pedido['Semiacabado']}"
            c.drawString(margem + 2*mm, y_pos[3]*mm, texto)
            
            # Adicionar nova página para próxima etiqueta
            c.showPage()
        
        c.save()
        return buffer.getvalue()

    def mostrar_interface(self):
        """Mostra a interface do histórico de pedidos"""
        pedidos_lista = []  # Garante que a variável sempre existe
        st.markdown("#### Histórico de Pedidos")
        
        try:
            # Expandable filter section
            with st.expander("🔍 Filtros de Pesquisa"):
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    filtro_numero = st.text_input("Número do Pedido", value="")
                with col2:
                    filtro_status = st.selectbox(
                        "Status",
                        ["TODOS", "PENDENTE", "PROCESSO", "CONCLUÍDO"],
                        index=1
                    )
                with col3:
                    data_inicial = st.date_input("Data Inicial", value=None)
                with col4:
                    data_final = st.date_input("Data Final", value=None)

            # Carregar e filtrar dados
            df_pedidos = self.controller.buscar_pedidos(
                numero_pedido=filtro_numero if filtro_numero else None,
                status=filtro_status if filtro_status != "TODOS" else None
            )
            
            if df_pedidos.empty:
                st.info("Nenhum pedido encontrado.")
                return

            # Criar uma cópia explícita do DataFrame antes de modificar
            df_pedidos = df_pedidos.copy()
            
            # Converter coluna de data para datetime
            df_pedidos.loc[:, 'Data'] = pd.to_datetime(df_pedidos['Data'], errors='coerce')

            # Aplicar filtros de data se fornecidos
            if data_inicial is not None:
                df_pedidos = df_pedidos[df_pedidos['Data'].dt.date >= data_inicial].copy()
            if data_final is not None:
                df_pedidos = df_pedidos[df_pedidos['Data'].dt.date <= data_final].copy()

            # Exibir a tabela com seleção
            with st.expander("📋 Lista de Pedidos", expanded=True):
                total_pedidos = len(df_pedidos)
                st.write(f"Total de pedidos: {total_pedidos}")
                
                # Formatar DataFrame para exibição
                df_display = df_pedidos[ [
                    "Numero_Pedido", "Data", "Serial", "Maquina", 
                    "Posto", "Coordenada", "Modelo", "OT",
                    "Semiacabado", "Pagoda", "Status"
                ]].copy()

                # Renomear colunas
                df_display.columns = [
                    "Número", "Data", "Serial", "Máquina",
                    "Posto", "Coordenada", "Modelo", "OT",
                    "Semiacabado", "Pagoda", "Status"
                ]
                
                # Formatar a coluna de data
                df_display["Data"] = df_display["Data"].dt.strftime("%d/%m/%Y %H:%M")

                # Adicionar coluna de seleção no início
                df_display.insert(0, 'Selecionar', False)

                # Salvar DataFrame original para comparação
                df_display_original = df_display.copy()

                edited_df = st.data_editor(
                    df_display,
                    hide_index=True,
                    use_container_width=True,
                    column_config={
                        "Selecionar": st.column_config.CheckboxColumn(
                            "Selecionar",
                            help="Selecione para editar",
                            default=False,
                        ),
                        "Status": st.column_config.SelectboxColumn(
                            "Status",
                            help="Status do pedido",
                            options=["PENDENTE", "PROCESSO", "CONCLUÍDO"],
                            required=True
                        )
                    },
                    disabled=["Número", "Data", "Serial", "Máquina", "Posto", "Coordenada", 
                            "Modelo", "OT", "Semiacabado", "Pagoda"]
                )

                # Detectar alterações de status
                status_alterados = []
                for idx, row in edited_df.iterrows():
                    status_original = df_display_original.loc[idx, "Status"]
                    status_novo = row["Status"]
                    if status_original != status_novo:
                        status_alterados.append({
                            'numero_pedido': row['Número'],
                            'novo_status': status_novo
                        })

                # Se houver alterações, exibir botão para salvar
                if status_alterados:
                    if st.button("Salvar Alterações", type="primary"):
                        for alteracao in status_alterados:
                            try:
                                self.controller.atualizar_status_pedido(
                                    numero_pedido=alteracao['numero_pedido'],
                                    novo_status=alteracao['novo_status'],
                                    responsavel="Usuário do Sistema"
                                )
                            except Exception as e:
                                st.error(f"Erro ao atualizar status do pedido {alteracao['numero_pedido']}: {str(e)}")
                        st.rerun()

            # Nova seção para Packlist
            st.markdown("### 📃 Gerar lista")
            
            # Inicializar o estado de visualização se não existir
            if 'mostrar_preview' not in st.session_state:
                st.session_state.mostrar_preview = False
            
            # Filtro por período
            col_periodo1, col_periodo2, col_preview, col_download = st.columns([2, 2, 1, 1])
            with col_periodo1:
                periodo_inicio = st.time_input("Hora Inicial", datetime.now().replace(hour=8, minute=0))
            with col_periodo2:
                periodo_fim = st.time_input("Hora Final", datetime.now().replace(hour=17, minute=0))
            
            # Filtrar pedidos pelo período selecionado
            df_periodo = df_pedidos.copy()
            df_periodo['Hora'] = df_periodo['Data'].dt.time
            df_periodo = df_periodo[
                (df_periodo['Hora'] >= periodo_inicio) & 
                (df_periodo['Hora'] <= periodo_fim)
            ]

            with col_preview:
                if st.button("👁️ Pré-visualizar", type="primary", use_container_width=True):
                    st.session_state.mostrar_preview = not st.session_state.mostrar_preview

            with col_download:
                if not df_periodo.empty:
                    # Preparar dados para o PDF
                    pedidos_lista = []
                    for _, row in df_periodo.iterrows():
                        pedido = {
                            'Numero_Pedido': row['Numero_Pedido'],
                            'Data': row['Data'].strftime('%d/%m/%Y %H:%M'),
                            'Maquina': row['Maquina'],
                            'Posto': row['Posto'],
                            'Coordenada': row['Coordenada'],
                            'Pagoda': row['Pagoda'],
                            'Semiacabado': row['Semiacabado']
                        }
                        pedidos_lista.append(pedido)
                    
                    # Gerar PDF
                    pdf_bytes = self._gerar_packlist_pdf(pedidos_lista)
                    
                    # Botão de download igual ao pré-visualizar
                    if st.button("📄 Processar Lista", type="primary", use_container_width=True):
                        b64 = base64.b64encode(pdf_bytes).decode()
                        href = f'<a href="data:application/pdf;base64,{b64}" download="etiquetas_{periodo_inicio.strftime('%H%M')}_{periodo_fim.strftime('%H%M')}.pdf" style="display:block;text-align:center;padding:0.5rem 1rem;background-color:#1a2b3a;color:white;border-radius:0.5rem;text-decoration:none;font-weight:500;margin-top:0.5rem;">Gerar Etiquetas</a>'
                        st.markdown(href, unsafe_allow_html=True)
                        # Atualizar status silenciosamente após download
                        for _, row in df_periodo.iterrows():
                            try:
                                self.controller.atualizar_status_pedido(
                                    numero_pedido=row['Numero_Pedido'],
                                    novo_status='CONCLUÍDO',
                                    responsavel='Sistema (PDF Gerado)'
                                )
                            except:
                                pass

            # Mostrar total de pedidos encontrados
            if not df_periodo.empty:
                st.caption(f"Pedidos encontrados no período: {len(df_periodo)}")

            # Mostrar ou ocultar a pré-visualização baseado no estado
            if st.session_state.mostrar_preview:
                if not df_periodo.empty:
                    st.markdown("##### Pré-visualização das Etiquetas")
                    st.caption(f"Mostrando {len(df_periodo)} etiquetas do período selecionado. O tamanho real será 60x30mm.")
                    
                    # Criar colunas para mostrar múltiplas etiquetas por linha
                    num_colunas = 3
                    for i in range(0, len(df_periodo), num_colunas):
                        cols = st.columns(num_colunas)
                        for j in range(num_colunas):
                            idx = i + j
                            if idx < len(df_periodo):
                                row = df_periodo.iloc[idx]
                                with cols[j]:
                                    pedido_dict = {
                                        'Numero_Pedido': row['Numero_Pedido'],
                                        'Data': row['Data'].strftime('%d/%m/%Y %H:%M'),
                                        'Maquina': row['Maquina'],
                                        'Posto': row['Posto'],
                                        'Coordenada': row['Coordenada'],
                                        'Pagoda': row['Pagoda'],
                                        'Semiacabado': row['Semiacabado']
                                    }
                                    preview_html = self._gerar_preview_etiqueta(pedido_dict)
                                    st.markdown(preview_html, unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Erro ao carregar pedidos: {str(e)}")
            st.exception(e)  # Isso mostrará o traceback completo para debug

    def _formatar_status_badge(self, status):
        """Formata o status como um badge colorido"""
        status = status.upper() if status else ""
        return status  # Retorna apenas o texto, a formatação é feita via style

    def formatar_pedido_para_impressao(self, pedido: dict) -> str:
        """Formata os detalhes do pedido para impressão"""
        info = pedido['info']
        
        texto = f"""=================================================
PEDIDO: {info['Numero_Pedido']}
Data: {info['Data']}
=================================================
Serial: {info['Serial']}
Máquina: {info['Maquina']}
Posto: {info['Posto']}
Coordenada: {info['Coordenada']}
Modelo: {info['Modelo']}
OT: {info['OT']}
Semiacabado: {info['Semiacabado']}
Pagoda: {info['Pagoda']}
=================================================
Status: {pedido['status']}
================================================="""
        
        return texto

    def _gerar_etiquetas_texto(self, pedidos):
        """Gera o texto das etiquetas no formato solicitado"""
        etiquetas = []
        for pedido in pedidos:
            etiqueta = "\n".join([
                f"{pedido.get('Numero_Pedido', '').strip()}  Data: {pedido.get('Data', '').strip()}",
                f"Maquina: {pedido.get('Maquina', '').strip()}",
                f"Posto: {pedido.get('Posto', '').strip()} Coordenada: {pedido.get('Coordenada', '').strip()}",
                f"Pagoda: {pedido.get('Pagoda', '').strip()}",
                f"Semiacabado: {pedido.get('Semiacabado', '').strip()}"
            ])
            etiquetas.append(etiqueta)
        return '\n'.join(etiquetas)

    def _gerar_etiqueta_pdf(self, pedido, pdf):
        """Gera uma etiqueta para um pedido específico no formato solicitado"""
        pdf.set_font("Arial", size=9)
        left_margin = 0
        col_gap = 4  # Espaço entre as colunas
        y_start = pdf.get_y()

        # Primeira linha: REQ - XX        Data: DD/MM/YYYY HH:MM
        pdf.set_xy(left_margin, y_start)
        pdf.cell(col_gap, 4, f"{pedido.get('Numero_Pedido', '')}", ln=0)
        pdf.cell(0, 8, f"Data: {pedido.get('Data', '')}", ln=1)

        # Segunda linha: Maquina          <valor>
        pdf.set_x(left_margin)
        pdf.cell(col_gap, 4, "Maquina", ln=0)
        pdf.cell(0, 8, f"{pedido.get('Maquina', '')}", ln=1)

        # Terceira linha: Posto: XX       Cordenada: YY
        pdf.set_x(left_margin)
        pdf.cell(col_gap, 4, f"Posto: {pedido.get('Posto', '')}", ln=0)
        pdf.cell(0, 8, f"Cordenada: {pedido.get('Coordenada', '')}", ln=1)

        # Quarta linha: Pagoda: <valor>
        pdf.set_x(left_margin)
        pdf.cell(0, 4, f"Pagoda: {pedido.get('Pagoda', '')}", ln=1)

        pdf.ln(1)

        # Quinta linha: Semiacabado: <valor>
        pdf.set_x(left_margin)
        pdf.cell(0, 4, f"Semiacabado: {pedido.get('Semiacabado', '')}", ln=1)

        pdf.ln(0)

    def _gerar_preview_etiqueta(self, pedido):
        """Gera uma prévia da etiqueta em HTML para visualização"""
        preview_html = f"""
        <div style="
            width: 226px;  /* 60mm em pixels aproximadamente */
            height: 113px; /* 30mm em pixels aproximadamente */
            border: 1px solid #ccc;
            padding: 5px;
            margin: 10px 0;
            font-family: Arial;
            font-size: 14px;
            line-height: 1.4;
            overflow: hidden;
            background-color: white;
        ">
            <div>
                <strong>
                    <span style='cursor:pointer; color:#2c3e50;' onclick=\"alert('Número do Pedido: {pedido.get('Numero_Pedido', 'N/A')}')\">
                        {pedido.get('Numero_Pedido', 'N/A')}
                    </span>
                </strong> - {pedido.get('Data', 'N/A')}
            </div>
            <div><strong>Maq:</strong> {pedido.get('Maquina', 'N/A')}</div>
            <div><strong>Coord:</strong> {pedido.get('Coordenada', 'N/A')} - <strong>Posto:</strong> {pedido.get('Posto', 'N/A')}</div>
            <div><strong>Pag:</strong> {pedido.get('Pagoda', 'N/A')} - <strong>Semi:</strong> {pedido.get('Semiacabado', 'N/A')}</div>
        </div>
        """
        return preview_html

    _gerar_etiquetas_pdf = _gerar_packlist_pdf

    def _mostrar_tabela_pedidos(self, df: pd.DataFrame):
        """Mostra a tabela de pedidos com formatação"""
        if not df.empty:
            # Garantir que as datas estejam no formato correto para exibição
            if 'Data' in df.columns:
                df['Data'] = pd.to_datetime(df['Data']).dt.strftime("%d/%m/%Y %H:%M:%S")
            if 'Ultima_Atualizacao' in df.columns:
                df['Ultima_Atualizacao'] = pd.to_datetime(df['Ultima_Atualizacao']).dt.strftime("%d/%m/%Y %H:%M:%S")

            # Ordenar por data mais recente primeiro
            df = df.sort_values('Data', ascending=False)

            # Exibir a tabela
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True
            )