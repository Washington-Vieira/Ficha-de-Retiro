# app.py
import streamlit as st
import pandas as pd
from io import StringIO

st.set_page_config(page_title="Leitor de Códigos de Barras", layout="centered")

st.title("📦 Leitura de Códigos de Barras (Modo Lote)")

# Área de texto para simular entrada de arquivo TXT
st.subheader("📄 Inserir códigos de barras (um por linha)")
input_text = st.text_area("Cole os códigos aqui:", height=300, placeholder="1234567890123\n9876543210987\n...")

if input_text:
    # Simula leitura de arquivo TXT, linha por linha
    string_io = StringIO(input_text)
    barcodes = [line.strip() for line in string_io if line.strip()]

    if barcodes:
        st.success(f"✅ {len(barcodes)} código(s) de barras lido(s).")
        df = pd.DataFrame(barcodes, columns=["Código de Barras"])
        st.dataframe(df, use_container_width=True)

        # Botão para exportar como CSV (simulando salvar um arquivo processado)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Baixar como CSV",
            data=csv,
            file_name="codigos_lidos.csv",
            mime="text/csv"
        )
    else:
        st.warning("Nenhum código válido encontrado.")
