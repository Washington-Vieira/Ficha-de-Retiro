import streamlit as st
import pandas as pd

def mostrar_dashboard_gerencial(controller):
    """
    Exibe um dashboard gerencial com totais gerais.
    controller: instância de PedidoController
    """
    # Buscar todos os pedidos
    df_pedidos = controller.buscar_pedidos(status=None)
    if df_pedidos.empty:
        return

    # --- TOTAIS GERAIS ---
    total_pedidos = len(df_pedidos)
    total_concluido = len(df_pedidos[df_pedidos['Status'] == 'CONCLUÍDO'])
    total_processando = len(df_pedidos[df_pedidos['Status'] == 'PROCESSO'])
    total_pendente = len(df_pedidos[df_pedidos['Status'] == 'PENDENTE'])

    st.markdown(f"""
    <style>
    .dashboard-cards {{display: flex; gap: 18px; margin-bottom: 24px; flex-wrap: wrap;}}
    .dashboard-card {{
        background: #fff; border-radius: 8px; padding: 22px 28px; min-width: 220px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.08); text-align: center; font-size: 17px;
        font-weight: 500; border: 1px solid #eee; flex: 1 1 220px;
    }}
    .card-total {{background: #2c3e50; color: #fff;}}
    .card-concluido {{background: #90EE90;}}
    .card-processando {{background: #87CEEB;}}
    .card-pendente {{background: #ffd700;}}
    .card-urgente {{background: #ff7f7f; color: #fff;}}
    </style>
    <div class="dashboard-cards">
        <div class="dashboard-card card-total">TOTAL PEDIDOS<br><span style='font-size:28px'>{total_pedidos}</span></div>
        <div class="dashboard-card card-concluido">CONCLUÍDO<br><span style='font-size:28px'>{total_concluido}</span></div>
        <div class="dashboard-card card-processando">PROCESSO<br><span style='font-size:28px'>{total_processando}</span></div>
        <div class="dashboard-card card-pendente">PENDENTE<br><span style='font-size:28px'>{total_pendente}</span></div>
    </div>
    """, unsafe_allow_html=True)