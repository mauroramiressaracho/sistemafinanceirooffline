from __future__ import annotations

from datetime import date

import streamlit as st

from database import init_db
from services import list_categories, list_payment_methods, money, query_df, save_expense

init_db()

st.title("Despesas comuns")

categories = list_categories("despesa")
payments = list_payment_methods()
cat_options = {row["nome"]: int(row["id"]) for _, row in categories.iterrows()}
pay_options = {row["nome"]: int(row["id"]) for _, row in payments.iterrows()}

with st.form("despesa_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    data_despesa = col1.date_input("Data da despesa", value=date.today())
    valor = col2.number_input("Valor", min_value=0.0, step=10.0, format="%.2f")
    descricao = st.text_input("Descricao")
    col3, col4 = st.columns(2)
    categoria_nome = col3.selectbox("Categoria", list(cat_options.keys()) or [""])
    forma_nome = col4.selectbox("Forma de pagamento", list(pay_options.keys()) or [""])
    responsavel = st.text_input("Responsavel")
    recorrente = st.checkbox("Despesa recorrente")
    observacao = st.text_area("Observacao")
    submitted = st.form_submit_button("Salvar despesa")

if submitted:
    if not descricao or valor <= 0:
        st.error("Informe descricao e valor maior que zero.")
    else:
        save_expense(
            data_despesa,
            descricao,
            cat_options.get(categoria_nome),
            pay_options.get(forma_nome),
            valor,
            responsavel,
            recorrente,
            observacao,
        )
        st.success("Despesa salva.")

st.subheader("Despesas cadastradas")
df = query_df(
    """
    SELECT d.data_despesa AS data, d.descricao, COALESCE(c.nome, 'Sem categoria') AS categoria,
           COALESCE(f.nome, '-') AS forma, d.valor, d.responsavel,
           CASE WHEN d.recorrente = 1 THEN 'Sim' ELSE 'Nao' END AS recorrente
      FROM despesas d
      LEFT JOIN categorias c ON c.id = d.categoria_id
      LEFT JOIN formas_pagamento f ON f.id = d.forma_pagamento_id
     ORDER BY d.data_despesa DESC, d.id DESC
    """
)
if df.empty:
    st.info("Nenhuma despesa cadastrada ainda.")
else:
    st.dataframe(df.assign(valor=df["valor"].map(money)), use_container_width=True, hide_index=True)
