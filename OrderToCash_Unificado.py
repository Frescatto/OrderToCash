import streamlit as st
import requests
import pandas as pd
import numpy as np
import plotly.express as px
import xml.etree.ElementTree as ET
from datetime import datetime
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configuração da página
st.set_page_config(
    page_title="Order to Cash",
    page_icon="📊",
    layout="wide"
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

# --- INICIALIZAÇÃO E FUNÇÃO DE CARREGAMENTO DE DADOS ---
if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame()

@st.cache_data(show_spinner="Buscando dados...")
def fetch_data(data, usar_arquivo_local=False, usar_xls_local=False, usar_webservice_wmw=False):
    if usar_xls_local:
        try:
            # Usar o arquivo Excel local
            df = pd.read_excel("dados.xlsx")
            
            # Criar as colunas TIMESTAMP combinando data e hora
            # Mapeamento correto para arquivo Excel (note os espaços extras nas colunas)
            timestamp_map = {
                ('DATA GERACAO', 'HORA GERACAO DO PEDIDO'): 'TIMESTAMP PEDIDO',
                ('DATA DE EMISSAO DA NOTA FISCAL', 'HORA GERACAO DA NOTA FISCAL'): 'TIMESTAMP REMESSA',
                ('DATA DA SAÍDA DAS MERCADORIAS ', 'HORA DA SAÍDA DAS MERCADORIAS '): 'TIMESTAMP ITEM',
                ('DATA GERACAO DA NOTA FISCAL', 'HORA GERACAO DA NOTA FISCAL'): 'TIMESTAMP NF',
                ('DATA ENTRADA DO TITULO', 'HORA GERACAO DO REGISTRO'): 'TIMESTAMP TITULO'
            }
            
            # Converter colunas de data para datetime
            colunas_data = [
                'DATA GERACAO', 'DATA DE EMISSAO DA NOTA FISCAL', 'DATA DA SAÍDA DAS MERCADORIAS ', 
                'DATA GERACAO DA NOTA FISCAL', 'DATA ENTRADA DO TITULO'
            ]
            
            for col in colunas_data:
                if col in df.columns:
                    # Substituir datas problemáticas por NaN antes da conversão
                    df[col] = df[col].replace(['31/12/1900', '1900-12-31', '', ' '], pd.NaT)
                    # Remover espaços em branco
                    df[col] = df[col].astype(str).str.strip()
                    # Substituir 'nan' string por NaT
                    df[col] = df[col].replace('nan', pd.NaT)
                    df[col] = pd.to_datetime(df[col], errors='coerce', dayfirst=True)
                    # Substituir datas de 1900 por NaT
                    df.loc[df[col].dt.year == 1900, col] = pd.NaT
            
            # Converter colunas de hora para time
            colunas_hora = [
                'HORA GERACAO DO PEDIDO', 'HORA GERACAO DA NOTA FISCAL', 'HORA DA SAÍDA DAS MERCADORIAS ',
                'HORA GERACAO DO REGISTRO'
            ]
            
            for col in colunas_hora:
                if col in df.columns:
                    # Substituir valores problemáticos por NaN antes da conversão
                    df[col] = df[col].replace([':', '00:00', '00:00:00', '', ' '], pd.NaT)
                    # Remover espaços em branco
                    df[col] = df[col].astype(str).str.strip()
                    # Substituir 'nan' string por NaT
                    df[col] = df[col].replace('nan', pd.NaT)
                    df[col] = pd.to_datetime(df[col], format='%H:%M:%S', errors='coerce').dt.time
            
            # Criar timestamps combinando data e hora
            for (data_col, hora_col), ts_col in timestamp_map.items():
                if data_col in df.columns and hora_col in df.columns:
                    df[ts_col] = df.apply(
                        lambda row: combinar_data_hora(row[data_col], row[hora_col]),
                        axis=1
                    )
            
            st.success("Dados carregados do arquivo Excel local com sucesso!")
            return df
        except Exception as e:
            st.error(f"Erro ao ler o arquivo Excel local: {e}")
            return pd.DataFrame()
    elif usar_arquivo_local:
        try:
            # Usar o arquivo XML local
            with open("response.xml", "r", encoding="utf-8") as file:
                xml_content = file.read()
            st.success("Dados carregados do arquivo XML local com sucesso!")
            root = ET.fromstring(xml_content)
        except Exception as e:
            st.error(f"Erro ao ler o arquivo XML local: {e}")
            return pd.DataFrame()
    elif usar_webservice_wmw:
        # Usar o webservice Senior (Timeline.py)
        url = os.getenv('WEBSERVICE_URL')
        user = os.getenv('WEBSERVICE_USER')
        password = os.getenv('WEBSERVICE_PASSWORD')
        
        # Verificar se as variáveis de ambiente foram carregadas
        if not all([url, user, password]):
            st.error("Erro: Credenciais do webservice não encontradas. Verifique o arquivo .env")
            return pd.DataFrame()
        
        headers = {
            "SOAPAction": "#POST",
            "Content-type": "text/xml",
            "Accept": "application/xml"
        }
        body = f"""<?xml.xml version="1.0" encoding="ISO-8859-1"?>
        <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ser="http://services.senior.com.br">
            <soapenv:Header/>
            <soapenv:Body>
                <ser:timeline>
                    <user>{user}</user>
                    <password>{password}</password>
                    <encryption>0</encryption>
                    <parameters>
                        <data>'{data}'</data>
                    </parameters>
                </ser:timeline>
            </soapenv:Body>
        </soapenv:Envelope>"""

        try:
            response = requests.post(url, headers=headers, data=body)
            
            if response.status_code == 200:
                st.success("Dados carregados do webservice Senior com sucesso!")
                root = ET.fromstring(response.text)
            else:
                st.error(f"Erro ao buscar os dados do webservice Senior: Código de status {response.status_code}")
                return pd.DataFrame()
        except requests.exceptions.RequestException as e:
            st.error(f"Erro de conexão com webservice Senior: {e}")
            return pd.DataFrame()
    else:
        # Usar o webservice principal
        url = "https://ocweb02s1p.seniorcloud.com.br:31201/g5-senior-services/sapiens_Synccom_frescatto_bi"
        user = "felipe.martins"
        password = "Canetaazul03"
        
        headers = {
            "SOAPAction": "#POST",
            "Content-type": "text/xml",
            "Accept": "application/xml"
        }
        body = f"""<?xml.xml version="1.0" encoding="ISO-8859-1"?>
        <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ser="http://services.senior.com.br">
            <soapenv:Header/>
            <soapenv:Body>
                <ser:timeline>
                    <user>{user}</user>
                    <password>{password}</password>
                    <encryption>0</encryption>
                    <parameters>
                        <data>'{data}'</data>
                    </parameters>
                </ser:timeline>
            </soapenv:Body>
        </soapenv:Envelope>"""

        try:
            response = requests.post(url, headers=headers, data=body)
            
            if response.status_code == 200:
                st.success("Dados carregados do webservice com sucesso!")
                root = ET.fromstring(response.text)
            else:
                st.error(f"Erro ao buscar os dados: Código de status {response.status_code}")
                return pd.DataFrame()
        except requests.exceptions.RequestException as e:
            st.error(f"Erro de conexão: {e}")
            return pd.DataFrame()
    
    # Processamento do XML para ambos os casos (local ou webservice)
    namespaces = {
        'S': "http://schemas.xmlsoap.org/soap/envelope/",
        'ns2': "http://services.senior.com.br",
        'xsi': "http://www.w3.org/2001/XMLSchema-instance"
    }
    
    retorno_elements = root.findall('.//ns2:timelineResponse/result/retorno', namespaces)
    
    if retorno_elements:
        all_data = []
        for retorno_item in retorno_elements:
            data_dict = {}
            for child in retorno_item:
                tag_name = child.tag.split('}')[-1]
                is_nil = child.attrib.get(f"{{{namespaces['xsi']}}}nil") == 'true'
                data_dict[tag_name] = None if is_nil else child.text
            all_data.append(data_dict)
        
        df = pd.DataFrame(all_data) 
        
        mapeamento_nomes = {
                    'CFilial': 'FILIAL',
                    'CPedido': 'PEDIDO',
                    'CDataEmissaoPedido': 'DATA EMISSAO PEDIDO',
                    'CHoraEmissaoPedido': 'HORA EMISSAO PEDIDO',
                    'CDataAssRemessa': 'DATA ASS REMESSA',
                    'CHoraAssRemessa': 'HORA ASS REMESSA',
                    'CDataPrepItem': 'DATA PREPARACAO DO ITEM',
                    'CHoraPrepItem': 'HORA PREPARACAO DO ITEM',
                    'CDataGerNF': 'DATA GERACAO NF',
                    'CHoraGerNF': 'HORA GERACAO NF',
                    'CDataGerTCR': 'DATA GERACAO DO REGISTRO',
                    'CHoraGerTCR': 'HORA GERACAO DO REGISTRO',
                    'CSituacaoPedido': 'SITUACAO DO PEDIDO',
                    'CPedidoBloqueado': 'PEDIDO BLOQUEADO',
                    'CUsuarioBloqPedido': 'USUARIO BLOQ PEDIDO',
                    'CDataBloqueio': 'DATA DO BLOQUEIO',
                    'CObservacaoPedido': 'OBSERVACAO DO PEDIDO',
                    'CNumeroNF': 'N° NOTA FISCAL',
                    'CInicioFaturamento': 'INICIO FATURAMENTO',
                    'CFimFaturamento': 'FIM FATURAMENTO',
                    'CCodigoProduto': 'CODIGO PRODUTO',
                    'CSituacaoPFA': 'SITUACAO PFA',
                    'CBloqPFA': 'BLOQUEIO PFA',
                    'CSituacaoFAT': 'SITUACAO FAT',
                    'CSituacaoCarga': 'SITUACAO CARGA',
                    'CSituacaoNFV': 'SITUACAO NFV',
                    'CNFVBloqueio': 'NFV BLOQUEIO',
                    'CDataGeracaoNF': 'DATA GERACAO DA NOTA FISCAL',
                    'CHoraGeracaoNF': 'HORA GERACAO DA NOTA FISCAL',
                    'CNumeroTitulo': 'N° TITULO',
                    'CVencOrigTitulo': 'VENCIMENTO ORIGINAL DO TITULO',
                    'CSituacaoTitulo': 'SITUACAO DO TITULO'
                }
                
        df = df.rename(columns=mapeamento_nomes)
        
        # Criar timestamps combinando data e hora usando a abordagem do Timeline.py
        timestamp_map = {
            ('DATA EMISSAO PEDIDO', 'HORA EMISSAO PEDIDO'): 'TIMESTAMP PEDIDO',
            ('DATA ASS REMESSA', 'HORA ASS REMESSA'): 'TIMESTAMP REMESSA',
            ('DATA PREPARACAO DO ITEM', 'HORA PREPARACAO DO ITEM'): 'TIMESTAMP ITEM',
            ('DATA GERACAO NF', 'HORA GERACAO NF'): 'TIMESTAMP NF',
            ('DATA GERACAO DA NOTA FISCAL', 'HORA GERACAO DA NOTA FISCAL'): 'TIMESTAMP NF2',
            ('DATA GERACAO DO REGISTRO', 'HORA GERACAO DO REGISTRO'): 'TIMESTAMP TITULO'
        }
        
        for (data_col, hora_col), ts_col in timestamp_map.items():
            if data_col in df.columns and hora_col in df.columns:
                # Substituir valores problemáticos nas strings
                df[data_col] = df[data_col].replace(['31/12/1900', '', ' ', 'nan'], np.nan)
                df[hora_col] = df[hora_col].replace([':', '00:00', '00:00:00', '', ' ', 'nan'], np.nan)
                
                # Combinar data e hora como string, tratando valores nulos
                def combinar_strings(row):
                    data_str = row[data_col]
                    hora_str = row[hora_col]
                    
                    # Se qualquer um for nulo, retornar NaT
                    if pd.isna(data_str) or pd.isna(hora_str):
                        return pd.NaT
                    
                    # Se hora for apenas ":", retornar NaT
                    if str(hora_str).strip() == ":":
                        return pd.NaT
                    
                    # Combinar as strings
                    combined = f"{data_str} {hora_str}"
                    
                    # Tentar converter com formato %d/%m/%Y %H:%M:%S
                    try:
                        return pd.to_datetime(combined, format='%d/%m/%Y %H:%M:%S')
                    except:
                        # Tentar formato %d/%m/%Y %H:%M
                        try:
                            return pd.to_datetime(combined, format='%d/%m/%Y %H:%M')
                        except:
                            return pd.NaT
                
                df[ts_col] = df.apply(combinar_strings, axis=1)
                
                # Substituir datas de 1900 por NaT
                df.loc[df[ts_col].dt.year == 1900, ts_col] = pd.NaT
        
        # Aplicar mapeamentos para códigos
        mapeamento_situacao_pfa = {
            '1': 'Em Analise Credito',
            '2': 'Em Preparação',
            '3': 'Para Faturar',
            '4': 'Faturada',
            '5': 'Em Conferencia',
            '6': 'Aguardando Integração WMS',
            '8': 'Sem Estoque',
            '9': 'Cancelada'
        }

        mapeamento_situacao_carga = {
            'A': 'Aberto',
            'F': 'Fechado'
        }

        mapeamento_situacao_nfv = {
            '1': 'Digitada',
            '2': 'Fechada',
            '3': 'Cancelada',
            '4': 'Documento Fiscal Emitido (Saida)',
            '5': 'Aguardando Fechamento (Pos Saida)',
            '6': 'Aguardando Integração WMS',
            '7': 'Digitada Integração',
            '8': 'Agrupada'
        }
        
        mapeamento_situacao_tcr = {
            'AO': 'Aberto ao Órgão de Proteção ao Crédito',
            'AN': 'Aberto Negociação',
            'AA': 'Aberto Advogado',
            'AB': 'Aberto Normal',
            'AC': 'Aberto Cartório',
            'AE': 'Aberto Encontro de Contas',
            'AI': 'Aberto Impostos',
            'AJ': 'Aberto Retorno Jurídico',
            'AP': 'Aberto Protestado',
            'AR': 'Aberto Representante',
            'AS': 'Aberto Suspenso',
            'AV': 'Aberto Gestão de Pessoas',
            'AX': 'Aberto Externo',
            'CA': 'Cancelado',
            'CE': 'Aberto CE (Preparação Cobrança Escritural)',
            'CO': 'Aberto Cobrança',
            'LQ': 'Liquidado Normal',
            'LC': 'Liquidado Cartório',
            'LI': 'Liquidado Impostos',
            'LM': 'Liquidado Compensado',
            'LO': 'Liquidado Cobrança',
            'LP': 'Liquidado Protestado',
            'LS': 'Liquidado Substituído',
            'LV': 'Liquidado Gestão de Pessoas',
            'LX': 'Liquidado Externo',
            'PE': 'Aberto PE (Pagamento Eletrônico)'
        }
        
        # Aplicar mapeamentos
        if 'SITUACAO PFA' in df.columns:
            df['SITUACAO PFA'] = df['SITUACAO PFA'].map(mapeamento_situacao_pfa)
        if 'SITUACAO CARGA' in df.columns:
            df['SITUACAO CARGA'] = df['SITUACAO CARGA'].map(mapeamento_situacao_carga)
        if 'SITUACAO NFV' in df.columns:
            df['SITUACAO NFV'] = df['SITUACAO NFV'].map(mapeamento_situacao_nfv)
        if 'SITUACAO DO TITULO' in df.columns:
            df['SITUACAO TCR'] = df['SITUACAO DO TITULO'].map(mapeamento_situacao_tcr)
        
        return df
    else:
        st.warning("Nenhum dado encontrado na resposta do XML. Verifique se o caminho da busca está correto.")
        return pd.DataFrame()

# Função auxiliar para combinar data e hora, lidando com nulos
def combinar_data_hora(data, hora):
    if pd.isna(data) or pd.isna(hora): # Verifica se data OU hora são nulas
        return pd.NaT # Retorna NaT (Not a Time) se alguma for nula
    
    # Verificar se hora é apenas ":" (dois pontos) que vem do XML
    if isinstance(hora, str) and hora.strip() == ":":
        return pd.NaT
    
    try:
        # Combina o ano, mês, dia da data com hora, minuto, segundo da hora
        return pd.to_datetime(f"{data.year}-{data.month}-{data.day} {hora.hour}:{hora.minute}:{hora.second}")
    except:
        return pd.NaT # Retorna NaT se houver algum erro inesperado na combinação

# --- INTERFACE DO STREAMLIT ---
# Título da página
st.title("📊 Order to Cash - Análise de Pedidos")
st.markdown("---")

# Sidebar para navegação e configurações
st.sidebar.title("⚙️ Configurações")

# Navegação entre etapas
st.sidebar.subheader("📊 Navegação")
etapa_selecionada = st.sidebar.radio(
    "Selecione a etapa:",
    ["Visão Geral", "Etapa 1 - Remessa", "Etapa 2 - Item", "Etapa 3 - Título"]
)

# Filtros de data
st.sidebar.subheader("📅 Filtro por Data")
data_input = st.sidebar.text_input("Digite a data (formato DD/MM/AAAA):", value="19/06/2025")

# Opções para escolher a fonte de dados
st.sidebar.subheader("📂 Fonte de Dados")
usar_arquivo_local = st.sidebar.checkbox("Usar arquivo XML local (response.xml)", value=False, 
                                help="Marque esta opção para usar o arquivo response.xml local em vez de fazer requisições ao webservice.")
usar_xls_local = st.sidebar.checkbox("Usar arquivo Excel local (dados.xlsx)", value=False, 
                            help="Marque esta opção para usar o arquivo dados.xlsx local com dados pré-processados.")
usar_webservice_wmw = st.sidebar.checkbox("Usar webservice Senior", value=False, 
                                 help="Marque esta opção para buscar dados do webservice Senior.")

if st.sidebar.button("🔄 Buscar Dados", type="primary"):
    if usar_xls_local:
        st.session_state.df = fetch_data(data_input, False, True, False)
    elif usar_arquivo_local:
        st.session_state.df = fetch_data(data_input, True, False, False)
    elif usar_webservice_wmw:
        st.session_state.df = fetch_data(data_input, False, False, True)
    elif data_input:
        st.session_state.df = fetch_data(data_input, False, False, False)
    else:
        st.warning("Por favor, digite uma data para buscar os dados ou selecione uma das opções de arquivo local.")

# --- PROCESSAMENTO DOS DADOS ---
if 'df' in st.session_state and not st.session_state.df.empty:
    df = st.session_state.df.copy()
    
    # Filtros de Filial no sidebar
    st.sidebar.header("Filtros")
    
    filiais_brutas = df['FILIAL'].unique()
    filiais_disponiveis = [filial for filial in filiais_brutas if pd.notna(filial)]
    
    if filiais_disponiveis:
        filiais_disponiveis.insert(0, "TODOS")

    filiais_selecionadas = st.sidebar.multiselect(
        "Selecione a(s) Filial(is):",
        options=filiais_disponiveis,
        default=filiais_disponiveis[1:] if "TODOS" in filiais_disponiveis else filiais_disponiveis
    )
    
    if not filiais_selecionadas:
        st.warning("Nenhuma filial selecionada. Por favor, ajuste os filtros.")
        st.stop()

    if "TODOS" in filiais_selecionadas:
        filiais_para_filtrar = filiais_disponiveis[1:]
        df_filtrado = df[df['FILIAL'].isin(filiais_para_filtrar)].copy()
    else:
        df_filtrado = df[df['FILIAL'].isin(filiais_selecionadas)].copy()

    if df_filtrado.empty:
        st.warning("Nenhum dado para as filiais selecionadas. Por favor, ajuste os filtros.")
        st.stop()
    
    # Remover duplicatas baseadas no número do pedido
    df_trabalho = df_filtrado.drop_duplicates(subset=['PEDIDO'], keep='first').copy()
    
    # Os timestamps já foram criados na função fetch_data, não precisamos recriar
    
    # Criação das colunas de STATUS baseadas nos timestamps corretos
    # Etapa 1 está concluída quando TIMESTAMP REMESSA está preenchido
    # Etapa 2 está concluída quando TIMESTAMP ITEM está preenchido  
    # Etapa 3 está concluída quando TIMESTAMP TITULO está preenchido
    
    # STATUS PEDIDO (sempre baseado em TIMESTAMP PEDIDO)
    df_trabalho['STATUS PEDIDO'] = np.where(df_trabalho['TIMESTAMP PEDIDO'].notna(), 'Concluído', 'Pendente')

    # Etapa 1: STATUS REMESSA (baseado em TIMESTAMP REMESSA)
    df_trabalho['STATUS REMESSA'] = np.where(
        df_trabalho['TIMESTAMP REMESSA'].notna(),
        'Concluído', 
        'Pendente'
    )

    # Etapa 2: STATUS ITEM (baseado em TIMESTAMP ITEM)
    df_trabalho['STATUS ITEM'] = np.where(
        df_trabalho['TIMESTAMP ITEM'].notna(), 
        'Concluído', 
        'Pendente'
    )

    # STATUS NF (baseado em TIMESTAMP NF)
    df_trabalho['STATUS NF'] = np.where(
        df_trabalho['TIMESTAMP NF'].notna(), 
        'Concluído', 
        'Pendente'
    )
    
    # Etapa 3: STATUS TITULO (baseado em TIMESTAMP TITULO)
    df_trabalho['STATUS TITULO'] = np.where(
        df_trabalho['TIMESTAMP TITULO'].notna(), 
        'Concluído', 
        'Pendente'
    )
    
    # --- VISUALIZAÇÃO BASEADA NA ETAPA SELECIONADA ---
    if etapa_selecionada == "Visão Geral":
        st.header("Visão Geral do Processo Order to Cash")
        
        # Exibir estatísticas gerais de qualidade dos dados
        total_registros = len(df_trabalho)
        total_pedidos = (df_trabalho['STATUS PEDIDO'] == 'Concluído').sum()
        concluidos_remessa = (df_trabalho['STATUS REMESSA'] == 'Concluído').sum()
        concluidos_item = (df_trabalho['STATUS ITEM'] == 'Concluído').sum()
        concluidos_titulo = (df_trabalho['STATUS TITULO'] == 'Concluído').sum()
        pendentes_geral = total_registros - concluidos_titulo
        percentual_conclusao_completa = (concluidos_titulo / total_registros * 100) if total_registros > 0 else 0
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("Total de Pedidos", f"{total_pedidos:,}")
        
        with col2:
            st.metric("Etapa 1 - Remessa", f"{concluidos_remessa:,}")
        
        with col3:
            st.metric("Etapa 2 - Item", f"{concluidos_item:,}")
        
        with col4:
            st.metric("Etapa 3 - Título", f"{concluidos_titulo:,}")
        
        with col5:
            st.metric("% Conclusão Total", f"{percentual_conclusao_completa:.1f}%")
        
        # Alerta baseado na qualidade dos dados
        percentual_pendentes = (pendentes_geral / total_registros * 100) if total_registros > 0 else 0
        
        if percentual_conclusao_completa < 30:
            st.warning(f"⚠️ Atenção: Apenas {percentual_conclusao_completa:.1f}% dos processos foram concluídos completamente.")
        elif percentual_conclusao_completa < 70:
            st.info(f"ℹ️ {percentual_conclusao_completa:.1f}% dos processos concluídos, {percentual_pendentes:.1f}% ainda em andamento.")
        else:
            st.success(f"✅ Excelente! {percentual_conclusao_completa:.1f}% dos processos foram concluídos completamente.")
        
        st.markdown("---")
        
        # Mostrar dados processados
        st.subheader("Dados Processados")
        colunas_visao_geral = [
            'FILIAL', 'PEDIDO', 'TIMESTAMP PEDIDO', 'STATUS PEDIDO',
            'TIMESTAMP REMESSA', 'STATUS REMESSA',
            'TIMESTAMP ITEM', 'STATUS ITEM',
            'TIMESTAMP TITULO', 'STATUS TITULO'
        ]
        st.dataframe(df_trabalho[colunas_visao_geral])
        
        # Gráfico de barras para status de cada etapa
        st.subheader("Status por Etapa")
        
        # Preparar dados para o gráfico
        status_counts = {
            'Pedido': df_trabalho['STATUS PEDIDO'].value_counts(),
            'Etapa 1 - Remessa': df_trabalho['STATUS REMESSA'].value_counts(),
            'Etapa 2 - Item': df_trabalho['STATUS ITEM'].value_counts(),
            'Etapa 3 - Título': df_trabalho['STATUS TITULO'].value_counts()
        }
        
        status_df = pd.DataFrame({
            'Etapa': [],
            'Status': [],
            'Quantidade': []
        })
        
        for etapa, counts in status_counts.items():
            for status, count in counts.items():
                status_df = pd.concat([status_df, pd.DataFrame({
                    'Etapa': [etapa],
                    'Status': [status],
                    'Quantidade': [count]
                })])
        
        # Criar gráfico de barras
        fig = px.bar(
            status_df, 
            x='Etapa', 
            y='Quantidade', 
            color='Status',
            barmode='group',
            title='Status por Etapa do Processo',
            color_discrete_map={'Concluído': '#28a745', 'Pendente': '#dc3545'}
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Gráfico de funil para visualizar o fluxo do processo
        st.subheader("Funil do Processo Order to Cash")
        
        funil_data = {
            'Etapa': ['Pedido', 'Etapa 1 - Remessa', 'Etapa 2 - Item', 'Etapa 3 - Título'],
            'Concluídos': [
                (df_trabalho['STATUS PEDIDO'] == 'Concluído').sum(),
                (df_trabalho['STATUS REMESSA'] == 'Concluído').sum(),
                (df_trabalho['STATUS ITEM'] == 'Concluído').sum(),
                (df_trabalho['STATUS TITULO'] == 'Concluído').sum()
            ]
        }
        
        funil_df = pd.DataFrame(funil_data)
        
        fig_funil = px.funnel(
            funil_df,
            x='Concluídos',
            y='Etapa',
            title='Funil do Processo Order to Cash'
        )
        
        st.plotly_chart(fig_funil, use_container_width=True)
        
    elif etapa_selecionada == "Etapa 1 - Remessa":
        st.header("Etapa 1 - Remessa")
        
        # Calcular duração entre pedido e remessa
        df_trabalho['DURACAO_PEDIDO_REMESSA'] = df_trabalho['TIMESTAMP REMESSA'] - df_trabalho['TIMESTAMP PEDIDO']
        df_trabalho['DURACAO_PEDIDO_REMESSA_HORAS'] = df_trabalho['DURACAO_PEDIDO_REMESSA'].dt.total_seconds() / 3600
        
        # Calcular média móvel
        tamanho_janela = 3
        df_trabalho['MEDIA_MOVEL_DURACAO_HORAS'] = df_trabalho['DURACAO_PEDIDO_REMESSA_HORAS'].rolling(window=tamanho_janela).mean()
        
        # Agrupamento para pedidos únicos
        agregacoes = {
            'TIMESTAMP PEDIDO': 'first',
            'TIMESTAMP REMESSA': 'first',
            'DURACAO_PEDIDO_REMESSA': 'first',
            'DURACAO_PEDIDO_REMESSA_HORAS': 'first',
            'MEDIA_MOVEL_DURACAO_HORAS': 'first',
            'STATUS PEDIDO': 'first',
            'STATUS REMESSA': 'first',
            'SITUACAO DO PEDIDO': 'first',
            'PEDIDO BLOQUEADO': 'first',
            'USUARIO BLOQ PEDIDO': 'first',
            'DATA DO BLOQUEIO': 'first',
            'OBSERVACAO DO PEDIDO': 'first'
        }
        
        # Filtrar colunas que existem no DataFrame
        agregacoes_existentes = {k: v for k, v in agregacoes.items() if k in df_trabalho.columns}
        df_pedidos_unicos = df_trabalho.groupby(['FILIAL', 'PEDIDO']).agg(agregacoes_existentes).reset_index()
        
        # Tratamento aprimorado dos dados insuficientes
        if 'MEDIA_MOVEL_DURACAO_HORAS' in df_pedidos_unicos.columns:
            # Primeiro, filtrar apenas registros com timestamps válidos
            df_com_timestamps = df_pedidos_unicos[
                df_pedidos_unicos['TIMESTAMP PEDIDO'].notna() & 
                df_pedidos_unicos['TIMESTAMP REMESSA'].notna()
            ].copy()
            
            # Calcular média móvel apenas para dados válidos
            if not df_com_timestamps.empty:
                # Recalcular duração para dados válidos
                df_com_timestamps['DURACAO_PEDIDO_REMESSA_HORAS_VALIDA'] = (
                    df_com_timestamps['TIMESTAMP REMESSA'] - df_com_timestamps['TIMESTAMP PEDIDO']
                ).dt.total_seconds() / 3600
                
                # Filtrar durações positivas (remover valores negativos ou zero)
                df_com_timestamps = df_com_timestamps[
                    df_com_timestamps['DURACAO_PEDIDO_REMESSA_HORAS_VALIDA'] > 0
                ]
                
                if not df_com_timestamps.empty:
                    # Calcular média móvel com dados válidos
                    df_com_timestamps['MEDIA_MOVEL_DURACAO_HORAS_VALIDA'] = (
                        df_com_timestamps['DURACAO_PEDIDO_REMESSA_HORAS_VALIDA']
                        .rolling(window=3, min_periods=1).mean()
                    )
                    
                    # Calcular média geral para preenchimento
                    media_geral_duracao = df_com_timestamps['DURACAO_PEDIDO_REMESSA_HORAS_VALIDA'].mean()
                    media_geral_movel = df_com_timestamps['MEDIA_MOVEL_DURACAO_HORAS_VALIDA'].mean()
                    
                    # Aplicar de volta ao DataFrame principal
                    df_pedidos_unicos = df_pedidos_unicos.merge(
                        df_com_timestamps[['FILIAL', 'PEDIDO', 'DURACAO_PEDIDO_REMESSA_HORAS_VALIDA', 'MEDIA_MOVEL_DURACAO_HORAS_VALIDA']],
                        on=['FILIAL', 'PEDIDO'],
                        how='left'
                    )
                    
                    # Preencher valores nulos com a média geral
                    df_pedidos_unicos['MEDIA_MOVEL_DURACAO_HORAS_FILLNA'] = (
                        df_pedidos_unicos['MEDIA_MOVEL_DURACAO_HORAS_VALIDA']
                        .fillna(media_geral_movel)
                    )
                    
                    df_pedidos_unicos['DURACAO_PEDIDO_REMESSA_HORAS_FILLNA'] = (
                        df_pedidos_unicos['DURACAO_PEDIDO_REMESSA_HORAS_VALIDA']
                        .fillna(media_geral_duracao)
                    )
                    
                    media_da_media_movel = media_geral_movel
                    
                    # Função aprimorada para classificar status da média
                    def classificar_status_media_aprimorado(row):
                        # Verificar se há timestamps válidos - se ausentes, considerar como pendente
                        if pd.isna(row.get('TIMESTAMP PEDIDO')):
                            return 'Pendente - Pedido não Criado'
                        
                        if pd.isna(row.get('TIMESTAMP REMESSA')):
                            return 'Pendente - Remessa não Associada'
                        
                        # Verificar se a duração é válida
                        duracao = row.get('DURACAO_PEDIDO_REMESSA_HORAS_VALIDA')
                        if pd.isna(duracao) or duracao <= 0:
                            return 'Dados Insuficientes - Duração Inválida'
                        
                        # Verificar se há média móvel
                        media_movel = row.get('MEDIA_MOVEL_DURACAO_HORAS_FILLNA')
                        if pd.isna(media_movel):
                            return 'Dados Insuficientes - Média Indisponível'
                        
                        # Classificar com base na comparação
                        if duracao <= media_movel:
                            return 'Dentro da Média'
                        else:
                            return 'Fora da Média'
                    
                    df_pedidos_unicos['CLASSIFICACAO_TEMPO'] = df_pedidos_unicos.apply(classificar_status_media_aprimorado, axis=1)
                    
                    # Adicionar estatísticas de qualidade dos dados
                    total_registros = len(df_pedidos_unicos)
                    registros_validos = len(df_com_timestamps)
                    percentual_dados_validos = (registros_validos / total_registros * 100) if total_registros > 0 else 0
                    
                    # Armazenar estatísticas para exibição
                    df_pedidos_unicos['PERCENTUAL_DADOS_VALIDOS'] = percentual_dados_validos
                    df_pedidos_unicos['TOTAL_REGISTROS'] = total_registros
                    df_pedidos_unicos['REGISTROS_VALIDOS'] = registros_validos
                else:
                    # Se não há dados válidos, aplicar classificação individual
                    def classificar_sem_dados_validos(row):
                        if pd.isna(row.get('TIMESTAMP PEDIDO')):
                            return 'Pendente - Pedido não Criado'
                        elif pd.isna(row.get('TIMESTAMP REMESSA')):
                            return 'Pendente - Remessa não Associada'
                        else:
                            return 'Dados Insuficientes - Sem Dados Válidos'
                    
                    df_pedidos_unicos['CLASSIFICACAO_TEMPO'] = df_pedidos_unicos.apply(classificar_sem_dados_validos, axis=1)
                    df_pedidos_unicos['MEDIA_MOVEL_DURACAO_HORAS_FILLNA'] = 0
                    media_da_media_movel = 0
            else:
                # Se não há dados com timestamps, aplicar classificação individual
                def classificar_sem_timestamps(row):
                    if pd.isna(row.get('TIMESTAMP PEDIDO')):
                        return 'Pendente - Pedido não Criado'
                    elif pd.isna(row.get('TIMESTAMP REMESSA')):
                        return 'Pendente - Remessa não Associada'
                    else:
                        return 'Dados Insuficientes - Timestamps Ausentes'
                
                df_pedidos_unicos['CLASSIFICACAO_TEMPO'] = df_pedidos_unicos.apply(classificar_sem_timestamps, axis=1)
                df_pedidos_unicos['MEDIA_MOVEL_DURACAO_HORAS_FILLNA'] = 0
                media_da_media_movel = 0
        
        # Mapeamento para situação do pedido
        mapeamento_situacao_pedido = {
            1: 'Aberto Total',
            2: 'Aberto Parcial',
            3: 'Suspenso',
            4: 'Liquidado',
            5: 'Cancelado',
            6: 'Aguardando Integração WMS',
            7: 'Em Transmissão',
            8: 'Preparação Análise ou NF',
            9: 'Fechado'
        }
        
        if 'SITUACAO DO PEDIDO' in df_pedidos_unicos.columns:
            # Converter para inteiro se necessário, tratando tanto string quanto numérico
            def converter_situacao(x):
                try:
                    # Tenta converter para int
                    return int(float(x)) if pd.notna(x) else None
                except (ValueError, TypeError):
                    return None
            
            df_pedidos_unicos['SITUACAO DO PEDIDO_NUM'] = df_pedidos_unicos['SITUACAO DO PEDIDO'].apply(converter_situacao)
            
            df_pedidos_unicos['SITUACAO DO PEDIDO_DESCRICAO'] = df_pedidos_unicos['SITUACAO DO PEDIDO_NUM'].apply(
                lambda x: mapeamento_situacao_pedido.get(x, 'Status Desconhecido') if x is not None else 'Status Desconhecido'
            )
        
        # Preparar dados para observações de pedidos bloqueados
        if 'PEDIDO BLOQUEADO' in df_pedidos_unicos.columns and 'OBSERVACAO DO PEDIDO' in df_pedidos_unicos.columns:
            pedidos_bloqueados_obs = df_pedidos_unicos[
                df_pedidos_unicos['PEDIDO BLOQUEADO'].astype(str).str.strip() != ''
            ].copy()
            
            if not pedidos_bloqueados_obs.empty:
                observacoes_bloqueados_validas = pedidos_bloqueados_obs[
                    pedidos_bloqueados_obs['OBSERVACAO DO PEDIDO'].astype(str).str.strip() != ''
                ]
                
                if not observacoes_bloqueados_validas.empty:
                    top_observacoes_bloqueados = observacoes_bloqueados_validas['OBSERVACAO DO PEDIDO'].value_counts().head(10).reset_index()
                    top_observacoes_bloqueados.columns = ['Observação do Pedido (Bloqueado)', 'Quantidade']
        
        # Usar dados já filtrados pela sidebar
        df_filtrado = df_pedidos_unicos.copy()
        
        if df_filtrado.empty:
            st.warning("Não há dados para as filiais selecionadas.")
        else:
            # Mostrar dados específicos da Etapa 1
            
            # Exibir estatísticas de qualidade dos dados da Etapa 1
            # Usar df_trabalho como base para manter consistência com outras etapas
            total_registros = len(df_trabalho)
            concluidos = (df_trabalho['STATUS REMESSA'] == 'Concluído').sum()
            pendentes = (df_trabalho['STATUS REMESSA'] == 'Pendente').sum()
            dados_insuficientes = total_registros - concluidos - pendentes
            percentual_concluidos = (concluidos / total_registros * 100) if total_registros > 0 else 0
                 
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric("Total de Registros", f"{total_registros:,}")
            
            with col2:
                st.metric("Concluídos", f"{concluidos:,}")
            
            with col3:
                st.metric("Pendentes", f"{pendentes:,}")
            
            with col4:
                st.metric("Dados Insuficientes", f"{dados_insuficientes:,}")
            
            with col5:
                st.metric("% Concluídos", f"{percentual_concluidos:.1f}%")
            
            # Alerta baseado na qualidade dos dados
            percentual_pendentes = (pendentes / total_registros * 100) if total_registros > 0 else 0
            percentual_insuficientes = (dados_insuficientes / total_registros * 100) if total_registros > 0 else 0
            
            if percentual_insuficientes > 10:
                st.warning(f"⚠️ Atenção: {percentual_insuficientes:.1f}% dos dados são insuficientes. Verifique a qualidade dos dados.")
            elif percentual_pendentes > 50:
                st.info(f"ℹ️ {percentual_pendentes:.1f}% dos registros estão pendentes (aguardando conclusão das etapas).")
            else:
                st.success(f"✅ Boa qualidade dos dados! {percentual_concluidos:.1f}% concluídos, {percentual_pendentes:.1f}% pendentes.")
            
            st.markdown("---")
            
            colunas_etapa1 = [
                'FILIAL', 'PEDIDO', 'TIMESTAMP PEDIDO', 'TIMESTAMP REMESSA', 
                'STATUS PEDIDO', 'STATUS REMESSA', 'SITUACAO DO PEDIDO', 
                'PEDIDO BLOQUEADO', 'USUARIO BLOQ PEDIDO', 'DATA DO BLOQUEIO', 'OBSERVACAO DO PEDIDO'
            ]
            
            # Filtrar colunas que existem no DataFrame
            colunas_existentes = [col for col in colunas_etapa1 if col in df_filtrado.columns]
            
            # Gráfico de classificação de tempo
            if 'CLASSIFICACAO_TEMPO' in df_filtrado.columns:
                st.subheader("Medição de tempo da geração do pedido até associação da remessa")
                
                # Filtrar apenas 'Dentro da Média' e 'Fora da Média'
                df_tempo_filtrado = df_filtrado[df_filtrado['CLASSIFICACAO_TEMPO'].isin(['Dentro da Média', 'Fora da Média'])]
                contagem_classificacao_tempo = df_tempo_filtrado['CLASSIFICACAO_TEMPO'].value_counts().reset_index()
                contagem_classificacao_tempo.columns = ['Classificação', 'Quantidade de Pedidos']
                
                # Mapeamento de cores para diferentes status
                color_map = {
                    'Dentro da Média': '#28a745',  # Verde
                    'Fora da Média': '#dc3545',    # Vermelho
                }
                
                fig_classificacao_tempo = px.bar(
                    contagem_classificacao_tempo,
                    x='Classificação',
                    y='Quantidade de Pedidos',
                    title='Quantidade de Pedidos Dentro/Fora da Média',
                    labels={
                        'Classificação': 'Classificação de Tempo de Processamento',
                        'Quantidade de Pedidos': 'Número de Pedidos'
                    },
                    color='Classificação',
                    color_discrete_map=color_map,
                    text='Quantidade de Pedidos'
                )
                
                fig_classificacao_tempo.update_traces(texttemplate='%{text}', textposition='outside')
                fig_classificacao_tempo.update_layout(
                    uniformtext_minsize=8,
                    uniformtext_mode='hide',
                    xaxis_title_standoff=25,
                    yaxis_title_standoff=25,
                    margin=dict(l=50, r=50, t=80, b=50),
                    bargap=0.15
                )
                
                if 'MEDIA_MOVEL_DURACAO_HORAS_FILLNA' in df_filtrado.columns:
                    media_filtrada = df_filtrado['MEDIA_MOVEL_DURACAO_HORAS_FILLNA'].mean()
                    fig_classificacao_tempo.add_annotation(
                        text=f"Média até a associação da remessa: {media_filtrada:.2f} horas",
                        xref="paper", yref="paper",
                        x=0.5, y=1.00,
                        showarrow=False,
                        font=dict(size=12, color="green"),
                        bgcolor="lightyellow",
                        bordercolor="green",
                        borderwidth=1,
                        borderpad=4,
                        xanchor="center", yanchor="bottom"
                    )
                
                st.plotly_chart(fig_classificacao_tempo, use_container_width=True)
                
                # Gráfico de proporção por STATUS REMESSA (apenas Concluído/Pendente)
                if 'STATUS REMESSA' in df_filtrado.columns:
                    contagem_por_status_e_filial = df_filtrado.groupby(['FILIAL', 'STATUS REMESSA']).size().reset_index(name='Quantidade')
                    
                    fig_status = px.bar(
                        contagem_por_status_e_filial,
                        x='STATUS REMESSA',
                        y='Quantidade',
                        facet_col='FILIAL',
                        title='Quantidade de Pedidos por Status da Remessa',
                        labels={
                            'Quantidade': 'Número de Pedidos',
                            'STATUS REMESSA': 'Status da Remessa',
                            'FILIAL': 'Filial'
                        },
                        color='STATUS REMESSA',
                         color_discrete_map={
                             'Concluído': '#28a745',  # Verde
                             'Pendente': '#dc3545'  # Vermelho
                         },
                        text='Quantidade'
                    )
                    
                    fig_status.update_traces(texttemplate='%{text}', textposition='outside')
                    fig_status.update_layout(
                        uniformtext_minsize=8,
                        uniformtext_mode='hide',
                        margin=dict(l=50, r=50, t=80, b=100),
                        bargap=0.15,
                        showlegend=False
                    )
                    
                    fig_status.update_xaxes(categoryorder='total descending')
                    
                    st.plotly_chart(fig_status, use_container_width=True)
            
            # Gráfico de situação do pedido
            if 'SITUACAO DO PEDIDO_DESCRICAO' in df_filtrado.columns:
                quantidade_situacao = df_filtrado['SITUACAO DO PEDIDO_DESCRICAO'].value_counts().reset_index()
                quantidade_situacao.columns = ['Situação do Pedido', 'Quantidade']
                
                fig_situacao_donut = px.pie(
                    quantidade_situacao,
                    values='Quantidade',
                    names='Situação do Pedido',
                    title='Proporção de Pedidos por Situação',
                    hole=0.4,
                    labels={'Situação do Pedido': 'Situação do Pedido', 'Quantidade': 'Número de Pedidos'},
                    color='Situação do Pedido',
                    color_discrete_map={
                        'Aberto Total': 'blue',
                        'Aberto Parcial': 'orange',
                        'Suspenso': 'firebrick',
                        'Liquidado': 'green',
                        'Cancelado': 'red',
                        'Fechado': 'yellow'
                    }
                )
                
                fig_situacao_donut.update_traces(textinfo='percent+label', pull=[0.05]*len(quantidade_situacao))
                fig_situacao_donut.update_layout(showlegend=True, uniformtext_minsize=12, uniformtext_mode='hide')
                
                st.plotly_chart(fig_situacao_donut, use_container_width=True)
            
            # Gráfico de observações de pedidos bloqueados
            if 'top_observacoes_bloqueados' in locals() and not top_observacoes_bloqueados.empty:
                fig_obs_bloqueio = px.bar(
                    top_observacoes_bloqueados,
                    y='Observação do Pedido (Bloqueado)',
                    x='Quantidade',
                    orientation='h',
                    title='Top 10 Observações Mais Comuns em Pedidos Bloqueados',
                    labels={
                        'Observação do Pedido (Bloqueado)': 'Observação',
                        'Quantidade': 'Número de Pedidos'
                    },
                    color='Quantidade',
                    color_continuous_scale=px.colors.sequential.Viridis
                )
                fig_obs_bloqueio.update_yaxes(categoryorder='total ascending')
                fig_obs_bloqueio.update_layout(
                    uniformtext_minsize=8,
                    uniformtext_mode='hide',
                    bargap=0.3,
                    margin=dict(l=708)
                )
                
                st.plotly_chart(fig_obs_bloqueio, use_container_width=True)
        
    elif etapa_selecionada == "Etapa 2 - Item":
        st.header("Etapa 2 - Item")
        
        # Os mapeamentos das situações já foram aplicados na função fetch_data
        # Não precisamos aplicar novamente aqui
        
        # Calcular duração e classificação de tempo
        df_trabalho_etapa2 = df_trabalho[df_trabalho['TIMESTAMP REMESSA'].notna() & df_trabalho['TIMESTAMP ITEM'].notna()].copy()
        
        if not df_trabalho_etapa2.empty:
            # Calcular duração em horas
            df_trabalho_etapa2['DURACAO_REMESSA_ITEM'] = df_trabalho_etapa2['TIMESTAMP ITEM'] - df_trabalho_etapa2['TIMESTAMP REMESSA']
            df_trabalho_etapa2['DURACAO_REMESSA_HORAS'] = df_trabalho_etapa2['DURACAO_REMESSA_ITEM'].dt.total_seconds() / 3600
            
            # Calcular média móvel
            tamanho_janela = 3
            df_trabalho_etapa2['MEDIA_MOVEL_DURACAO_HORAS'] = df_trabalho_etapa2['DURACAO_REMESSA_HORAS'].rolling(window=tamanho_janela, min_periods=1).mean()
            
            # Agrupar por pedidos únicos
            agregacoes = {
                'TIMESTAMP REMESSA': 'first',
                'TIMESTAMP ITEM': 'first',
                'DURACAO_REMESSA_ITEM': 'first',
                'DURACAO_REMESSA_HORAS': 'first',
                'MEDIA_MOVEL_DURACAO_HORAS': 'first',
                'STATUS ITEM': 'first'
            }
            
            # Adicionar colunas opcionais se existirem
            if 'CODIGO PRODUTO' in df_trabalho_etapa2.columns:
                agregacoes['CODIGO PRODUTO'] = lambda x: list(x.unique())
            if 'N° NOTA FISCAL' in df_trabalho_etapa2.columns:
                agregacoes['N° NOTA FISCAL'] = lambda x: list(x.unique())
            
            df_pedidos_unicos = df_trabalho_etapa2.groupby(['FILIAL','PEDIDO']).agg(agregacoes).reset_index()
            df_pedidos_unicos['MEDIA_MOVEL_DURACAO_HORAS_FILLNA'] = df_pedidos_unicos['MEDIA_MOVEL_DURACAO_HORAS'].fillna(df_pedidos_unicos['MEDIA_MOVEL_DURACAO_HORAS'].mean())
            
            # Corrigir valores negativos
            media_positiva_duracao = df_pedidos_unicos[df_pedidos_unicos['MEDIA_MOVEL_DURACAO_HORAS_FILLNA'] >= 0]['MEDIA_MOVEL_DURACAO_HORAS_FILLNA'].mean()
            df_pedidos_unicos.loc[df_pedidos_unicos['MEDIA_MOVEL_DURACAO_HORAS_FILLNA'] < 0, 'MEDIA_MOVEL_DURACAO_HORAS_FILLNA'] = media_positiva_duracao
            media_da_media_movel = df_pedidos_unicos['MEDIA_MOVEL_DURACAO_HORAS_FILLNA'].mean()
            
            # Classificar tempo
            def classificar_status_media(row):
                if pd.isna(row['DURACAO_REMESSA_HORAS']) or pd.isna(row['MEDIA_MOVEL_DURACAO_HORAS_FILLNA']):
                    return 'Dados Insuficientes'
                elif row['DURACAO_REMESSA_HORAS'] <= row['MEDIA_MOVEL_DURACAO_HORAS_FILLNA']:
                    return 'Dentro da Média'
                else:
                    return 'Fora da Média'
            
            df_pedidos_unicos['CLASSIFICACAO_TEMPO'] = df_pedidos_unicos.apply(classificar_status_media, axis=1)
        
        # Criar df_situacoes_agrupadas para os gráficos de rosca (como no arquivo original)
        # Usar df_trabalho que já tem os mapeamentos aplicados
        df_situacoes_agrupadas = df_trabalho.copy()
        
        # Usar dados já filtrados pela sidebar
        df_filtrado = df_trabalho.copy()
        if 'df_pedidos_unicos' in locals():
            df_pedidos_filtrados = df_pedidos_unicos.copy()
        
        # Exibir estatísticas de qualidade dos dados da Etapa 2
        # Usar df_trabalho como base para manter consistência
        total_registros = len(df_trabalho)
        concluidos = (df_trabalho['STATUS ITEM'] == 'Concluído').sum()
        pendentes = (df_trabalho['STATUS ITEM'] == 'Pendente').sum()
        dados_insuficientes = total_registros - concluidos - pendentes
        percentual_concluidos = (concluidos / total_registros * 100) if total_registros > 0 else 0
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("Total de Registros", f"{total_registros:,}")
        
        with col2:
            st.metric("Concluídos", f"{concluidos:,}")
        
        with col3:
            st.metric("Pendentes", f"{pendentes:,}")
        
        with col4:
            st.metric("Dados Insuficientes", f"{dados_insuficientes:,}")
        
        with col5:
            st.metric("% Concluídos", f"{percentual_concluidos:.1f}%")
        
        # Alerta baseado na qualidade dos dados
        percentual_pendentes = (pendentes / total_registros * 100) if total_registros > 0 else 0
        percentual_insuficientes = (dados_insuficientes / total_registros * 100) if total_registros > 0 else 0
        
        if percentual_insuficientes > 10:
            st.warning(f"⚠️ Atenção: {percentual_insuficientes:.1f}% dos dados são insuficientes. Verifique a qualidade dos dados.")
        elif percentual_pendentes > 50:
            st.info(f"ℹ️ {percentual_pendentes:.1f}% dos registros estão pendentes (aguardando conclusão das etapas).")
        else:
            st.success(f"✅ Boa qualidade dos dados! {percentual_concluidos:.1f}% concluídos, {percentual_pendentes:.1f}% pendentes.")
        
        st.markdown("---")
        
        # Mostrar dados específicos da Etapa 2
        st.subheader("Medição de tempo da associação da remessa até a preparação do item (PFA)")
        
        # Gráfico de classificação de tempo
        if 'df_pedidos_filtrados' in locals() and not df_pedidos_filtrados.empty:
            contagem_classificacao_tempo = df_pedidos_filtrados['CLASSIFICACAO_TEMPO'].value_counts().reset_index()
            contagem_classificacao_tempo.columns = ['Classificação', 'Quantidade de Pedidos']
            
            fig_classificacao_tempo = px.bar(
                contagem_classificacao_tempo,
                x='Classificação',
                y='Quantidade de Pedidos',
                title='Quantidade de Pedidos por Classificação de Tempo',
                labels={
                    'Classificação': 'Classificação de Tempo de Processamento',
                    'Quantidade de Pedidos': 'Número de Pedidos'
                },
                color='Classificação',
                color_discrete_map={
                    'Dentro da Média': '#28a745',
                    'Fora da Média': '#dc3545',
                    'Dados Insuficientes': 'gray'
                },
                text='Quantidade de Pedidos'
            )
            
            fig_classificacao_tempo.update_traces(texttemplate='%{text}', textposition='outside')
            fig_classificacao_tempo.update_layout(
                uniformtext_minsize=8,
                uniformtext_mode='hide',
                xaxis_title_standoff=25,
                yaxis_title_standoff=25,
                margin=dict(l=50, r=50, t=80, b=50),
                bargap=0.15
            )
            
            if 'media_da_media_movel' in locals():
                fig_classificacao_tempo.add_annotation(
                    text=f"Média até a preparação do item (PFA): {media_da_media_movel:.2f} horas",
                    xref="paper", yref="paper",
                    x=0.5, y=1.00,
                    showarrow=False,
                    font=dict(size=12, color="green"),
                    bgcolor="lightyellow",
                    bordercolor="green",
                    borderwidth=1,
                    borderpad=4,
                    xanchor="center", yanchor="bottom"
                )
            
            st.plotly_chart(fig_classificacao_tempo, use_container_width=True)
        

        # Gráfico de proporção por STATUS ITEM (apenas Concluído/Pendente)
        if 'STATUS ITEM' in df_trabalho.columns:
            contagem_por_status_e_filial = df_trabalho.groupby(['FILIAL', 'STATUS ITEM']).size().reset_index(name='Quantidade')
            
            fig_status_item = px.bar(
                contagem_por_status_e_filial,
                x='STATUS ITEM',
                y='Quantidade',
                facet_col='FILIAL',
                title='Quantidade de Pedidos por Status do Item',
                labels={
                    'Quantidade': 'Número de Pedidos',
                    'STATUS ITEM': 'Status do Item',
                    'FILIAL': 'Filial'
                },
                color='STATUS ITEM',
                color_discrete_map={
                    'Concluído': '#28a745',  # Verde
                    'Pendente': '#dc3545'  # Vermelho
                },
                text='Quantidade'
            )
            
            fig_status_item.update_traces(texttemplate='%{text}', textposition='outside')
            fig_status_item.update_layout(
                uniformtext_minsize=8,
                uniformtext_mode='hide',
                margin=dict(l=50, r=50, t=80, b=100),
                bargap=0.15,
                showlegend=False
            )
            
            fig_status_item.update_xaxes(categoryorder='total descending')
            
            st.plotly_chart(fig_status_item, use_container_width=True)
        
        # Análise de produtos por nota fiscal
        if not df_filtrado.empty and 'N° NOTA FISCAL' in df_filtrado.columns and 'CODIGO PRODUTO' in df_filtrado.columns:
            quantidade_produtos_por_nota = df_filtrado.groupby('N° NOTA FISCAL')['CODIGO PRODUTO'].nunique().reset_index()
            quantidade_produtos_por_nota.columns = ['N° NOTA FISCAL', 'Quantidade de Produtos']
            
            contagem_notas_por_quantidade_produtos = quantidade_produtos_por_nota.groupby('Quantidade de Produtos').size().reset_index(name='Quantidade de Notas Fiscais')
            
            total_notas_fiscais_analisadas = contagem_notas_por_quantidade_produtos['Quantidade de Notas Fiscais'].sum()
            
            if total_notas_fiscais_analisadas > 0:
                contagem_notas_por_quantidade_produtos['Porcentagem'] = (
                    contagem_notas_por_quantidade_produtos['Quantidade de Notas Fiscais'] / total_notas_fiscais_analisadas * 100
                ).round(2)
                
                fig_produtos_nota = px.bar(
                    contagem_notas_por_quantidade_produtos,
                    x='Quantidade de Produtos',
                    y='Porcentagem',
                    text='Porcentagem',
                    title='Porcentagem de Notas Fiscais por Quantidade de Produtos',
                    labels={'Porcentagem': 'Porcentagem (%)', 'Quantidade de Produtos': 'Qtd. de Produtos por Nota'},
                    color='Porcentagem',
                    color_continuous_scale=px.colors.sequential.Sunset
                )
                
                fig_produtos_nota.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
                fig_produtos_nota.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
                fig_produtos_nota.update_yaxes(range=[0, 100])
                
                st.plotly_chart(fig_produtos_nota, use_container_width=True)
        
        # Gráfico de produtos mais vendidos
        if not df_filtrado.empty and 'CODIGO PRODUTO' in df_filtrado.columns:
            top_produtos = df_filtrado['CODIGO PRODUTO'].value_counts().reset_index()
            top_produtos.columns = ['Codigo do Produto', 'Quantidade de Vendas (Itens)']
            
            if len(top_produtos) > 3:
                df_donut = top_produtos.head(3).copy()
                outros_soma = top_produtos['Quantidade de Vendas (Itens)'][3:].sum()
                df_donut.loc[3] = ['Outros', outros_soma]
            else:
                df_donut = top_produtos.copy()
            
            fig_donut = px.pie(
                df_donut,
                values='Quantidade de Vendas (Itens)',
                names='Codigo do Produto',
                title='Contribuição dos Produtos Mais Vendidos',
                hole=0.4,
                color_discrete_sequence=px.colors.sequential.Plasma
            )
            fig_donut.update_traces(textinfo='percent+label', pull=[0.05]*len(df_donut))
            st.plotly_chart(fig_donut, use_container_width=True)
        
        # Gráficos de situações em colunas
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if 'SITUACAO PFA' in df_situacoes_agrupadas.columns:
                df_pfa_counts = df_situacoes_agrupadas['SITUACAO PFA'].value_counts().reset_index()
                df_pfa_counts.columns = ['Situacao', 'Contagem']
                
                fig_pfa = px.pie(df_pfa_counts, values='Contagem', names='Situacao',
                                title='Distribuição por Situação PFA', hole=0.4,
                                color_discrete_sequence=px.colors.sequential.Plasma)
                fig_pfa.update_traces(textinfo='percent+label', pull=[0.05]*len(df_pfa_counts))
                st.plotly_chart(fig_pfa, use_container_width=True)
        
        with col2:
            if 'SITUACAO CARGA' in df_situacoes_agrupadas.columns:
                df_carga_counts = df_situacoes_agrupadas['SITUACAO CARGA'].value_counts().reset_index()
                df_carga_counts.columns = ['Situacao', 'Contagem']
                
                fig_carga = px.pie(df_carga_counts, values='Contagem', names='Situacao',
                                  title='Distribuição por Situação Carga', hole=0.4,
                                  color_discrete_sequence=px.colors.sequential.Plasma)
                fig_carga.update_traces(textinfo='percent+label', pull=[0.05]*len(df_carga_counts))
                st.plotly_chart(fig_carga, use_container_width=True)
        
        with col3:
            if 'SITUACAO NFV' in df_situacoes_agrupadas.columns:
                df_nfv_counts = df_situacoes_agrupadas['SITUACAO NFV'].value_counts().reset_index()
                df_nfv_counts.columns = ['Situacao', 'Contagem']
                
                fig_nfv = px.pie(df_nfv_counts, values='Contagem', names='Situacao',
                                title='Distribuição por Situação NFV', hole=0.4,
                                color_discrete_sequence=px.colors.sequential.Plasma)
                fig_nfv.update_traces(textinfo='percent+label', pull=[0.05]*len(df_nfv_counts))
                st.plotly_chart(fig_nfv, use_container_width=True)
        
        # Gráfico de bloqueios PFA por data
        if 'BLOQUEIO PFA' in df_filtrado.columns:
            df_bloqueios_pfa = df_filtrado[df_filtrado['BLOQUEIO PFA'].notna() & (df_filtrado['BLOQUEIO PFA'] != 0) & (df_filtrado['BLOQUEIO PFA'] != '')].copy()
        else:
            df_bloqueios_pfa = pd.DataFrame()
        
        if not df_bloqueios_pfa.empty:
            bloqueios_por_data = df_bloqueios_pfa.groupby(df_bloqueios_pfa['TIMESTAMP REMESSA'].dt.date).size().reset_index(name='Quantidade de Bloqueios')
            bloqueios_por_data.columns = ['Data do Bloqueio', 'Quantidade de Bloqueios']
            bloqueios_por_data = bloqueios_por_data.sort_values('Data do Bloqueio')
            
            if not bloqueios_por_data.empty:
                fig_bloqueios_pfa_data = px.bar(
                    bloqueios_por_data,
                    x='Data do Bloqueio',
                    y='Quantidade de Bloqueios',
                    title='Quantidade de Bloqueios PFA por Data',
                    labels={'Data do Bloqueio': 'Data', 'Quantidade de Bloqueios': 'Número de Bloqueios'},
                    color='Quantidade de Bloqueios',
                    color_continuous_scale=px.colors.sequential.Sunset,
                    text='Quantidade de Bloqueios'
                )
                fig_bloqueios_pfa_data.update_traces(texttemplate='%{text}', textposition='outside')
                fig_bloqueios_pfa_data.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
                st.plotly_chart(fig_bloqueios_pfa_data, use_container_width=True)
        else:
            st.info("Não foram encontrados bloqueios PFA para as filiais selecionadas.")
        
    elif etapa_selecionada == "Etapa 3 - Título":
        st.header("Etapa 3 - Título")
        
        # Exibir estatísticas de qualidade dos dados da Etapa 3
        total_registros = len(df_trabalho)
        concluidos = (df_trabalho['STATUS TITULO'] == 'Concluído').sum()
        pendentes = (df_trabalho['STATUS TITULO'] == 'Pendente').sum()
        dados_insuficientes = total_registros - concluidos - pendentes
        percentual_concluidos = (concluidos / total_registros * 100) if total_registros > 0 else 0
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("Total de Registros", f"{total_registros:,}")
        
        with col2:
            st.metric("Concluídos", f"{concluidos:,}")
        
        with col3:
            st.metric("Pendentes", f"{pendentes:,}")
        
        with col4:
            st.metric("Dados Insuficientes", f"{dados_insuficientes:,}")
        
        with col5:
            st.metric("% Concluídos", f"{percentual_concluidos:.1f}%")
        
        # Alerta baseado na qualidade dos dados
        percentual_pendentes = (pendentes / total_registros * 100) if total_registros > 0 else 0
        percentual_insuficientes = (dados_insuficientes / total_registros * 100) if total_registros > 0 else 0
        
        if percentual_insuficientes > 10:
            st.warning(f"⚠️ Atenção: {percentual_insuficientes:.1f}% dos dados são insuficientes. Verifique a qualidade dos dados.")
        elif percentual_pendentes > 50:
            st.info(f"ℹ️ {percentual_pendentes:.1f}% dos registros estão pendentes (aguardando conclusão das etapas).")
        else:
            st.success(f"✅ Boa qualidade dos dados! {percentual_concluidos:.1f}% concluídos, {percentual_pendentes:.1f}% pendentes.")
        
        st.markdown("---")
        
        # Gráfico original de STATUS TITULO
        if 'STATUS TITULO' in df_trabalho.columns:
            contagem_por_status = df_trabalho['STATUS TITULO'].value_counts().reset_index()
            contagem_por_status.columns = ['Status', 'Quantidade']
            
            fig_status = px.bar(
                contagem_por_status,
                x='Status',
                y='Quantidade',
                title='Quantidade de Títulos por Status',
                labels={'Quantidade': 'Número de Títulos', 'Status': 'Status do Título'},
                color='Status',
                color_discrete_map={
                    'Concluído': '#28a745',  # Verde
                    'Pendente': '#dc3545'  # Vermelho
                },
                text='Quantidade'
            )
            
            fig_status.update_traces(texttemplate='%{text}', textposition='outside')
            fig_status.update_layout(
                uniformtext_minsize=8,
                uniformtext_mode='hide',
                xaxis_title_standoff=25,
                yaxis_title_standoff=25,
                margin=dict(l=50, r=50, t=80, b=50),
                bargap=0.15
            )
            
            fig_status.update_xaxes(categoryorder='total descending')
            
            st.plotly_chart(fig_status, use_container_width=True)
        
        # Gráfico de proporção por STATUS TITULO por filial
        if 'STATUS TITULO' in df_trabalho.columns:
            contagem_por_status_e_filial = df_trabalho.groupby(['FILIAL', 'STATUS TITULO']).size().reset_index(name='Quantidade')
            
            fig_status_titulo = px.bar(
                contagem_por_status_e_filial,
                x='STATUS TITULO',
                y='Quantidade',
                facet_col='FILIAL',
                title='Quantidade de Pedidos por Status do Título por Filial',
                labels={
                    'Quantidade': 'Número de Pedidos',
                    'STATUS TITULO': 'Status do Título',
                    'FILIAL': 'Filial'
                },
                color='STATUS TITULO',
                color_discrete_map={
                    'Concluído': '#28a745',  # Verde
                    'Pendente': '#dc3545'  # Vermelho
                },
                text='Quantidade'
            )
            
            fig_status_titulo.update_traces(texttemplate='%{text}', textposition='outside')
            fig_status_titulo.update_layout(
                uniformtext_minsize=8,
                uniformtext_mode='hide',
                margin=dict(l=50, r=50, t=80, b=100),
                bargap=0.15,
                showlegend=False
            )
            
            fig_status_titulo.update_xaxes(categoryorder='total descending')
            
            st.plotly_chart(fig_status_titulo, use_container_width=True)
        
        # Mostrar dados específicos da Etapa 3
        colunas_etapa3 = [
            'FILIAL', 'PEDIDO', 'N° TITULO', 'VENCIMENTO ORIGINAL DO TITULO',
            'TIMESTAMP ITEM', 'TIMESTAMP TITULO', 'STATUS ITEM', 'STATUS TITULO',
            'SITUACAO DO TITULO', 'SITUACAO TCR'
        ]
        
        # Filtrar colunas que existem no DataFrame
        colunas_existentes = [col for col in colunas_etapa3 if col in df_trabalho.columns]
        
        # Gráfico de tempo médio entre Item e Título
        st.subheader("Tempo Médio entre Item e Título")
        
        # Filtrar apenas registros com ambos timestamps disponíveis
        df_tempo = df_trabalho[df_trabalho['TIMESTAMP ITEM'].notna() & df_trabalho['TIMESTAMP TITULO'].notna()].copy()
        
        if not df_tempo.empty:
            # Calcular a diferença em horas
            df_tempo['Tempo (horas)'] = (df_tempo['TIMESTAMP TITULO'] - df_tempo['TIMESTAMP ITEM']).dt.total_seconds() / 3600
            
            # Agrupar por filial
            tempo_medio_por_filial = df_tempo.groupby('FILIAL')['Tempo (horas)'].mean().reset_index()
            tempo_medio_por_filial['Tempo (horas)'] = tempo_medio_por_filial['Tempo (horas)'].round(2)
            
            fig = px.bar(
                tempo_medio_por_filial,
                x='FILIAL',
                y='Tempo (horas)',
                title='Tempo Médio entre Item e Título por Filial (horas)',
                color='FILIAL'
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Não há dados suficientes para calcular o tempo médio entre Item e Título.")
        
        # Gráfico de distribuição por Situação TCR
        if 'SITUACAO TCR' in df_trabalho.columns:
            st.subheader("Distribuição por Situação TCR")
            
            situacao_tcr_counts = df_trabalho['SITUACAO TCR'].value_counts().reset_index()
            situacao_tcr_counts.columns = ['Situação TCR', 'Quantidade']
            
            fig = px.pie(
                situacao_tcr_counts,
                values='Quantidade',
                names='Situação TCR',
                title='Distribuição por Situação TCR'
            )
            
            st.plotly_chart(fig, use_container_width=True)

else:
    st.info("Por favor, digite uma data e clique em 'Buscar Dados' para visualizar as informações.")