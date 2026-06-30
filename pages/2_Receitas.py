from __future__ import annotations

from datetime import date

import streamlit as st

from database import init_db
from services import list_categories, money, query_df, save_income

init_db()

st.title("Receitas")

categories = list_categories("receita")
cat_options = {row["nome"]: int(row["id"]) for _, row in categories.iterrows()}

with st.form("receita_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    data_receita = col1.date_input("Data da receita", value=date.today())
    valor = col2.number_input("Valor", min_value=0.0, step=50.0, format="%.2f")
    descricao = st.text_input("Descricao")
    categoria_nome = st.selectbox("Categoria", list(cat_options.keys()) or [""])
    responsavel = st.text_input("Responsavel")
    recorrente = st.checkbox("Receita recorrente")
    observacao = st.text_area("Observacao")
    submitted = st.form_submit_button("Salvar receita")

if submitted:
    if not descricao or valor <= 0:
        st.error("Informe descricao e valor maior que zero.")
    else:
        save_income(data_receita, descricao, cat_options.get(categoria_nome), valor, responsavel, recorrente, observacao)
        st.success("Receita salva.")

st.subheader("Receitas cadastradas")
df = query_df(
    """
    SELECT r.data_receita AS data, r.descricao, COALESCE(c.nome, 'Sem categoria') AS categoria,
           r.valor, r.responsavel, CASE WHEN r.recorrente = 1 THEN 'Sim' ELSE 'Nao' END AS recorrente
      FROM receitas r
      LEFT JOIN categorias c ON c.id = r.categoria_id
     ORDER BY r.data_receita DESC, r.id DESC
    """
)
if df.empty:
    st.info("Nenhuma receita cadastrada ainda.")
else:
    st.dataframe(df.assign(valor=df["valor"].map(money)), use_container_width=True, hide_index=True)
