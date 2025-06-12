import streamlit as st
from controllers.pedido_controller import PedidoController
from datetime import datetime
import time
import pandas as pd
import os
from pathlib import Path
from fpdf import FPDF
from utils.print_manager import PrintManager

class PedidoHistoricoView:
    def __init__(self, controller: PedidoController):
        self.controller = controller
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

            {
            .detalhes-do-pedido {
                font-size: 14px;
                line-height: 1.5;
                margin-top: 1rem;
                padding: 1rem;
                background-color: #f8f9fa;
            
            }
            
            /* Status selectbox styling */
            .stSelectbox [data-baseweb="select"] {
                min-width: 120px;
            }
            
            /* Compact status badges */
            .status-badge {
                display: inline-block;
                padding: 0.25rem 0.5rem;
                border-radius: 4px;
                font-size: 0.875rem;
                font-weight: 600;
                text-align: center;
                white-space: nowrap;
                vertical-align: middle;
                line-height: 1.2;
            }

            /* Status select container */
            
            .status-select-label {
                font-size: 14px;
                /*font-weight: 600;
                color: #1f2937;
            }

            /* Ajuste do layout de colunas */
            [data-testid="column"] {
                width: auto !important;
                flex: 1 1 auto !important;
            }

            /* Container principal mais largo */
            [data-testid="stAppViewContainer"] > .main {
                padding-left: 1rem !important;
                padding-right: 1rem !important;
            }

            /* Ajuste para o modo wide */
            @media (min-width: 1200px) {
                .block-container {
                    padding-left: 2rem !important;
                    padding-right: 2rem !important;
                    max-width: 1400px !important;  /* Aumentando a largura máxima */
                }
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

    def mostrar_interface(self):
        """Mostra a interface do histórico de pedidos"""
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
                        index=0
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

            # Converter coluna de data para datetime
            df_pedidos['Data'] = pd.to_datetime(df_pedidos['Data'], errors='coerce')

            # Aplicar filtros de data se fornecidos
            if data_inicial is not None:
                df_pedidos = df_pedidos[df_pedidos['Data'].dt.date >= data_inicial]
            if data_final is not None:
                df_pedidos = df_pedidos[df_pedidos['Data'].dt.date <= data_final]

            # Layout em duas colunas com proporção ajustada
            col1, col2 = st.columns([4, 1])

            with col1:
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
                            st.success("Status do(s) pedido(s) atualizado(s).")
                            st.rerun()

            with col2:
                st.markdown("##### Detalhes do Pedido")
                
                # Encontrar o pedido selecionado e verificar mudanças de status
                for idx, row in edited_df.iterrows():
                    if row['Selecionar']:
                        status_atual = row['Status'].upper()
                        
                        # Mostrar detalhes do pedido selecionado com fonte menor
                        st.markdown('<div class="pedido-detalhes">', unsafe_allow_html=True)
                        col1_details, col2_details = st.columns(2)
                        
                        with col1_details:
                            st.markdown(f"""
                            **Número:** {row['Número']}<br>
                            **Data:** {row['Data']}<br>
                            **Serial:** {row['Serial']}<br>
                            **Máquina:** {row['Máquina']}<br>
                            **Posto:** {row['Posto']}<br>
                            **Coordenada:** {row['Coordenada']}
                            """, unsafe_allow_html=True)
                        
                        with col2_details:
                            st.markdown(f"""
                            **Modelo:** {row['Modelo']}<br>
                            **OT:** {row['OT']}<br>
                            **Semiacabado:** {row['Semiacabado']}<br>
                            **Pagoda:** {row['Pagoda']}<br>
                            **Status Atual:** {status_atual}
                            """, unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                        # Adicionar seletor de status
                        st.markdown('<div class="status-select-container">', unsafe_allow_html=True)
                        st.markdown('<div class="status-select-label">Alterar Status</div>', unsafe_allow_html=True)
                        novo_status = st.selectbox(
                            "Novo Status",
                            options=["PENDENTE", "PROCESSO", "CONCLUÍDO"],
                            index=["PENDENTE", "PROCESSO", "CONCLUÍDO"].index(status_atual),
                            key="status_selector",
                            label_visibility="collapsed"
                        )
                        
                        # Botão para atualizar status
                        if novo_status != status_atual:
                            if st.button("💾 Salvar Alteração", type="primary"):
                                try:
                                    self.controller.atualizar_status_pedido(
                                        numero_pedido=row['Número'],
                                        novo_status=novo_status,
                                        responsavel="Usuário do Sistema"
                                    )
                                    st.success("Status do pedido atualizado.")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Erro ao atualizar status: {str(e)}")
                        st.markdown('</div>', unsafe_allow_html=True)
                        break
                else:
                    st.info("👈 Selecione um pedido na tabela para ver os detalhes")

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
                PEDIDO DE REQUISIÇÃO
=================================================
Número: {info['Numero_Pedido']}
Data: {info['Data']}
Status: {pedido['status']}

INFORMAÇÕES DO PRODUTO:
-------------------------------------------------
Serial: {info['Serial']}
Máquina: {info['Maquina']}
Posto: {info['Posto']}
Coordenada: {info['Coordenada']}

DETALHES DO ITEM:
-------------------------------------------------
Modelo: {info['Modelo']}
OT: {info['OT']}
Semiacabado: {info['Semiacabado']}
Pagoda: {info['Pagoda']}

FLUXO DE PROCESSAMENTO:
-------------------------------------------------
Urgente: {"Sim" if info.get('Urgente') == True else "Não"}
"""
        
        # Adicionar informações de separação se existirem
        if info.get('Responsavel_Separacao'):
            texto += f"""
Responsável Separação: {info['Responsavel_Separacao']}
Data Separação: {info['Data_Separacao']}"""
        
        # Adicionar informações de coleta se existirem
        if info.get('Responsavel_Coleta'):
            texto += f"""
Responsável Coleta: {info['Responsavel_Coleta']}
Data Coleta: {info['Data_Coleta']}"""
        
        texto += "\n-------------------------------------------------"
        
        texto += "\n\nAssinaturas:\n"
        texto += "\nSeparador: _____________________________"
        texto += "\nColetador: _____________________________"
        texto += f"\n\nImpresso em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
        
        return texto

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