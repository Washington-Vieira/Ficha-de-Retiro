import streamlit as st
from controllers.pedido_controller import PedidoController
from typing import List, Dict
import pandas as pd
from datetime import datetime

class PedidoView:
    def __init__(self, controller: PedidoController):
        self.controller = controller
        # Aplicar estilos CSS personalizados
        self._aplicar_estilos()

    def _aplicar_estilos(self):
        """Aplica estilos CSS personalizados para melhorar a aparência"""
        st.markdown("""
        <style>
            /* Título principal */
            .titulo-secao {
                color: #2c3e50;
                font-size: 22px;
                font-weight: 600;
                margin-bottom: 25px;
                text-align: center;
            }
            
            /* Campo de nome do solicitante */
            [data-testid="stTextInput"] input[aria-label=""] {
                border: 2px solid #3498db !important;
                border-radius: 4px !important;
                padding: 10px !important;
                font-size: 14px !important;
                background-color: #ffffff !important;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1) !important;
                transition: all 0.3s ease !important;
            }

            [data-testid="stTextInput"] input[aria-label=""]:focus {
                border-color: #2980b9 !important;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.15) !important;
            }

            [data-testid="stTextInput"] input[aria-label=""]:hover {
                border-color: #2980b9 !important;
            }
            
            /* Campos de entrada */
            .stTextArea>div>div>textarea,
            .stNumberInput>div>div>input {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 8px 12px;
                font-size: 14px;
                width: 100%;
            }
            
            .stTextArea>div>div>textarea:focus,
            .stNumberInput>div>div>input:focus {
                border-color: #3498db;
                box-shadow: none;
            }
            
            /* Remove labels dos inputs do Streamlit */
            .stNumberInput label,
            .stTextInput label,
            .stTextArea label {
                display: none !important;
            }
            
            /* Ajustes para o layout em colunas */
            .css-1r6slb0,
            .css-12w0qpk {
                background-color: transparent !important;
                border: none !important;
                padding: 0 10px !important;
            }
            
            /* Mensagens de sucesso e erro */
            .stSuccess,
            .stError {
                padding: 12px;
                border-radius: 4px;
                margin: 15px 0;
            }
            
            /* Campos de seleção */
            .stSelectbox {
                margin-bottom: 15px;
            }
            
            /* Informações do item */
            .info-item {
                background-color: #f8f9fa;
                padding: 15px;
                border-radius: 4px;
                margin: 15px 0;
            }
            
            /* Tabela de posições */
            .posicoes-table {
                margin: 15px 0;
            }
            
            /* Botões de posição */
            .posicao-button {
                width: 100%;
                padding: 10px;
                margin: 5px;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                background-color: white;
                cursor: pointer;
                transition: all 0.3s ease;
            }
            
            .posicao-button:hover {
                background-color: #f0f0f0;
                border-color: #3498db;
            }
            
            /* Contagem de posições */
            .contagem-posicoes {
                background-color: #e8f4f8;
                padding: 15px;
                border-radius: 4px;
                text-align: center;
                margin: 15px 0;
            }
            
            /* Formulário de requisição */
            .requisicao-form {
                background-color: #f8f9fa;
                padding: 20px;
                border-radius: 4px;
                margin-top: 25px;
            }
        </style>
        """, unsafe_allow_html=True)

    def _mostrar_posicoes_e_contagem(self, dados, cliente: str, rack: str):
        """Mostra a tabela de posições e a contagem"""
        # Filtrar posições do rack (remover dependência de cliente)
        posicoes = [
            item.locacao
            for item in dados
            if item.rack.lower() == rack.lower()
        ]
        
        if posicoes:
            # Layout em duas colunas
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown("### 📍 Posições no RACK")
                # Criar grid de 4 colunas com as posições
                num_colunas = 4
                num_linhas = (len(posicoes) + num_colunas - 1) // num_colunas
                
                # Criar colunas para os botões
                cols = st.columns(num_colunas)
                
                # Distribuir posições entre as colunas
                for i, posicao in enumerate(posicoes):
                    col_idx = i % num_colunas
                    with cols[col_idx]:
                        if st.button(
                            posicao,
                            key=f"pos_{i}",
                            use_container_width=True,
                            type="secondary"
                        ):
                            # Quando o botão é clicado, salvar a posição selecionada
                            st.session_state.posicao_selecionada = posicao
            
            with col2:
                st.markdown("### 📊 Total de Posições")
                st.markdown(
                    f'<div class="contagem-posicoes">'
                    f'<h1>{len(posicoes)}</h1>'
                    f'<p>posições disponíveis</p>'
                    f'</div>',
                    unsafe_allow_html=True
                )
        else:
            st.warning(f"Nenhuma posição encontrada para o RACK {rack}")

    def _mostrar_formulario_requisicao(self, item_selecionado):
        """Mostra o formulário de requisição com todas as informações"""
        st.markdown('<div class="requisicao-form">', unsafe_allow_html=True)
        st.markdown("### 📋 Pedido de Requisição")
        
        # Informações do item
        st.markdown("#### Informações do Item")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            **RACK:** {item_selecionado.rack}  
            **Localização:** {item_selecionado.locacao}  
            **CÓD Yazaki:** {item_selecionado.cod_yazaki}  
            **Código Cabo:** {item_selecionado.codigo_cabo}
            """)
        
        with col2:
            st.markdown(f"""
            **Seção:** {item_selecionado.seccao}  
            **Cor:** {item_selecionado.cor}  
            **Projeto:** {item_selecionado.projeto or 'N/A'}  
            **Cod OES:** {item_selecionado.cod_oes or 'N/A'}
            """)
        
        # Formulário
        with st.form(key="pedido_form", clear_on_submit=True):
            st.markdown("#### Dados do Solicitante")
            
            solicitante = st.text_input(
                "Nome do Solicitante",
                placeholder="Digite seu nome completo"
            )
            # Botão de seleção para urgência
            try:
                urgente = st.toggle("Esse pedido é urgente?", key="urgente_toggle_rapido")
            except AttributeError:
                urgente = st.checkbox("Esse pedido é urgente?", key="urgente_toggle_rapido")
            
            quantidade = st.number_input(
                "Quantidade",
                min_value=1,
                value=1
            )
            
            observacoes = st.text_area(
                "Observações",
                placeholder="Digite aqui observações importantes sobre o pedido (opcional)"
            )
            
            # Botão de submit
            submitted = st.form_submit_button("💾 Criar Pedido de Requisição")
            
            if submitted:
                if not solicitante:
                    st.error("Por favor, informe o nome do solicitante!")
                    return
                
                try:
                    # Criar pedido
                    pedido = {
                        "cliente": item_selecionado.cliente,
                        "rack": item_selecionado.rack,
                        "locacao": item_selecionado.locacao,
                        "solicitante": solicitante,
                        "observacoes": observacoes,
                        "urgente": urgente,
                        "data": datetime.now(),
                        "itens": [{
                            "cod_yazaki": item_selecionado.cod_yazaki,
                            "codigo_cabo": item_selecionado.codigo_cabo,
                            "seccao": item_selecionado.seccao,
                            "cor": item_selecionado.cor,
                            "quantidade": quantidade
                        }]
                    }
                    
                    # Salvar pedido
                    numero_pedido = self.controller.salvar_pedido(pedido)
                    
                    # Limpar seleção após criar pedido
                    if 'posicao_selecionada' in st.session_state:
                        del st.session_state.posicao_selecionada
                    
                    st.success(f"""
                    ✅ Pedido {numero_pedido} criado com sucesso!
                    
                    Você pode visualizá-lo na aba de Histórico.
                    """)
                    
                except Exception as e:
                    st.error(f"""
                    ❌ Erro ao criar pedido:
                    
                    {str(e)}
                    
                    Por favor, tente novamente ou contate o suporte.
                    """)
        
        st.markdown('</div>', unsafe_allow_html=True)

    def mostrar_interface(self):
        st.title("📦 Localizações - Paco")
        # Remover exibição da tabela de localizações
        st.markdown("Selecione a opção 'Novo Pedido' no menu ao lado para iniciar um novo pedido.")