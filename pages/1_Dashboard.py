from __future__ import annotations

from datetime import date

import streamlit as st

from charts import category_bar
from database import init_db
from services import category_spending, dashboard_text, money, month_totals

init_db()

st.title("Dashboard geral")

today = date.today()
col_filter1, col_filter2 = st.columns(2)
month = col_filter1.selectbox("Mes", list(range(1, 13)), index=today.month - 1)
year = col_filter2.number_input("Ano", min_value=2020, max_value=2100, value=today.year, step=1)

totals = month_totals(month, int(year))

cols = st.columns(6)
cols[0].metric("Receita do mes", money(totals["receitas"]))
cols[1].metric("Despesas comuns", money(totals["despesas"]))
cols[2].metric("Cartoes", money(totals["cartoes"]))
cols[3].metric("Dividas fora do cartao", money(totals["dividas"]))
cols[4].metric("Saldo previsto", money(totals["saldo"]))
cols[5].metric("Renda comprometida", f"{totals['comprometido']:.1f}%")

st.subheader("Leitura simples do mes")
st.write(dashboard_text(totals, month, int(year)))

st.subheader("Gastos por categoria")
cat_df = category_spending(month, int(year))
fig = category_bar(cat_df)
if fig:
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Ainda nao ha gastos cadastrados para este mes.")

if not cat_df.empty:
    st.dataframe(cat_df.assign(valor=cat_df["valor"].map(money)), use_container_width=True, hide_index=True)
