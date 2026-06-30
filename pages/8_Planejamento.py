from __future__ import annotations

from datetime import date

import streamlit as st

from charts import projection_line
from database import init_db
from services import money, planning_projection

init_db()

st.title("Planejamento")

today = date.today()
col1, col2, col3 = st.columns(3)
month = col1.selectbox("Mes inicial", list(range(1, 13)), index=today.month - 1)
year = col2.number_input("Ano inicial", min_value=2020, max_value=2100, value=today.year)
months = col3.selectbox("Periodo", [6, 12], index=1)

df = planning_projection(int(month), int(year), int(months))

st.subheader("Projecao")
fig = projection_line(df, "Saldo previsto")
if fig:
    st.plotly_chart(fig, use_container_width=True)

view = df.copy()
for col in ["Receita prevista", "Despesas comuns", "Cartoes", "Dividas fora do cartao", "Saldo previsto"]:
    view[col] = view[col].map(money)
st.dataframe(view, use_container_width=True, hide_index=True)
