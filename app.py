# dashboard_btc.py

import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from statsmodels.tsa.stattools import acf, pacf
from dash import Dash, dcc, html, dash_table
from dash.dependencies import Input, Output
import numpy as np

# Descargar datos de Bitcoin
btc = yf.download('BTC-USD', start='2018-12-01', progress=False)
df = btc.reset_index()
df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]

# Renombrar columnas
df.rename(columns={
    "Date": "Fecha",
    "Open": "Apertura",
    "High": "Maximo",
    "Low": "Minimo",
    "Close": "Cierre",
    "Volume": "Volumen"
}, inplace=True)

# Colores personalizados
colors = {
    "background": "#f8fbe8",
    "text": "#1a1a1a",
    "accent": "#2d572c",
    "secondary": "#ffd700",
    "table_bg": "#ffffff"
}

# ACF y PACF
def generar_acf_pacf(series, nlags=40):
    acf_vals = acf(series, nlags=nlags)
    pacf_vals = pacf(series, nlags=nlags)
    lags = np.arange(len(acf_vals))

    acf_fig = go.Figure()
    acf_fig.add_trace(go.Bar(x=lags, y=acf_vals, marker_color=colors["accent"]))
    acf_fig.update_layout(title="ACF del Precio", template="plotly_white")

    pacf_fig = go.Figure()
    pacf_fig.add_trace(go.Bar(x=lags, y=pacf_vals, marker_color=colors["secondary"]))
    pacf_fig.update_layout(title="PACF del Precio", template="plotly_white")

    return acf_fig, pacf_fig

acf_fig, pacf_fig = generar_acf_pacf(df['Cierre'].dropna())

# App Dash
app = Dash(__name__)
app.title = "Dashboard BTC"

app.layout = html.Div(style={
    'backgroundColor': colors["background"],
    'color': colors["text"],
    'font-family': 'Segoe UI, sans-serif'
}, children=[
    html.H1("📊 Dashboard de Análisis BTC-USD", style={
        'textAlign': 'center',
        'color': colors["accent"],
        'paddingTop': '20px'
    }),

    dcc.Tabs([
        dcc.Tab(label='📌 Introducción', children=[
            html.Div([
                html.Div([
                    html.H2("¿De qué trata este dashboard?", style={
                        'color': colors["accent"],
                        'textAlign': 'center',
                        'marginBottom': '20px'
                    }),
                    html.P(
                        "Este dashboard analiza la evolución histórica del precio de Bitcoin (BTC) en dólares estadounidenses (USD), "
                        "utilizando datos extraídos desde Yahoo Finance. La base contiene información desde diciembre de 2018 hasta abril de 2025, "
                        "incluyendo precios de apertura, cierre, máximos, mínimos, volumen y precio ajustado. "
                        "A través de distintas visualizaciones, se busca entender mejor su comportamiento, identificar patrones y analizar su estructura temporal.",
                        style={
                            'fontSize': '18px',
                            'textAlign': 'justify',
                            'lineHeight': '1.7',
                            'color': colors["text"]
                        }
                    )
                ], style={
                    'backgroundColor': 'white',
                    'padding': '30px',
                    'borderRadius': '12px',
                    'boxShadow': '0px 4px 8px rgba(0, 0, 0, 0.1)',
                    'maxWidth': '90%',
                    'margin': '30px auto'
                })
            ])
        ]),

        dcc.Tab(label='📈 Precio BTC', children=[
            html.Div([
                dcc.Dropdown(
                    id='price-type',
                    options=[{'label': i, 'value': i} for i in ['Apertura', 'Maximo', 'Minimo', 'Cierre']],
                    value='Cierre',
                    clearable=False,
                    style={'width': '40%', 'margin': '0 auto'}
                ),
                dcc.Graph(id='price-graph', config={'displayModeBar': False})
            ], style={'padding': '30px'})
        ]),

        dcc.Tab(label='📋 Tabla Estadística', children=[
            html.Div(id='tabla-resumen', style={'padding': '30px'})
        ]),

        dcc.Tab(label='📊 ACF y PACF', children=[
            html.Div([
                dcc.Graph(figure=acf_fig),
                dcc.Graph(figure=pacf_fig)
            ], style={'padding': '30px'})
        ]),

        dcc.Tab(label='🔍 Definición de Variables', children=[
            html.Div([
                dash_table.DataTable(
                    data=pd.DataFrame({
                        "Variable": ["Fecha", "Apertura", "Maximo", "Minimo", "Cierre", "Volumen"],
                        "Descripción": [
                            "Fecha del registro.",
                            "Precio de apertura (USD).",
                            "Precio máximo del día.",
                            "Precio mínimo del día.",
                            "Precio de cierre del día.",
                            "Volumen total operado."
                        ]
                    }).to_dict("records"),
                    columns=[{"name": i, "id": i} for i in ["Variable", "Descripción"]],
                    style_cell={
                        'textAlign': 'left',
                        'backgroundColor': colors["table_bg"],
                        'color': colors["text"]
                    },
                    style_header={
                        'backgroundColor': colors["accent"],
                        'color': 'white',
                        'fontWeight': 'bold'
                    },
                    style_table={'overflowX': 'auto'}
                )
            ], style={'padding': '30px'})
        ])
    ])
])

@app.callback(
    Output('price-graph', 'figure'),
    Input('price-type', 'value')
)
def update_graph(price_type):
    fig = go.Figure()
    if price_type in df.columns and not df[price_type].isnull().all():
        fig.add_trace(go.Scatter(
            x=pd.to_datetime(df["Fecha"]),
            y=df[price_type],
            mode="lines",
            line=dict(color=colors["text"]),
            name=price_type
        ))
        fig.update_layout(
            title="📈 Evolución del Precio de Bitcoin (USD)",
            xaxis_title="Fecha",
            yaxis_title="Precio (USD)",
            template="plotly_white"
        )
    else:
        fig.update_layout(
            title="❌ Datos no disponibles",
            template="plotly_white"
        )
    return fig

@app.callback(
    Output('tabla-resumen', 'children'),
    Input('price-type', 'value')
)
def update_table(_):
    resumen = df.describe().reset_index()
    resumen.columns = resumen.columns.map(str)
    return dash_table.DataTable(
        data=resumen.to_dict("records"),
        columns=[{"name": i, "id": i} for i in resumen.columns],
        style_table={'overflowX': 'auto'},
        style_cell={
            'textAlign': 'center',
            'backgroundColor': colors["table_bg"],
            'color': colors["text"]
        },
        style_header={
            'backgroundColor': colors["accent"],
            'color': 'black',
            'fontWeight': 'bold'
        }
    )

if __name__ == '__main__':
    app.run(debug=True)

server = app.server