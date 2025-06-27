import tkinter as tk
from tkinter import messagebox, ttk
from utils.sheets_pedidos_sync import SheetsPedidosSync
from datetime import datetime
import platform
import sys
import os

# Função para obter o caminho absoluto do recurso (compatível com PyInstaller)
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class PedidoScannerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Scanner de Pedidos")
        # Ajustar tamanho da janela baseado no sistema operacional
        if platform.system() == 'Linux':
            self.root.geometry("800x400")
        else:
            self.root.geometry("700x370")
        
        self.sheets_sync = SheetsPedidosSync(enable_sheets=True)
        self.leituras = []  # Lista de dicionários: codigo, status, mensagem, hora
        self._build_interface()

    def _build_interface(self):
        # Frame para status da conexão
        self.frame_status = tk.Frame(self.root)
        self.frame_status.pack(fill=tk.X, padx=10, pady=(10, 0))
        self.lbl_status = tk.Label(self.frame_status, text="Conectado ao Google Sheets" if self.sheets_sync.client else "Desconectado", 
                                 fg="green" if self.sheets_sync.client else "red")
        self.lbl_status.pack(side=tk.LEFT, padx=10)

        # Campo para código de barras
        frame_leitura = tk.Frame(self.root)
        frame_leitura.pack(fill=tk.X, padx=10, pady=(10, 0))
        tk.Label(frame_leitura, text="Escaneie o código de barras:").pack(side=tk.LEFT)
        self.codigo_var = tk.StringVar()
        self.codigo_entry = tk.Entry(frame_leitura, textvariable=self.codigo_var, width=40, font=("Arial", 16))
        self.codigo_entry.pack(side=tk.LEFT, padx=5)
        self.codigo_entry.focus()
        self.codigo_entry.bind('<Return>', self.on_leitura)

        # Tabela de leituras
        frame_tabela = tk.Frame(self.root)
        frame_tabela.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 0))
        columns = ("codigo", "status", "mensagem", "hora")
        self.tree = ttk.Treeview(frame_tabela, columns=columns, show="headings", height=10)
        self.tree.heading("codigo", text="Código")
        self.tree.heading("status", text="Status")
        self.tree.heading("mensagem", text="Mensagem")
        self.tree.heading("hora", text="Hora")
        self.tree.column("codigo", width=180)
        self.tree.column("status", width=80)
        self.tree.column("mensagem", width=300)
        self.tree.column("hora", width=100)
        self.tree.pack(fill=tk.BOTH, expand=True)
        # Adicionar tag para sucesso
        self.tree.tag_configure('sucesso', background='#d4fcd4')  # verde claro

    def on_leitura(self, event=None):
        codigo = self.codigo_var.get().strip()
        hora_leitura = datetime.now().strftime("%H:%M:%S")
        
        if not codigo:
            self.add_leitura(codigo, "❌", "Campo vazio", hora_leitura)
            self.codigo_var.set("")
            self.codigo_entry.focus()
            return
        
        # Tentar registrar a leitura e gerar o pedido
        success, message = self.sheets_sync.registrar_leitura_barcode(codigo)
        
        # Adicionar à tabela
        self.add_leitura(
            codigo,
            "✅" if success else "❌",
            message,
            hora_leitura
        )
        
        # Limpar campo e focar
        self.codigo_var.set("")
        self.codigo_entry.focus()

    def add_leitura(self, codigo, status, mensagem, hora):
        self.leituras.append({"codigo": codigo, "status": status, "mensagem": mensagem, "hora": hora})
        # Limitar aos últimos 10
        self.leituras = self.leituras[-10:]
        # Limpar tabela
        for row in self.tree.get_children():
            self.tree.delete(row)
        # Adicionar na tabela
        for leitura in self.leituras:
            tag = 'sucesso' if leitura["status"] == "✅" else ''
            self.tree.insert("", tk.END, values=(
                leitura["codigo"],
                leitura["status"],
                leitura["mensagem"],
                leitura["hora"]
            ), tags=(tag,))

if __name__ == "__main__":
    root = tk.Tk()
    app = PedidoScannerApp(root)
    root.mainloop() 