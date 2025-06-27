import os
import shutil
import platform
import subprocess
import sys
import time

def limpar_diretorios():
    """Limpa os diretórios de build e dist"""
    diretorios = ['build', 'dist']
    for dir_name in diretorios:
        if os.path.exists(dir_name):
            try:
                shutil.rmtree(dir_name)
            except PermissionError:
                print(f"Aguardando liberação do diretório {dir_name}...")
                time.sleep(2)  # Aguarda 2 segundos
                try:
                    shutil.rmtree(dir_name)
                except PermissionError:
                    print(f"Não foi possível limpar o diretório {dir_name}. Tentando continuar mesmo assim...")

def criar_spec_windows():
    """Cria o arquivo .spec para Windows"""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['pedido_local_desktop.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('config.json', '.'),
        ('utils', 'utils'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='pedido_local_desktop',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
'''
    with open('pedido_local_desktop_windows.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)

def criar_spec_linux():
    """Cria o arquivo .spec para Linux"""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['pedido_local_desktop.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('config.json', '.'),
        ('utils', 'utils'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='pedido_local_desktop',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
'''
    with open('pedido_local_desktop_linux.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)

def criar_pacote_windows():
    """Cria o pacote de distribuição para Windows"""
    os.makedirs('pedido_local_windows', exist_ok=True)
    
    executavel = 'dist/pedido_local_desktop.exe'
    if os.path.exists(executavel):
        shutil.copy(executavel, 'pedido_local_windows/')
    else:
        print(f"Erro: Executável não encontrado em {executavel}")
        return False

    shutil.copy('config.json', 'pedido_local_windows/')
    
    readme_content = '''# Pedido Local Windows

## Instalação
1. Copie a pasta 'pedido_local_windows' para seu computador
2. Execute pedido_local_desktop.exe

## Observações
- O aplicativo criará automaticamente a pasta de configurações
- O arquivo config.json deve estar na mesma pasta do executável
'''
    with open('pedido_local_windows/README.txt', 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    shutil.make_archive('pedido_local_windows', 'zip', 'pedido_local_windows')
    return True

def criar_pacote_linux():
    """Cria o pacote de distribuição para Linux"""
    os.makedirs('pedido_local_linux', exist_ok=True)
    
    executavel = 'dist/pedido_local_desktop'
    if os.path.exists(executavel):
        shutil.copy(executavel, 'pedido_local_linux/')
    else:
        print(f"Erro: Executável não encontrado em {executavel}")
        return False

    shutil.copy('config.json', 'pedido_local_linux/')
    
    readme_content = '''# Pedido Local Linux

## Instalação
1. Copie a pasta 'pedido_local_linux' para seu computador
2. Abra o terminal na pasta
3. Execute: chmod +x pedido_local_desktop
4. Execute: ./pedido_local_desktop

## Observações
- O aplicativo criará automaticamente a pasta ~/.pedido_local para armazenar configurações
- O arquivo config.json deve estar na mesma pasta do executável
'''
    with open('pedido_local_linux/README.txt', 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    shutil.make_archive('pedido_local_linux', 'gztar', 'pedido_local_linux')
    return True

def main():
    print("Limpando diretórios anteriores...")
    limpar_diretorios()

    print("Criando arquivos .spec...")
    criar_spec_windows()
    criar_spec_linux()

    print("\nCompilando executáveis...")
    try:
        # Compilar para Windows
        print("\nCompilando para Windows...")
        cmd_windows = [
            'pyinstaller',
            '--noconfirm',  # Não pedir confirmação
            '--onefile',
            '--windowed',
            '--add-data', 'config.json;.',
            '--add-data', 'utils;utils',
            'pedido_local_desktop.py'
        ]
        subprocess.run(cmd_windows, check=True)
        
        print("Criando pacote Windows...")
        if criar_pacote_windows():
            print("Pacote Windows criado com sucesso!")
        
        # Compilar para Linux
        print("\nCompilando para Linux...")
        cmd_linux = [
            'pyinstaller',
            '--noconfirm',  # Não pedir confirmação
            '--onefile',
            '--windowed',
            '--add-data', 'config.json:.',
            '--add-data', 'utils:utils',
            'pedido_local_desktop.py'
        ]
        subprocess.run(cmd_linux, check=True)
        
        print("Criando pacote Linux...")
        if criar_pacote_linux():
            print("Pacote Linux criado com sucesso!")
        
        print("\nBuild concluído com sucesso!")
        print("Arquivos gerados:")
        print("- pedido_local_windows.zip (para Windows)")
        print("- pedido_local_linux.tar.gz (para Linux)")
        
    except subprocess.CalledProcessError as e:
        print(f"\nErro ao compilar: {e}")
        return

if __name__ == "__main__":
    main() 