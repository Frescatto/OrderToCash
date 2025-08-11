# homepage.py
import streamlit as st

st.set_page_config(
    page_title="Timeline", # Título que aparece na aba do navegador
    page_icon="📊", # Ícone que aparece na aba do navegador
    layout="wide" # Layout expandido para ocupar mais espaço
)

st.title("TI - Frescatto")
st.write("Timeline do processo de pedidos")

st.markdown(
    """
    Esta aplicação unifica três diferentes etapas de geração de gráficos, cada uma focada em um conjunto específico de dados ou análises:

    - **📊 Etapa 1:** Fluxo da geração do pedido até associação da remessa.
    - **📈 Etapa 2:** Fluxo da associação da remessa até a preparação do item (PFA).
    - **📉 Etapa 3:** Fluxo da preparação do item (PFA) até a emissão do título (TCR).

    Use o menu de navegação à esquerda para explorar cada seção e visualizar os respectivos gráficos.
    """
)

# Você pode adicionar mais conteúdo aqui, como links, imagens, etc.
st.info("💡 Dica: O menu de navegação está à esquerda. Se não o vir, clique na seta no canto superior esquerdo da tela.")