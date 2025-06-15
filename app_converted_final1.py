#!/usr/bin/env python
# coding: utf-8

# In[2]:


import dash
from dash import dcc, html
import plotly.graph_objs as go
import requests
import pandas as pd

# --- Series A: Trade Balance ---
trade_series_ids = {
    "Imports excl. ships/aircraft/diamonds": 77,
    "Exports excl. ships/aircraft/diamonds": 624440,
    "Trade Deficit excl. ships/aircraft/diamonds": 624477,
    "Trade Deficit excl. ships/aircraft/diamonds & energy": 624478
}

# --- Series B: Imports by Use ---
imports_use_ids = {
    "Raw Materials (excl. diamonds & fuel)": 51315,
    "Investment Goods (excl. ships & aircraft)": 51298,
    "Consumer Goods": 51317
}

# --- Series C: Exports by Technology Level ---
tech_series_ids = {
    "High-tech": 624416,
    "Low-tech": 624417,
    "Medium-high tech": 624418,
    "Medium-low tech": 624419
}

# --- Series D: Exports by Region (Seasonally Adjusted) ---
region_series_ids = {
    "USA (SA)": 11207,
    "EU (SA)": 11211,
    "Asia (SA)": 11209
}

# --- Generic fetch function ---
def fetch_series(series_id, label=None):
    res = requests.get("https://apis.cbs.gov.il/series/data/list", params={
        "id": series_id,
        "startPeriod": "01-2018",
        "endPeriod": "04-2025",
        "format": "json",
        "lang": "he"
    })
    res.raise_for_status()
    obs = res.json()["DataSet"]["Series"][0]["obs"]
    df = pd.DataFrame(obs)
    df.columns = ["Period", "Value"]
    df["Period"] = pd.to_datetime(df["Period"])
    df["Value"] = pd.to_numeric(df["Value"], errors="coerce") / 1000
    df.dropna(inplace=True)
    return df.rename(columns={"Value": label}) if label else df

# --- Merge multiple series into one dataframe ---
def build_merged_dataframe(series_dict):
    dfs = [fetch_series(sid, label) for label, sid in series_dict.items()]
    df = dfs[0]
    for next_df in dfs[1:]:
        df = df.merge(next_df, on="Period")
    return df

# --- Dataset Builders ---
df_trade = build_merged_dataframe(trade_series_ids)
df_imports = build_merged_dataframe(imports_use_ids)
df_tech = build_merged_dataframe(tech_series_ids)
df_region = build_merged_dataframe(region_series_ids)

# --- Dash App Layout ---
app = dash.Dash(__name__)
app.title = "Israel Trade Dashboard"

app.layout = html.Div([
    html.H2("Israel Trade Dashboard", style={"textAlign": "center"}),

    html.H4("1. Trade Balance Components (Seasonally Adjusted, $B)"),
    dcc.Graph(figure={
        "data": [go.Scatter(x=df_trade["Period"], y=df_trade[col], mode="lines+markers", name=col)
                 for col in df_trade.columns if col != "Period"],
        "layout": go.Layout(xaxis_title="Month", yaxis_title="Value (Billion USD)",
                            template="plotly_white", hovermode="x unified")
    }),

    html.H4("2. Imports by Economic Use (Seasonally Adjusted, $B)"),
    dcc.Graph(figure={
        "data": [go.Scatter(x=df_imports["Period"], y=df_imports[col], mode="lines+markers", name=col)
                 for col in df_imports.columns if col != "Period"],
        "layout": go.Layout(xaxis_title="Month", yaxis_title="Imports (Billion USD)",
                            template="plotly_white", hovermode="x unified")
    }),

    html.H4("3. Exports by Technology Level (Seasonally Adjusted, $B)"),
    dcc.Graph(figure={
        "data": [go.Scatter(x=df_tech["Period"], y=df_tech[col], mode="lines+markers", name=col)
                 for col in df_tech.columns if col != "Period"],
        "layout": go.Layout(xaxis_title="Month", yaxis_title="Exports (Billion USD)",
                            template="plotly_white", hovermode="x unified")
    }),

    html.H4("4. Exports by Region – USA, EU, Asia (Seasonally Adjusted, $B)"),
    dcc.Graph(figure={
        "data": [go.Scatter(x=df_region["Period"], y=df_region[col], mode="lines+markers", name=col)
                 for col in df_region.columns if col != "Period"],
        "layout": go.Layout(xaxis_title="Month", yaxis_title="Exports (Billion USD)",
                            template="plotly_white", hovermode="x unified")
    })
])

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8050))  # Use Render's assigned port
    app.run(host="0.0.0.0", port=port)

