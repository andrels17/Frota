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

# --- NOVA LÓGICA DE CATEGORIZAÇÃO PERSONALIZADA ---

# Lista das categorias que você quer destacar
categorias_principais = [
    'COLHEDORA', 'TRATOR', 'TRANSBORDO', 'CAMINHAO', 'CARREGADEIRA',
    'MOTOR BOMBA', 'GERADOR', 'REBOQUE', 'MOTONIVELADORA', 'PÁS', 
    'EMPILHADEIRA'
]

# Função para categorizar a frota com base na sua lista
def categorizar_frota(descricao):
    descricao = str(descricao).upper()
    for categoria in categorias_principais:
        if categoria in descricao:
            # Para PÁS, podemos especificar melhor
            if 'PÁ' in descricao and ('MECANICA' in descricao or 'CARREGADEIRA' in descricao):
                return 'PÁ CARREGADEIRA / MECANICA'
            else:
                return categoria
    return 'Outros'

df['Categoria'] = df['Descrição'].apply(categorizar_frota)

# Preparar dados para o gráfico de barras
df_por_categoria = df['Categoria'].value_counts().reset_index()
df_por_categoria.columns = ['Categoria', 'Número de Itens']

# --- Construir a interface com Streamlit ---

st.subheader("Distribuição da Frota por Categoria Principal")

# Criar um gráfico de barras com as categorias personalizadas
fig_bar = px.bar(df_por_categoria, x='Categoria', y='Número de Itens',
                 title='Distribuição da Frota por Categoria')
st.plotly_chart(fig_bar, use_container_width=True)

st.subheader("Dados da Frota Completa")

# Adicionar a caixa de pesquisa
search_term = st.text_input("Pesquisar na frota (ex: Trator, Placa, Proprietário)")

# Filtrar o DataFrame com base no termo de pesquisa
if search_term:
    df_filtered = df[df.apply(lambda row: row.astype(str).str.contains(search_term, case=False).any(), axis=1)]
    st.dataframe(df_filtered, use_container_width=True)
else:
    # Exibir a tabela completa se não houver termo de pesquisa
    st.dataframe(df, use_container_width=True)
