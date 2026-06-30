from __future__ import annotations

from datetime import date

import streamlit as st

from charts import projection_line
from database import init_db
from services import money, relief_projection

init_db()

st.title("Alivio financeiro")

today = date.today()
col1, col2 = st.columns(2)
month = col1.selectbox("Mes inicial", list(range(1, 13)), index=today.month - 1)
year = col2.number_input("Ano inicial", min_value=2020, max_value=2100, value=today.year)

df = relief_projection(int(month), int(year), 12)

if not df.empty:
    best = df[df["Alivio acumulado"] > 0]
    if best.empty:
        st.info("Nos proximos 12 meses, nenhuma compra parcelada cadastrada chega ao fim.")
    else:
        row = best.iloc[0]
        st.success(
            f"A partir de {row['Mes']}, se nenhuma nova compra parcelada for feita, "
            f"sua despesa mensal com parcelas comeca a reduzir. Alivio acumulado: {money(row['Alivio acumulado'])}."
        )

fig = projection_line(df, "Alivio acumulado")
if fig:
    st.plotly_chart(fig, use_container_width=True)

view = df.copy()
view["Alivio do mes"] = view["Alivio do mes"].map(money)
view["Alivio acumulado"] = view["Alivio acumulado"].map(money)
st.dataframe(view, use_container_width=True, hide_index=True)
