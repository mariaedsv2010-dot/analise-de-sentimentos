import streamlit as st
import spacy
import psycopg2
import os

# -----------------------------------------------------------------------------
# Configuração da Página e Estilo (Focado no público 17-35 anos)
# -----------------------------------------------------------------------------
st.set_page_config(page_title="SentimenTech", page_icon="🧠", layout="centered")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; background-color: #4F46E5; color: white; border-radius: 8px; }
    .stButton>button:hover { background-color: #4338CA; color: white; }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Inicialização do Modelo SpaCy e Conexão com o Banco
# -----------------------------------------------------------------------------
@st.cache_resource
def carregar_spacy():
    # Carrega o modelo leve de português
    try:
        return spacy.load("pt_core_news_sm")
    except OSError:
        # Fallback caso o download falhe no ambiente local
        from spacy.cli import download
        download("pt_core_news_sm")
        return spacy.load("pt_core_news_sm")

nlp = carregar_spacy()

def conectar_banco():
    # No Render/Local, pegamos a URL das variáveis de ambiente por segurança
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        # Fallback para desenvolvimento local (substitua pela sua se necessário)
        DATABASE_URL = st.secrets.get("DATABASE_URL", "")
    
    return psycopg2.connect(DATABASE_URL)

# -----------------------------------------------------------------------------
# Lógica de Análise de Sentimento (SpaCy Lematização)
# -----------------------------------------------------------------------------
def analisar_sentimento(texto):
    doc = nlp(texto.lower())
    
    # Léxico simples baseado em lemas para demonstração robusta e leve
    palavras_positivas = {'bom', 'otimo', 'maravilhoso', 'excelente', 'gostar', 'amar', 'feliz', 'top', 'sucesso', 'recomendo'}
    palavras_negativas = {'ruim', 'pessimo', 'odiar', 'triste', 'decepcionado', 'horrivel', 'fracasso', 'nao', 'nunca', 'errado'}
    
    score = 0
    for token in doc:
        if token.lemma_ in palavras_positivas:
            score += 1
        elif token.lemma_ in palavras_negativas:
            score -= 1
            
    return "Positivo" if score >= 0 else "Negativo"

# -----------------------------------------------------------------------------
# Interface do Usuário (Streamlit View)
# -----------------------------------------------------------------------------
st.title("🧠 SentimenTech")
st.subheader("Analise o sentimento de forma simples e rápida.")
st.write("Insira os dados abaixo para rodar a nossa IA.")

with st.form(key="formulario_sentimento", clear_on_submit=True):
    nome = st.text_input("Seu Nome", placeholder="Ex: João Silva")
    cpf = st.text_input("Seu CPF", placeholder="Ex: 000.000.000-00")
    sentimento_texto = st.text_area("O que você está sentindo/pensando?", placeholder="Escreva sua avaliação aqui...")
    
    botao_enviar = st.form_submit_button(label="Analisar e Salvar")

# -----------------------------------------------------------------------------
# Processamento do Formulário
# -----------------------------------------------------------------------------
if botao_enviar:
    if not nome or not cpf or not sentimento_texto:
        st.error("⚠️ Por favor, preencha todos os campos do formulário.")
    else:
        with st.spinner("Nossa IA está processando seu texto..."):
            # Executa a análise de NLP
            resultado = analisar_sentimento(sentimento_texto)
            
            # Salva no Neon Tech (PostgreSQL)
            try:
                conn = conectar_banco()
                cursor = conn.cursor()
                
                query = """
                INSERT INTO avaliacoes_sentimento (nome, cpf, texto_sentimento, analise_resultado)
                VALUES (%s, %s, %s, %s);
                """
                cursor.execute(query, (nome, cpf, sentimento_texto, resultado))
                conn.commit()
                
                cursor.close()
                conn.close()
                
                # Feedback visual para o usuário
                st.success("🎉 Dados processados e salvos com sucesso!")
                
                if resultado == "Positivo":
                    st.balloons()
                    st.success(f"**Resultado da Análise:** Seu sentimento foi classificado como **{resultado}**! 😄")
                else:
                    st.warning(f"**Resultado da Análise:** Seu sentimento foi classificado como **{resultado}**. 😕")
                    
            except Exception as e:
                st.error(f"Erro ao conectar ou salvar no banco de dados: {e}")