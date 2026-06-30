from __future__ import annotations

import pandas as pd
import plotly.express as px


def category_bar(df: pd.DataFrame):
    if df.empty:
        return None
    return px.bar(
        df,
        x="valor",
        y="categoria",
        orientation="h",
        text_auto=".2s",
        labels={"valor": "Valor", "categoria": "Categoria"},
        color_discrete_sequence=["#2f6f73"],
    ).update_layout(yaxis={"categoryorder": "total ascending"}, height=420)


def card_compare(df: pd.DataFrame):
    if df.empty:
        return None
    return px.bar(
        df,
        x="Cartao",
        y="Total da fatura",
        labels={"Cartao": "Cartao", "Total da fatura": "Total da fatura"},
        color_discrete_sequence=["#5b6c8f"],
    ).update_layout(height=380)


def card_category_pie(df: pd.DataFrame):
    if df.empty:
        return None
    return px.pie(
        df,
        values="valor",
        names="categoria",
        hole=0.45,
        color_discrete_sequence=px.colors.qualitative.Set2,
    ).update_layout(height=380)


def projection_line(df: pd.DataFrame, y: str):
    if df.empty:
        return None
    return px.line(df, x="Mes", y=y, markers=True).update_layout(height=380)
