from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.utils import platform
from datetime import datetime
import json
import os
import pandas as pd
from utils.sheets_pedidos_sync import SheetsPedidosSync
import threading
import time

# Configurar tema claro
Window.clearcolor = (1, 1, 1, 1)  # Fundo branco

# Configurações de arquivos
def get_app_dir():
    if platform == 'android':
        from android.storage import primary_external_storage_path
        directory = os.path.join(primary_external_storage_path(), 'PedidoMobile')
        os.makedirs(directory, exist_ok=True)
        return directory
    return os.path.abspath(".")

CONFIG_FILE = os.path.join(get_app_dir(), "config.json")
PENDENTES_FILE = os.path.join(get_app_dir(), "leituras_pendentes.json")

class PedidoMobileUI(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = dp(10)
        self.spacing = dp(10)
        
        # Inicializar SheetsPedidosSync
        self.sheets_sync = SheetsPedidosSync(enable_sheets=True)
        self.leituras = []
        
        # Criar interface
        self._build_interface()
        
        # Iniciar thread de sincronização
        self.sync_thread = threading.Thread(target=self.sync_pendencias_background, daemon=True)
        self.sync_thread.start()
        
        # Atualizar status inicial
        self.update_pendencias_status()

    def _build_interface(self):
        # Status Bar
        status_bar = BoxLayout(size_hint_y=None, height=dp(30))
        self.url_status = Label(
            text="URL configurada" if self._carregar_url_planilha() else "URL não configurada",
            color=(0, 0.7, 0, 1) if self._carregar_url_planilha() else (0.8, 0, 0, 1)
        )
        self.pendencias_label = Label(text="", color=(0.8, 0.4, 0, 1))
        status_bar.add_widget(self.url_status)
        status_bar.add_widget(self.pendencias_label)
        self.add_widget(status_bar)

        # Campo de entrada com botão de scanner
        input_layout = BoxLayout(size_hint_y=None, height=dp(50))
        self.codigo_input = TextInput(
            hint_text='Escaneie ou digite o código',
            multiline=False,
            font_size=dp(18),
            size_hint_x=0.7,
            background_color=(0.95, 0.95, 0.95, 1),  # Fundo cinza claro
            foreground_color=(0, 0, 0, 1)  # Texto preto
        )
        self.codigo_input.bind(on_text_validate=self.on_leitura)
        
        scan_button = Button(
            text='📷 Scan',
            size_hint_x=0.3,
            background_color=(0.2, 0.6, 1, 1),
            color=(1, 1, 1, 1)  # Texto branco para contraste
        )
        scan_button.bind(on_press=self.iniciar_scanner)
        
        input_layout.add_widget(self.codigo_input)
        input_layout.add_widget(scan_button)
        self.add_widget(input_layout)

        # Lista de leituras
        self.lista_layout = GridLayout(cols=4, spacing=dp(2), size_hint_y=None)
        self.lista_layout.bind(minimum_height=self.lista_layout.setter('height'))
        
        # Headers
        headers = ['Serial', 'Status', 'Mensagem', 'Hora']
        for header in headers:
            self.lista_layout.add_widget(Label(
                text=header,
                size_hint_y=None,
                height=dp(30),
                bold=True,
                color=(0, 0, 0, 1)  # Texto preto
            ))

        # ScrollView para a lista
        scroll = ScrollView(size_hint=(1, 1))
        scroll.add_widget(self.lista_layout)
        self.add_widget(scroll)

        # Botões de ação
        actions_layout = BoxLayout(size_hint_y=None, height=dp(50))
        config_btn = Button(
            text='⚙️ Configurar',
            background_color=(0.9, 0.9, 0.9, 1),  # Cinza claro
            color=(0, 0, 0, 1)  # Texto preto
        )
        config_btn.bind(on_press=self.mostrar_configuracao)
        actions_layout.add_widget(config_btn)
        self.add_widget(actions_layout)

    def _carregar_url_planilha(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                return config.get('sheets_url', '')
            except:
                return ''
        return ''

    def iniciar_scanner(self, instance):
        if platform == 'android':
            from android.permissions import request_permissions, Permission
            request_permissions([Permission.CAMERA])
            
            from pyzbar.pyzbar import decode
            from PIL import Image
            # Aqui você implementaria a lógica do scanner
            # Para o Honeywell, você usaria a API específica deles
            # Este é apenas um exemplo genérico
            try:
                # Código do scanner aqui
                # Quando um código for lido, chame:
                # self.processar_codigo(codigo_lido)
                pass
            except Exception as e:
                self.mostrar_erro(f"Erro no scanner: {str(e)}")

    def processar_codigo(self, codigo):
        self.codigo_input.text = codigo
        self.on_leitura(None)

    def on_leitura(self, instance):
        codigo = self.codigo_input.text.strip()
        hora_leitura = datetime.now().strftime("%H:%M:%S")
        
        if not codigo:
            self.add_leitura(codigo, "❌", "Campo vazio", hora_leitura)
            self.codigo_input.text = ""
            return

        # Salvar localmente
        self.salvar_leitura_pendente(codigo, hora_leitura)
        self.codigo_input.text = ""
        self.update_pendencias_status()

    def salvar_leitura_pendente(self, codigo, hora):
        pendencias = self.carregar_pendencias()
        pendencias.append({"codigo": codigo, "hora": hora})
        with open(PENDENTES_FILE, 'w') as f:
            json.dump(pendencias, f, indent=4)

    def carregar_pendencias(self):
        if os.path.exists(PENDENTES_FILE):
            try:
                with open(PENDENTES_FILE, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []

    def update_pendencias_status(self):
        pendencias = self.carregar_pendencias()
        if pendencias:
            self.pendencias_label.text = f"Pendências: {len(pendencias)}"
            self.pendencias_label.color = (0.8, 0.4, 0, 1)  # Laranja mais suave
        else:
            self.pendencias_label.text = "Sincronizado"
            self.pendencias_label.color = (0, 0.7, 0, 1)  # Verde mais suave

    def sync_pendencias_background(self):
        while True:
            try:
                self.sync_pendencias()
            except Exception as e:
                print(f"Erro na sincronização: {str(e)}")
            time.sleep(5)

    def sync_pendencias(self):
        pendencias = self.carregar_pendencias()
        if not pendencias:
            return

        indices_sucesso = []
        for i, pend in enumerate(pendencias):
            codigo = pend["codigo"]
            hora = pend["hora"]
            
            try:
                # Tentar criar pedido no Google Sheets
                if not self.sheets_sync.client or not self.sheets_sync.SPREADSHEET_URL:
                    continue

                df_paco = self.sheets_sync.get_paco_as_dataframe()
                df_paco.columns = [str(col).strip().title() for col in df_paco.columns]
                
                # Procurar o código na planilha
                codigo_norm = codigo.strip().upper()
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
                    # Criar novo pedido
                    proximo_num = self.sheets_sync.get_proximo_numero_pedido(prefixo="REQ-")
                    numero_pedido = f"REQ-{proximo_num:03d}"
                    
                    novo_pedido = {
                        "Numero_Pedido": numero_pedido,
                        "Data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Serial": pedido_encontrado['serial'],
                        "Maquina": pedido_encontrado['maquina'],
                        "Posto": pedido_encontrado['posto'],
                        "Coordenada": pedido_encontrado['coordenada'],
                        "Modelo": pedido_encontrado['modelo'],
                        "OT": pedido_encontrado['ot'],
                        "Semiacabado": pedido_encontrado['semiacabado'],
                        "Pagoda": pedido_encontrado['pagoda'],
                        "Status": "PENDENTE",
                        "Urgente": "Não",
                        "Ultima_Atualizacao": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Responsavel_Atualizacao": "Pedido Mobile",
                        "Responsavel_Separacao": "",
                        "Data_Separacao": "",
                        "Responsavel_Coleta": "",
                        "Data_Coleta": "",
                        "Solicitante": "Pedido Mobile",
                        "Observacoes": ""
                    }

                    # Preparar DataFrames
                    colunas_pedidos = [
                        "Numero_Pedido", "Data", "Serial", "Maquina", "Posto", "Coordenada",
                        "Modelo", "OT", "Semiacabado", "Pagoda", "Status", "Urgente",
                        "Ultima_Atualizacao", "Responsavel_Atualizacao", "Responsavel_Separacao",
                        "Data_Separacao", "Responsavel_Coleta", "Data_Coleta", "Solicitante",
                        "Observacoes"
                    ]
                    
                    df_pedidos = pd.DataFrame(
                        [[novo_pedido.get(col, "") for col in colunas_pedidos]],
                        columns=colunas_pedidos
                    )
                    
                    df_itens = pd.DataFrame([{
                        "Numero_Pedido": numero_pedido,
                        "Serial": pedido_encontrado['serial'],
                        "Quantidade": 1
                    }])

                    # Salvar no Google Sheets
                    success, message = self.sheets_sync.salvar_pedido_completo(df_pedidos, df_itens)
                    
                    if success:
                        self.add_leitura(
                            codigo,
                            "✅",
                            f"Pedido {numero_pedido} criado!",
                            hora
                        )
                        indices_sucesso.append(i)
                    else:
                        self.add_leitura(
                            codigo,
                            "❌",
                            f"Erro ao sincronizar: {message}",
                            hora
                        )
                else:
                    self.add_leitura(
                        codigo,
                        "❌",
                        "Serial não encontrado",
                        hora
                    )

            except Exception as e:
                self.add_leitura(
                    codigo,
                    "❌",
                    f"Erro: {str(e)}",
                    hora
                )

        # Remover pedidos sincronizados com sucesso
        if indices_sucesso:
            pendencias = [p for i, p in enumerate(pendencias) if i not in indices_sucesso]
            with open(PENDENTES_FILE, 'w') as f:
                json.dump(pendencias, f, indent=4)

        self.update_pendencias_status()

    def add_leitura(self, serial, status, mensagem, hora):
        # Limitar a 10 últimas leituras
        self.leituras = self.leituras[-9:] if len(self.leituras) > 9 else self.leituras
        self.leituras.append({
            "serial": serial,
            "status": status,
            "mensagem": mensagem,
            "hora": hora
        })
        
        # Atualizar UI na thread principal
        Clock.schedule_once(lambda dt: self._update_lista_ui())

    def _update_lista_ui(self):
        # Limpar lista atual (mantendo headers)
        while len(self.lista_layout.children) > 4:
            self.lista_layout.remove_widget(self.lista_layout.children[0])
        
        # Adicionar novas leituras
        for leitura in reversed(self.leituras):
            for valor in [
                leitura["serial"],
                leitura["status"],
                leitura["mensagem"],
                leitura["hora"]
            ]:
                label = Label(
                    text=str(valor),
                    size_hint_y=None,
                    height=dp(30),
                    color=(0, 0.7, 0, 1) if leitura["status"] == "✅" else (0, 0, 0, 1)
                )
                self.lista_layout.add_widget(label)

    def mostrar_configuracao(self, instance):
        # Implementar diálogo de configuração
        pass

    def mostrar_erro(self, mensagem):
        # Implementar exibição de erro
        pass

class PedidoMobileApp(App):
    def build(self):
        return PedidoMobileUI()

if __name__ == '__main__':
    if platform == 'android':
        from android.permissions import request_permissions, Permission
        request_permissions([
            Permission.INTERNET,
            Permission.WRITE_EXTERNAL_STORAGE,
            Permission.READ_EXTERNAL_STORAGE,
            Permission.CAMERA
        ])
    
    PedidoMobileApp().run() 