import streamlit as st
from controllers.pedido_controller import PedidoController
from datetime import datetime
import pandas as pd
import os
import time
import json
import atexit
import contextlib
import sys
if sys.platform == "win32":
    import msvcrt  # Para Windows

class CacheManager:
    def __init__(self, cache_dir="pedidos/cache"):
        self.cache_dir = cache_dir
        self.cache_file = os.path.join(cache_dir, "leituras_cache.json")
        os.makedirs(cache_dir, exist_ok=True)
    
    def load_cache(self):
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
        except:
            return []
    
    def save_cache(self, data):
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def add_to_cache(self, serial, status, mensagem):
        cache = self.load_cache()
        cache.append({
            'serial': serial,
            'status': status,
            'mensagem': mensagem,
            'data': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        self.save_cache(cache)
    
    def clear_cache(self):
        if os.path.exists(self.cache_file):
            os.remove(self.cache_file)

class PedidoFormView:
    def __init__(self, pedido_controller: PedidoController):
        self.pedido_controller = pedido_controller
        self.cache_manager = CacheManager()
        
        # Inicializar controle de códigos processados
        if 'codigos_processados' not in st.session_state:
            st.session_state.codigos_processados = set()
            
        self._aplicar_estilos()

    def _aplicar_estilos(self):
        """Aplica estilos CSS personalizados"""
        st.markdown("""
        <style>
            /* Layout principal */
            .main .block-container {
                max-width: 100% !important;
                padding: 2rem !important;
            }

            /* Título principal */
            .titulo-secao {
                color: #2c3e50;
                font-size: 1.8rem;
                font-weight: 600;
                margin-bottom: 1.5rem;
                text-align: center;
                padding: 1rem;
                background: #f8f9fa;
                border-radius: 8px;
            }

            /* Formulário de pedido */
            .pedido-form {
                background-color: white;
                padding: 1.5rem;
                border-radius: 8px;
                margin: 1rem 0;
                border: 1px solid #e0e0e0;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            }

            /* Informações do pedido */
            .pedido-info {
                background-color: #f8f9fa;
                padding: 1.2rem;
                border-radius: 6px;
                margin-bottom: 1rem;
                border: 1px solid #e0e0e0;
            }

            /* Campos de entrada responsivos */
            .stTextInput input,
            .stTextArea textarea,
            .stNumberInput input {
                width: 100% !important;
                padding: 0.8rem !important;
                border: 1px solid #dee2e6 !important;
                border-radius: 6px !important;
                font-size: 1rem !important;
                transition: all 0.2s ease !important;
            }

            .stTextInput input:focus,
            .stTextArea textarea:focus,
            .stNumberInput input:focus {
                border-color: #3498db !important;
                box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.2) !important;
            }

            /* Botões */
            .stButton button {
                width: 100% !important;
                padding: 0.8rem !important;
                background-color: #2c3e50 !important;
                color: white !important;
                border: none !important;
                border-radius: 6px !important;
                font-weight: 500 !important;
                font-size: 1rem !important;
                transition: all 0.3s ease !important;
            }

            .stButton button:hover {
                background-color: #34495e !important;
                transform: translateY(-2px) !important;
                box-shadow: 0 4px 8px rgba(0,0,0,0.1) !important;
            }

            /* Tabelas */
            .dataframe {
                width: 100% !important;
                margin: 1rem 0 !important;
                border-collapse: collapse !important;
                border-radius: 8px !important;
                overflow: hidden !important;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05) !important;
            }

            .dataframe th {
                background-color: #f8f9fa !important;
                padding: 1rem !important;
                text-align: left !important;
                font-weight: 600 !important;
                color: #2c3e50 !important;
                border-bottom: 2px solid #dee2e6 !important;
            }

            .dataframe td {
                padding: 0.8rem 1rem !important;
                border-bottom: 1px solid #e9ecef !important;
                color: #495057 !important;
            }

            .dataframe tr:hover {
                background-color: #f8f9fa !important;
            }

            /* Mensagens de status */
            .stSuccess, .stInfo, .stWarning, .stError {
                padding: 1rem !important;
                border-radius: 6px !important;
                margin: 1rem 0 !important;
                font-size: 1rem !important;
            }

            /* Layout responsivo */
            @media (max-width: 768px) {
                .pedido-form {
                    padding: 1rem !important;
                }

                .dataframe th,
                .dataframe td {
                    padding: 0.6rem !important;
                    font-size: 0.9rem !important;
                }
            }
        </style>
        """, unsafe_allow_html=True)

    def _mostrar_formulario_pedido(self, pedido_info):
        """Mostra o formulário de pedido para um item específico"""
        st.markdown('<div class="pedido-form">', unsafe_allow_html=True)
        
        # Informações do item
        st.markdown('<div class="pedido-info">', unsafe_allow_html=True)
        st.markdown("#### 📋 Informações do Item")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            **Serial:** {pedido_info['serial']}  
            **Máquina:** {pedido_info['maquina']}  
            **Posto:** {pedido_info['posto']}  
            **Coordenada:** {pedido_info['coordenada']}
            """)
        
        with col2:
            st.markdown(f"""
            **Modelo:** {pedido_info['modelo']}  
            **OT:** {pedido_info['ot']}  
            **Semiacabado:** {pedido_info['semiacabado']}  
            **Pagoda:** {pedido_info['pagoda']}
            """)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Formulário
        with st.form(key=f"pedido_form_{pedido_info['serial']}", clear_on_submit=True):
            st.markdown("#### 👤 Dados do Solicitante")
            
            solicitante = st.text_input(
                "Nome do Solicitante",
                placeholder="Digite seu nome completo",
                key=f"solicitante_{pedido_info['serial']}"
            )
            
            urgente = st.toggle(
                "Esse pedido é urgente?",
                key=f"urgente_{pedido_info['serial']}"
            )
            
            quantidade = st.number_input(
                "Quantidade",
                min_value=1,
                value=1,
                key=f"quantidade_{pedido_info['serial']}"
            )
            
            observacoes = st.text_area(
                "Observações",
                placeholder="Digite aqui observações importantes sobre o pedido (opcional)",
                key=f"observacoes_{pedido_info['serial']}"
            )
            
            # Botão de submit
            submitted = st.form_submit_button("💾 Criar Pedido")
            
            if submitted:
                if not solicitante:
                    st.error("Por favor, informe o nome do solicitante!")
                    return
                
                try:
                    # Criar pedido
                    pedido_info['solicitante'] = solicitante
                    pedido_info['urgente'] = urgente
                    pedido_info['observacoes'] = observacoes
                    pedido_info['quantidade'] = quantidade
                    
                    numero_pedido = self.pedido_controller.salvar_pedido(pedido_info)
                    
                    # Adicionar ao cache com sucesso
                    self.cache_manager.add_to_cache(
                        pedido_info['serial'],
                        'success',
                        f"Pedido {numero_pedido} criado com sucesso!"
                    )
                    
                    st.success(f"✅ Pedido {numero_pedido} criado com sucesso!")
                    
                    # Gerar PDF do pedido
                    from fpdf import FPDF
                    pedido_dict = {
                        'info': {
                            'Numero_Pedido': numero_pedido,
                            'Data': datetime.now().strftime("%d/%m/%Y %H:%M"),
                            'Serial': pedido_info['serial'],
                            'Maquina': pedido_info['maquina'],
                            'Posto': pedido_info['posto'],
                            'Coordenada': pedido_info['coordenada'],
                            'Modelo': pedido_info['modelo'],
                            'OT': pedido_info['ot'],
                            'Semiacabado': pedido_info['semiacabado'],
                            'Pagoda': pedido_info['pagoda'],
                            'Urgente': pedido_info['urgente'],
                            'Solicitante': pedido_info['solicitante'],
                            'Observacoes': pedido_info['observacoes']
                        },
                        'status': 'PENDENTE'
                    }
                    
                    texto = self.formatar_pedido_para_impressao(pedido_dict)
                    pdf = FPDF()
                    pdf.add_page()
                    pdf.set_font("Arial", size=10)
                    pdf.set_auto_page_break(auto=True, margin=15)
                    
                    line_height = 8
                    for linha in texto.split('\n'):
                        if linha.strip():
                            pdf.cell(0, line_height, txt=linha.strip(), ln=True)
                        else:
                            pdf.ln(2)
                    
                    pdf_bytes = pdf.output(dest='S').encode('latin1')
                    st.download_button(
                        label="📥 Baixar PDF do Pedido",
                        data=pdf_bytes,
                        file_name=f"pedido_{numero_pedido}.pdf",
                        mime="application/pdf"
                    )
                    
                    st.rerun()
                    
                except ValueError as ve:
                    # Erro de validação (serial duplicado no mesmo lote)
                    self.cache_manager.add_to_cache(
                        pedido_info['serial'],
                        'error',
                        str(ve)
                    )
                    st.error(str(ve))
                except Exception as e:
                    # Outros erros
                    self.cache_manager.add_to_cache(
                        pedido_info['serial'],
                        'error',
                        f"Erro ao criar pedido: {str(e)}"
                    )
                    st.error(f"Erro ao criar pedido: {str(e)}")
        
        st.markdown('</div>', unsafe_allow_html=True)

    def mostrar_interface(self):
        # Inicializar session_state
        if 'ultimo_codigo' not in st.session_state:
            st.session_state.ultimo_codigo = None
        if 'deve_limpar' not in st.session_state:
            st.session_state.deve_limpar = False
        if 'seriais_processados' not in st.session_state:
            st.session_state.seriais_processados = set()

        # Carregar cache existente
        cache = self.cache_manager.load_cache()
        if cache:
            st.info(f"📋 Existem {len(cache)} leituras em cache")

        # Área de texto para entrada de códigos
        st.markdown("### 📄 Escaneie o código de barras")
        
        # Se deve limpar, redefine o valor antes de criar o widget
        valor_inicial = "" if st.session_state.deve_limpar else st.session_state.get('ultimo_codigo', "")
        if st.session_state.deve_limpar:
            st.session_state.deve_limpar = False
            st.session_state.ultimo_codigo = ""
        
        input_text = st.text_area(
            "",
            value=valor_inicial,
            height=100,
            placeholder="Escaneie ou cole o código de barras aqui",
            key="input_barcode",
            label_visibility="collapsed"
        )

        # Adicionar códigos ao cache ao digitar
        if input_text and input_text != st.session_state.ultimo_codigo:
            st.session_state.ultimo_codigo = input_text
            barcodes = list(set([line.strip() for line in input_text.split('\n') if line.strip()]))
            # Salvar no cache (sem criar pedidos ainda)
            for codigo in barcodes:
                if codigo not in [item['serial'] for item in self.cache_manager.load_cache()]:
                    self.cache_manager.add_to_cache(codigo, 'aguardando', 'Aguardando sincronização')
            st.success(f"{len(barcodes)} código(s) adicionados ao lote para sincronização.")
            st.rerun()

        # Botão para sincronizar pedidos em lote
        if st.button('🚀 Sincronizar Pedidos (Lote)'):
            cache = self.cache_manager.load_cache()
            if not cache:
                st.warning('Nenhum código para sincronizar!')
            else:
                # Buscar dados da aba 'paco' do Google Sheets se disponível
                if hasattr(self.pedido_controller, 'sheets_sync') and self.pedido_controller.sheets_sync and self.pedido_controller.sheets_sync.client:
                    pedidos_paco = self.pedido_controller.carregar_paco_google_sheets()
                    df_paco = pd.DataFrame([p.__dict__ for p in pedidos_paco])
                    df_paco.columns = [str(col).strip().title() for col in df_paco.columns]
                else:
                    df_paco = pd.read_excel(self.pedido_controller.caminho_planilha, sheet_name='Paco', dtype=str)
                    df_paco = df_paco.fillna("")
                    df_paco.columns = [str(col).strip().title() for col in df_paco.columns]
                resultados = []
                pedidos_criados = []
                for item in cache:
                    codigo = item['serial']
                    codigo_norm = str(codigo).strip().upper()
                    pedido_encontrado = None
                    for _, row in df_paco.iterrows():
                        serial = str(row.get('Serial', '')).strip().upper()
                        if serial and serial == codigo_norm:
                            pedido_encontrado = {
                                'serial': str(row.get('Serial', '')).strip(),
                                'maquina': str(row.get('Maquina', '')).strip(),
                                'posto': str(row.get('Posto', '')).strip(),
                                'coordenada': str(row.get('Coordenada', '')).strip(),
                                'modelo': str(row.get('Modelo', '')).strip(),
                                'ot': str(row.get('Ot', '')).strip(),
                                'semiacabado': str(row.get('Semiacabado', '')).strip(),
                                'pagoda': str(row.get('Pagoda', '')).strip()
                            }
                            break
                    if pedido_encontrado:
                        data_atual = datetime.now()
                        pedido_info = {
                            **pedido_encontrado,
                            "solicitante": "Sistema Automático",
                            "observacoes": "",
                            "urgente": "Não",
                            "data": data_atual,
                            "ultima_atualizacao": data_atual
                        }
                        try:
                            numero_pedido = self.pedido_controller.salvar_pedido(pedido_info)
                            if numero_pedido:
                                status = "✅"
                                mensagem = f"Pedido {numero_pedido} criado com sucesso"
                                pedidos_criados.append(numero_pedido)
                            else:
                                status = "❌"
                                mensagem = "Erro ao criar pedido"
                        except Exception as e:
                            status = "❌"
                            mensagem = f"Erro ao criar pedido: {str(e)}"
                    else:
                        status = "❌"
                        mensagem = "Serial não encontrado na planilha"
                    resultados.append({
                        'serial': codigo,
                        'status': status,
                        'mensagem': mensagem
                    })
                # Limpar cache após sincronizar
                self.cache_manager.clear_cache()
                st.markdown('<div class="resultados-container">', unsafe_allow_html=True)
                if pedidos_criados:
                    st.success(f"✅ {len(pedidos_criados)} pedido(s) criado(s) com sucesso!")
                df = pd.DataFrame(resultados)
                df.columns = ["Serial", "Status", "Mensagem"]
                st.dataframe(df, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
                st.session_state.deve_limpar = True
                st.session_state.ultimo_codigo = ""
                st.rerun()

        # Mostrar cache
        st.markdown("### 📋 Lote de Códigos para Sincronizar (Cache)")
        cache_df = pd.DataFrame(self.cache_manager.load_cache())
        if not cache_df.empty:
            st.dataframe(cache_df, use_container_width=True)

    def limpar_codigos_processados(self):
        """Limpa a lista de códigos já processados"""
        if 'codigos_processados' in st.session_state:
            st.session_state.codigos_processados.clear()

    def formatar_pedido_para_impressao(self, pedido: dict) -> str:
        """Formata os detalhes do pedido para impressão"""
        info = pedido['info']
        
        texto = f"""=================================================
                PEDIDO DE REQUISIÇÃO
=================================================
Número: {info['Numero_Pedido']}    Data: {info['Data']}    Status: {pedido['status']}

INFORMAÇÕES DO PRODUTO:
-------------------------------------------------
Serial: {info['Serial']}    Máquina: {info['Maquina']}
Posto: {info['Posto']}    Coordenada: {info['Coordenada']}

DETALHES DO ITEM:
-------------------------------------------------
Modelo: {info['Modelo']}    OT: {info['OT']}
Semiacabado: {info['Semiacabado']}    Pagoda: {info['Pagoda']}

INFORMAÇÕES ADICIONAIS:
-------------------------------------------------
Solicitante: {info['Solicitante']}
Urgente: {"Sim" if info.get('Urgente') == True else "Não"}
Observações: {info.get('Observacoes', '')}

-------------------------------------------------

Assinaturas:

Separador: _____________________________
Coletador: _____________________________

Impresso em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
"""
        return texto

    def __del__(self):
        # Garantir que o lock seja liberado ao encerrar, se foi adquirido
        # Isso é uma tentativa de limpeza, mas pode não ser confiável em todas as situações
        # devido à natureza dos destrutores em Python e como o Streamlit lida com o ciclo de vida.
        # if hasattr(self, 'cache_manager') and hasattr(self.cache_manager, 'release_lock'):
        #     self.cache_manager.release_lock()
        pass