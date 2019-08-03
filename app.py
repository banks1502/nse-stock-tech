import numpy as np
import dash
import pandas as pd
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import dash_table
import sys
from pandas_datareader import data
import matplotlib.pyplot as plt
import datetime
import plotly.graph_objs as go
from plotly import tools
import chart_studio.plotly as py
from flask import Flask
import os

now = str(datetime.datetime.now())

start_date = '2018-01-01'
end_date = now

df = data.DataReader('INFY.NS', 'yahoo', start_date, end_date).round(1)
df = df.reset_index()
df.sort_values(by=['Date'], inplace=True, ascending=False)

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css', dbc.themes.BOOTSTRAP, dbc.themes.GRID, dbc.themes.CERULEAN]

#server = Flask(__name__)
#server.secret_key = os.environ.get('secret_key', 'secret')
app = dash.Dash(name = __name__, external_stylesheets=external_stylesheets)
server =app.server

dropdown = dcc.Dropdown(
    id='dropdown',
    options=[
            {'label': 'Infosys', 'value': 'INFY.NS'},
            {'label': 'Reliance', 'value': 'RELIANCE.NS'},
            {'label': 'Tata Consultancy Services', 'value': 'TCS.NS'},
            {'label': 'HDFC Bank', 'value': 'HDFCBANK.NS'},
            {'label': 'HUL', 'value': 'HINDUNILVR.NS'},
        ],
    value = 'INFY.NS'
)

date = html.Div([
    dcc.Input(id='start-date', type='text', value='2018-01-01'),
    dcc.Input(id='end-date', type='text', value=str(datetime.datetime.now()).split()[0]),
    html.Button(id='submit-button', n_clicks=0, children='Submit dates')
])



PAGE_SIZE = 10
data_table = dash_table.DataTable(
    id='table',
    columns=[{'name': i, 'id': i} for i in df.columns],
    data=df.to_dict('rows'),
    style_table={
        'maxHeight': '10',
        'overflowY': 'scroll'
    },
    page_current=0,
    page_size=PAGE_SIZE,
    page_action='custom'    
)

graph = dcc.Graph(
    id='graph'
)

checklist = dbc.FormGroup(
    [
        dbc.Label('Choose indicators', color='blue', size=20),
        dbc.Checklist(
            options=[
                {'label': 'Volume', 'value': 'Volume'},
                {'label': 'Bollinger Bands', 'value': 'Bollinger'},
                {'label': 'Stochastic Oscillator', 'value': 'Stoch'}
            ],
            inline=True,
            style={'width':5000, 'color':'blue'},
            value=[],
            id='checklist-input',
        ),
    ]
)




app.layout = html.Div([dropdown, date, data_table, checklist, graph])

@app.callback(
    Output('table', 'data'),
    [Input('table', 'page_current'),
     Input('table','page_size'),
     Input('dropdown', 'value'),
     Input('submit-button', 'n_clicks')],
    [State('start-date', 'value'),
     State('end-date', 'value')])
def update_table(page_current,page_size, stock, n_clicks, start_date, end_date):
    if n_clicks > 0:
        df = data.DataReader(stock, 'yahoo', start_date, end_date).round(1)
        df = df.reset_index()
        df.sort_values(by=['Date'], inplace=True, ascending=False)
    else:
        df = data.DataReader(stock, 'yahoo', '2018-01-01', str(datetime.datetime.now()).split()[0]).round(1)
        df = df.reset_index()
        df.sort_values(by=['Date'], inplace=True, ascending=False)
    return df.iloc[
        page_current*page_size:(page_current+ 1)*page_size
    ].to_dict('rows')

@app.callback(
    Output('graph', 'figure'),
    [Input('dropdown', 'value'),
     Input('checklist-input', 'value'),
     Input('submit-button', 'n_clicks')],
    [State('start-date', 'value'),
     State('end-date', 'value')])
def update_graph(stock, indicators, n_clicks, start_date, end_date):
    if n_clicks > 0:
        df = data.DataReader(stock, 'yahoo', start_date, end_date).round(1)
        dff = df.reset_index()
    else:
        df = data.DataReader(stock, 'yahoo', '2018-01-01', str(datetime.datetime.now()).split()[0]).round(1)
        dff = df.reset_index()

    trace1 = {'x':dff['Date'],
              'open':dff['Open'],
              'low':dff['Low'],
              'high':dff['High'],
              'close':dff['Close'],
              'increasing':{'line': {'color': '#00CC94'}},
              'decreasing':{'line': {'color': '#F50030'}},
              'name': stock,
              'yaxis':'y1',
              'type':'candlestick',
              'showlegend':False
              }

    if 'Volume' in indicators:
        trace2 = {'x':dff['Date'],
                  'y':dff['Volume'],
                  'name':'Volume',
                  'yaxis':'y2',
                  'type':'bar'}
    else:
        trace2 = {}

    if 'Bollinger' in indicators:
        MA = dff['Close'].rolling(window=20).mean()
        STD = dff['Close'].rolling(window=20).std()
        upper_band = MA + (STD*2)
        lower_band = MA - (STD*2)
        middle_band = MA
        trace3 = {'x':dff['Date'],
                  'y':upper_band,
                  'line':{'width':1},
                  'hoverinfo':'none',
                  'legendgroup':'Bollinger Bands',
                  'marker':{'color':'green'},
                  'name':'Bollinger Bands',
                  'mode':'lines',
                  'type':'scatter',
                  'yaxis':'y1'}
        trace4 = {'x':dff['Date'],
                  'y':lower_band,
                  'line': {'width':1},
                  'hoverinfo':'none',
                  'legendgroup':'Bollinger Bands',
                  'showlegend': False,
                  'marker':{'color':'green'},
                  'mode':'lines',
                  'type':'scatter',
                  'yaxis':'y1'}
        trace5 = {'x':dff['Date'],
                  'y':middle_band,
                  'line': {'width':1},
                  'hoverinfo':'none',
                  'legendgroup':'Bollinger Bands',
                  'showlegend': False,
                  'marker':{'color':'yellow'},
                  'mode':'lines',
                  'type':'scatter',
                  'yaxis':'y1'}
    else:
        trace3 = {}
        trace4 = {}
        trace5 = {}

    if 'Stoch' in indicators:
        L14 = dff['Low'].rolling(window=14).min()
        H14 = dff['High'].rolling(window=14).max()
        dff['%k'] = 100*((dff['Close'] - L14) / (H14 - L14))
        dff['%d'] = dff['%k'].rolling(window=3).mean()
        trace6 = {'x':dff['Date'],
                  'y':dff['%k'],
                  'line': {'width': 1},
                  'legendgroup':'Stochastic Oscilator',
                  'name':'Stochastic Oscillator',
                  'mode':'lines',
                  'type':'scatter',
                  'yaxis':'y3'}
        trace7 = {'x':dff['Date'],
                  'y':dff['%d'],
                  'line': {'width': 1},
                  'legendgroup':'Stochastic Oscilator',
                  'showlegend':False,
                  'mode':'lines',
                  'type':'scatter',
                  'yaxis':'y3'}
    else:
        trace6 = {}
        trace7 = {}

    dat = [trace1, trace2, trace3, trace4, trace5, trace6, trace7]
    layout = go.Layout(
        title='Chart for ' + stock,
        xaxis={'rangeslider':{'visible':False}},
        legend={'x':0,
                'y':1,
                'bgcolor':'#E2E2E2',
                'bordercolor':'#FFFFFF',
                'borderwidth':2,
                'font':{'family':'sans-serif',
                        'size':8,
                        'color':'#000'}},
        yaxis={'title': 'Stock price',
               'domain': [0.5, 1],
               'side': 'left',
               #'overlaying': 'y2',
               'showticklabels': True},
        yaxis2={'side': 'right',
                'domain': [0.25, 0.5],
                'showticklabels': False,
                'showgrid': False},
        yaxis3={'side':'left',
                'domain':[0, 0.25],
                'showticklabels':True}
    )
    return go.Figure(data=dat, layout=layout)


if __name__ == '__main__':
    app.run_server(debug=True)

