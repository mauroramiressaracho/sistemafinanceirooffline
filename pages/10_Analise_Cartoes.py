from __future__ import annotations

from datetime import date

import streamlit as st

from charts import card_category_pie, card_compare
from database import init_db
from services import card_analysis, invoice_details, money

init_db()

st.title("Analise dos cartoes")

today = date.today()
col1, col2 = st.columns(2)
month = col1.selectbox("Mes da fatura", list(range(1, 13)), index=today.month - 1)
year = col2.number_input("Ano", min_value=2020, max_value=2100, value=today.year)

analysis = card_analysis(int(month), int(year))

if analysis.empty:
    st.info("Nenhum cartao cadastrado ainda.")
else:
    view = analysis.copy()
    for col in ["Total da fatura", "Total parcelado", "Total a vista", "Alivio proximo mes"]:
        view[col] = view[col].map(money)
    st.dataframe(view, use_container_width=True, hide_index=True)

    fig = card_compare(analysis)
    if fig:
        st.plotly_chart(fig, use_container_width=True)

details = invoice_details(int(month), int(year))
if not details.empty:
    by_category = details.groupby("categoria", as_index=False)["valor"].sum().sort_values("valor", ascending=False)
    st.subheader("Categorias dentro dos cartoes")
    fig_cat = card_category_pie(by_category)
    if fig_cat:
        st.plotly_chart(fig_cat, use_container_width=True)
    st.dataframe(by_category.assign(valor=by_category["valor"].map(money)), use_container_width=True, hide_index=True)
else:
    st.info("Nao ha parcelas de cartao no mes selecionado.")
