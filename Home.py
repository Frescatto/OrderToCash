# homepage.py
import streamlit as st
import os
import sys

st.set_page_config(
    page_title="Order to Cash - Unificado", # Título que aparece na aba do navegador
    page_icon="📊", # Ícone que aparece na aba do navegador
    layout="wide", # Layout expandido para ocupar mais espaço
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': 'Aplicação Order to Cash Unificada'
    }
)

# Esconder as páginas da barra lateral e limpar o layout
st.markdown("""
<style>
    /* Esconder o menu principal e o rodapé */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Esconder o controle de colapso da barra lateral */
    [data-testid="collapsedControl"] {
        display: none
    }
    
    /* Esconder os links para outras páginas na barra lateral */
    section[data-testid='stSidebar'] .css-1d391kg,
    section[data-testid='stSidebar'] .css-1siy2j7,
    section[data-testid='stSidebar'] .css-1wrcr25,
    section[data-testid='stSidebar'] .css-1avcm0n,
    section[data-testid='stSidebar'] .css-1qrvfrg {
        display: none !important;
    }
    
    /* Esconder todos os elementos que começam com 'OrderToCash' ou 'Etapa' ou 'Timeline' */
    section[data-testid='stSidebar'] a[href*="OrderToCash"],
    section[data-testid='stSidebar'] a[href*="Etapa"],
    section[data-testid='stSidebar'] a[href*="Timeline"] {
        display: none !important;
    }
    
    /* Centralizar imagens na barra lateral */
    [data-testid=stSidebar] [data-testid=stImage]{
        text-align: center;
        display: block;
        margin-left: auto;
        margin-right: auto;
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# Redirecionar para a página unificada
st.title("TI - Frescatto")
st.write("Order to Cash - Processo Unificado")

st.markdown(
    """
    Esta aplicação unifica o processo Order to Cash em uma única interface, permitindo visualizar todas as etapas do processo:

    - **📊 Visão Geral:** Visão completa do processo Order to Cash.
    - **📈 Etapa 1 - Remessa:** Fluxo da geração do pedido até associação da remessa.
    - **📉 Etapa 2 - Item:** Fluxo da associação da remessa até a preparação do item (PFA).
    - **📋 Etapa 3 - Título:** Fluxo da preparação do item (PFA) até a emissão do título (TCR).
    """
)

# Botão para acessar a versão unificada
if st.button("Acessar Versão Unificada", type="primary"):
    # Obter o caminho do script atual
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Construir o caminho para o script unificado
    unified_script = os.path.join(current_dir, "OrderToCash_Unificado.py")
    
    # Executar o script unificado
    os.system(f"{sys.executable} -m streamlit run {unified_script}")

st.info("💡 Clique no botão acima para acessar a versão unificada do Order to Cash, que busca os dados uma única vez e apresenta todas as etapas em uma interface otimizada.")