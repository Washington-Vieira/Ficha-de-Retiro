FROM arm32v7/python:3.11-slim

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libpq-dev \
    libffi-dev \
    libssl-dev \
    zlib1g-dev \
    libbz2-dev \
    libreadline-dev \
    libsqlite3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar arquivos do projeto
COPY . .

# Atualizar pip
RUN pip install --upgrade pip

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir pyinstaller

# Compilar o executável
RUN pyinstaller --clean --onefile \
    --add-data "config.json:." \
    --add-data "utils:utils" \
    --name pedido_local_desktop \
    pedido_local_desktop.py

# Criar diretório de distribuição
RUN mkdir -p pedido_local_linux
RUN cp dist/pedido_local_desktop pedido_local_linux/
RUN cp config.json pedido_local_linux/

# Criar README
RUN echo "# Pedido Local Linux (Raspberry Pi)\n\n## Instalação\n1. Copie a pasta 'pedido_local_linux' para seu Raspberry Pi\n2. Abra o terminal na pasta\n3. Execute: chmod +x pedido_local_desktop\n4. Execute: ./pedido_local_desktop\n\n## Observações\n- O aplicativo criará automaticamente a pasta ~/.pedido_local para armazenar configurações\n- O arquivo config.json deve estar na mesma pasta do executável" > pedido_local_linux/README.txt

# Criar arquivo compactado
RUN tar -czf pedido_local_linux.tar.gz pedido_local_linux
