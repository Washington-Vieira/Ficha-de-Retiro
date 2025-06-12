# Sistema de Gestão de Pedidos

Sistema desenvolvido em Python com Streamlit para gerenciamento de pedidos de requisição, integrado ao Google Sheets e com suporte a importação/exportação via Excel.

---

## Requisitos

- Python 3.10+ (recomendado)
- Conta Google com permissão de edição na planilha
- Credenciais de serviço do Google (JSON)
- [Streamlit](https://streamlit.io/)
- [gspread](https://gspread.readthedocs.io/)
- Outras dependências listadas em `requirements.txt`

---

## Instalação

1. **Clone este repositório**
   ```bash
   git clone https://github.com/SEU_USUARIO/pedido.git
   cd pedido
   ```

2. **Crie e ative o ambiente virtual**
   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # Linux/Mac
   source .venv/bin/activate
   ```

3. **Instale as dependências**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure as credenciais do Google Sheets**
   - Crie um arquivo `secrets.toml` em `.streamlit/` com:
     ```
     [general]
     sheets_url = "URL_DA_SUA_PLANILHA"
     sheets_credentials = 'CONTEUDO_JSON_DAS_CREDENCIAIS'
     ```
   - Compartilhe a planilha com o e-mail do campo `client_email` das credenciais.

---

## Estrutura do Projeto

```
.
├── app.py                      # Aplicação principal Streamlit
├── pedido_local_desktop.py     # Versão desktop do aplicativo
├── pedido_local.py            # Módulo de operações locais
├── requirements.txt           # Dependências do projeto
├── config.json               # Configurações do sistema
├── runtime.txt              # Configuração do runtime
├── .streamlit/             # Configurações do Streamlit
│   └── secrets.toml        # Credenciais e configurações sensíveis
├── models/                 # Modelos de dados
│   └── pedido.py          # Modelo de dados do pedido
├── views/                 # Interface do usuário
│   ├── configuracoes_view.py
│   ├── pedido_form_view.py
│   ├── pedido_view.py
│   ├── pedido_historico_view.py
│   └── pedido_dashboard_gerencial.py
├── controllers/          # Lógica de negócios
│   └── pedido_controller.py
├── utils/               # Utilitários
│   ├── sheets_pedidos_sync.py
│   └── sheets_sync.py
├── pedidos/            # Armazenamento local
│   └── (backups e arquivos locais)
├── dist/              # Arquivos de distribuição
├── build/            # Arquivos de build
└── .devcontainer/   # Configurações do container de desenvolvimento
```

---

## Componentes do Sistema

### 1. Aplicação Web (Streamlit)
- `app.py`: Aplicação principal com interface web
- Interface responsiva
- Integração com Google Sheets
- Sistema de autenticação e autorização

### 2. Aplicação Desktop
- `pedido_local_desktop.py`: Versão desktop do sistema
- Funcionalidades offline
- Sincronização automática quando online
- Interface nativa do sistema

### 3. Modelos de Dados
- Estrutura de dados para pedidos
- Validação de dados
- Persistência local e remota

### 4. Controllers
- Lógica de negócios
- Processamento de pedidos
- Sincronização de dados
- Validações e regras de negócio

### 5. Views
- Interface do usuário
- Formulários de pedidos
- Visualização de histórico
- Dashboard gerencial
- Configurações do sistema

### 6. Utilitários
- Sincronização com Google Sheets
- Backup de dados
- Importação/Exportação
- Funções auxiliares

---

## Funcionalidades

### 1. Gestão de Pedidos
- Criação e edição de pedidos
- Visualização e filtro de pedidos
- Atualização de status
- Histórico completo

### 2. Integração
- Sincronização com Google Sheets
- Importação via Excel
- Exportação de dados
- Backup automático

### 3. Interface
- Dashboard gerencial
- Formulários intuitivos
- Filtros 
- Visualização de histórico

### 4. Segurança
- Autenticação de usuários
- Backup automático
- Validação de dados
- Log de operações

---

## Fluxo de Operação

### 1. Configuração Inicial
- Configuração do ambiente
- Definição de credenciais
- Importação de dados iniciais

### 2. Operação Diária
- Criação de pedidos
- Atualização de status
- Sincronização de dados
- Backup automático

### 3. Manutenção
- Atualização de localizações
- Backup de dados
- Limpeza de registros
- Otimização do sistema

---

## Dicas e Boas Práticas

1. **Backup**
   - Mantenha backups regulares
   - Verifique a sincronização
   - Monitore o espaço em disco

2. **Performance**
   - Limpe dados antigos
   - Otimize consultas
   - Monitore uso de recursos

3. **Segurança**
   - Mantenha credenciais seguras
   - Atualize dependências
   - Monitore logs

4. **Desenvolvimento**
   - Siga padrões de código
   - Documente alterações
   - Teste novas funcionalidades

---

## Suporte e Manutenção

- Documentação atualizada
- Suporte técnico
- Atualizações regulares
- Correção de bugs

---

## Licença

MIT
# Ficha-de-Retiro
# Ficha-de-Retiro
# Ficha-de-Retiro
