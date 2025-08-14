import streamlit as st
import requests
import pandas as pd
import xml.etree.ElementTree as ET
import plotly.express as px
import numpy as np

# --- INICIALIZAÇÃO E FUNÇÃO DE CARREGAMENTO DE DADOS ---
if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame()

@st.cache_data(show_spinner="Buscando dados...")
def fetch_data(data):
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
            st.success("Dados carregados com sucesso!")
            root = ET.fromstring(response.text)
            
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
                    'CHoraGerTCR': 'HORA GERACAO DO REGISTRO'
                }
                
                df = df.rename(columns=mapeamento_nomes)
                return df
            else:
                st.warning("Nenhum dado encontrado na resposta do XML. Verifique se o caminho da busca está correto.")
                return pd.DataFrame() 
            
        else:
            st.error(f"Erro ao buscar os dados: Código de status {response.status_code}")
            return pd.DataFrame()
    
    except requests.exceptions.RequestException as e:
        st.error(f"Erro de conexão: {e}")
        return pd.DataFrame()

# --- INTERFACE DO STREAMLIT E FLUXO DE FILTRO ---
st.title("Consulta de Dados do Web Service")
data_input = st.text_input("Digite a data (formato DD/MM/AAAA):", value="19/06/2025")

if st.button("Buscar Dados"):
    if data_input:
        st.session_state.df = fetch_data(data_input)
    else:
        st.warning("Por favor, digite uma data para buscar os dados.")
        
# --- INÍCIO DO TRATAMENTO E VISUALIZAÇÃO ---
if 'df' in st.session_state and not st.session_state.df.empty:
    
    st.sidebar.header("Filtros")
    
    filiais_brutas = st.session_state.df['FILIAL'].unique()
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
        df_filtrado = st.session_state.df[st.session_state.df['FILIAL'].isin(filiais_para_filtrar)].copy()
    else:
        df_filtrado = st.session_state.df[st.session_state.df['FILIAL'].isin(filiais_selecionadas)].copy()

    if df_filtrado.empty:
        st.warning("Nenhum dado para as filiais selecionadas. Por favor, ajuste os filtros.")
        st.stop()

    colunas_selecionadas = ['FILIAL', 'PEDIDO', 'DATA EMISSAO PEDIDO', 'HORA EMISSAO PEDIDO', 'DATA ASS REMESSA', 'HORA ASS REMESSA',
                             'DATA PREPARACAO DO ITEM', 'HORA PREPARACAO DO ITEM', 'DATA GERACAO NF', 'HORA GERACAO NF',
                             'DATA GERACAO DO REGISTRO', 'HORA GERACAO DO REGISTRO'] 
    
    df_trabalho = df_filtrado[colunas_selecionadas].copy()
    df_trabalho = df_trabalho.drop_duplicates(subset=['PEDIDO'], keep='first').copy()
    
    st.markdown("---")
    st.subheader("Dados Processados")
    st.dataframe(df_trabalho)
    st.markdown("---")

    # --- CRIAÇÃO DOS TIMESTAMPS ---
    
    timestamp_map = {
        ('DATA EMISSAO PEDIDO', 'HORA EMISSAO PEDIDO'): 'TIMESTAMP PEDIDO',
        ('DATA ASS REMESSA', 'HORA ASS REMESSA'): 'TIMESTAMP REMESSA',
        ('DATA PREPARACAO DO ITEM', 'HORA PREPARACAO DO ITEM'): 'TIMESTAMP ITEM',
        ('DATA GERACAO DO REGISTRO', 'HORA GERACAO DO REGISTRO'): 'TIMESTAMP TITULO'
    }
    
    for (data_col, hora_col), ts_col in timestamp_map.items():
        df_trabalho[data_col] = df_trabalho[data_col].replace('31/12/1900', np.nan)
        df_trabalho[hora_col] = df_trabalho[hora_col].replace([':', '00:00'], np.nan)

        combined_string = df_trabalho[data_col].astype(str) + ' ' + df_trabalho[hora_col].astype(str)

        df_trabalho[ts_col] = pd.to_datetime(
            combined_string,
            format='%d/%m/%Y %H:%M:%S',
            errors='coerce'
        )

        nan_mask = df_trabalho[ts_col].isna()
        if nan_mask.any():
            df_trabalho.loc[nan_mask, ts_col] = pd.to_datetime(
                combined_string,
                format='%d/%m/%Y %H:%M',
                errors='coerce'
            )

        df_trabalho.loc[df_trabalho[ts_col].dt.year == 1900, ts_col] = pd.NaT

    # --- CRIAÇÃO DAS COLUNAS DE STATUS COM LÓGICA SEQUENCIAL APRIMORADA ---
    # Etapa 1: PEDIDO (base)
    df_trabalho['STATUS PEDIDO'] = np.where(df_trabalho['TIMESTAMP PEDIDO'].notna(), 'Concluído', 'Pendente')

    # Etapa 2: REMESSA (depende do status de PEDIDO)
    df_trabalho['STATUS REMESSA'] = np.where(
        (df_trabalho['TIMESTAMP REMESSA'].notna()) & (df_trabalho['STATUS PEDIDO'] == 'Concluído'),
        'Concluído', 
        'Pendente'
    )

    # Etapa 3: ITEM (depende do status de REMESSA)
    df_trabalho['STATUS ITEM'] = np.where(
        (df_trabalho['TIMESTAMP ITEM'].notna()) & (df_trabalho['STATUS REMESSA'] == 'Concluído'), 
        'Concluído', 
        'Pendente'
    )

    # Etapa 4: TITULO (depende do status de ITEM)
    df_trabalho['STATUS TITULO'] = np.where(
        (df_trabalho['TIMESTAMP TITULO'].notna()) & (df_trabalho['STATUS ITEM'] == 'Concluído'), 
        'Concluído', 
        'Pendente'
    )
    
    # --- PREPARAÇÃO DOS DADOS PARA O GRÁFICO ---
    status_cols_map = {
        'TIMESTAMP PEDIDO': 'STATUS PEDIDO',
        'TIMESTAMP REMESSA': 'STATUS REMESSA',
        'TIMESTAMP ITEM': 'STATUS ITEM',
        'TIMESTAMP TITULO': 'STATUS TITULO'
    }
    
    status_cols = list(status_cols_map.values())
    df_status_counts = pd.DataFrame(columns=['Etapa', 'Status', 'Quantidade'])

    for col in status_cols:
        etapa = col.replace('STATUS ', '')
        counts = df_trabalho[col].value_counts().reset_index()
        counts.columns = ['Status', 'Quantidade']
        counts['Etapa'] = etapa
        df_status_counts = pd.concat([df_status_counts, counts], ignore_index=True)

    for etapa in ['PEDIDO', 'REMESSA', 'ITEM', 'TITULO']:
        if 'Concluído' not in df_status_counts[df_status_counts['Etapa'] == etapa]['Status'].values:
            df_status_counts = pd.concat([df_status_counts, pd.DataFrame([{'Etapa': etapa, 'Status': 'Concluído', 'Quantidade': 0}])], ignore_index=True)
        if 'Pendente' not in df_status_counts[df_status_counts['Etapa'] == etapa]['Status'].values:
            df_status_counts = pd.concat([df_status_counts, pd.DataFrame([{'Etapa': etapa, 'Status': 'Pendente', 'Quantidade': 0}])], ignore_index=True)

    etapa_ordem = ['PEDIDO', 'REMESSA', 'ITEM', 'TITULO']
    df_status_counts['Etapa'] = pd.Categorical(df_status_counts['Etapa'], categories=etapa_ordem, ordered=True)
    df_status_counts = df_status_counts.sort_values('Etapa')

    df_status_counts['Quantidade'] = pd.to_numeric(df_status_counts['Quantidade'], errors='coerce')
    df_total_por_etapa = df_status_counts.groupby('Etapa', observed=False)['Quantidade'].sum().reset_index()
    df_total_por_etapa.columns = ['Etapa', 'Total']
    df_status_counts = pd.merge(df_status_counts, df_total_por_etapa, on='Etapa')
    df_status_counts['Porcentagem'] = (df_status_counts['Quantidade'] / df_total_por_etapa.loc[0, 'Total'] * 100).round(1)

    # --- VISUALIZAÇÃO DO GRÁFICO E TABELA ---
    st.title("Análise da Linha do Tempo de Pedidos")

    color_map = {
        'Concluído': 'green',
        'Pendente': 'red'
    }

    fig = px.bar(
        df_status_counts,
        x='Etapa',
        y='Quantidade',
        color='Status',
        title='Pedidos por Status em cada Etapa',
        labels={'Etapa': 'Etapa do Processo', 'Quantidade': 'Quantidade de Pedidos'},
        barmode='stack',
        text='Porcentagem',
        color_discrete_map=color_map
    )

    fig.update_traces(textposition='inside')

    st.plotly_chart(fig, use_container_width=True)
    st.markdown("---")
    st.dataframe(df_status_counts)