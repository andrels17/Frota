import pandas as pd
import plotly.express as px
import streamlit as st
import io

# Configurar a página do Streamlit
st.set_page_config(layout="wide")
st.title("Dashboard de Frotas")

# Carregar o arquivo CSV com a codificação 'latin1'
# Altere o caminho se necessário
file_path = 'frotas.csv'
df = pd.read_csv(file_path, delimiter=';', encoding='latin1')

# Renomear colunas com caracteres especiais
df.rename(columns={
    'DescriÃ§Ã£o': 'Descrição',
    'CÃ³digo': 'Código',
    'SÃ©rie': 'Série',
    'ProprietÃ¡rio': 'Proprietário',
    'Filial ProprietÃ¡rio': 'Filial Proprietário'
}, inplace=True)

# Preencher valores ausentes e padronizar
df['Placa'] = df['Placa'].fillna('Não Informado')
df['Patrimonio'] = df['Patrimonio'].fillna('Não Informado')
df['Chassis'] = df['Chassis'].fillna('Não Informado')
df['Série'] = df['Série'].fillna('Não Informado')
df['Proprietário'] = df['Proprietário'].str.replace(' S/A', '', regex=False).str.strip().str.upper()

def categorizar_descricao(descricao):
    descricao = str(descricao).upper()
    if 'TRATOR' in descricao:
        return 'TRATOR'
    elif 'ADUBADEIRA' in descricao:
        return 'ADUBADEIRA'
    elif 'ASPERSORES' in descricao:
        return 'ASPERSORES'
    elif 'TURBOMAQ' in descricao:
        return 'TURBOMAQ'
    else:
        return 'OUTROS'

df['Categoria'] = df['Descrição'].apply(categorizar_descricao)

# Preparar dados para os gráficos
df_por_categoria = df['Categoria'].value_counts().reset_index()
df_por_categoria.columns = ['Categoria', 'Número de Itens']

df_por_proprietario = df['Proprietário'].value_counts().reset_index()
df_por_proprietario.columns = ['Proprietário', 'Número de Itens']

# --- Construir a interface com Streamlit ---

# Criar duas colunas para os gráficos
col1, col2 = st.columns(2)

with col1:
    st.subheader("Distribuição por Categoria")
    fig_pie = px.pie(df_por_categoria, values='Número de Itens', names='Categoria', 
                     title='Distribuição da Frota por Categoria')
    st.plotly_chart(fig_pie, use_container_width=True)

with col2:
    st.subheader("Itens por Proprietário")
    fig_bar = px.bar(df_por_proprietario, x='Proprietário', y='Número de Itens',
                     title='Itens por Proprietário')
    st.plotly_chart(fig_bar, use_container_width=True)

st.subheader("Dados da Frota Completa")
st.dataframe(df, use_container_width=True)