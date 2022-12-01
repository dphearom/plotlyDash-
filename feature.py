import base64
import io
import dash
import collections
from collections import defaultdict
from dash.dependencies import Input, Output, State
from dash import dcc, html, dash_table
import dash_bootstrap_components as dbc
import plotly_express as px
import plotly.graph_objects as go

import pandas as pd


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = html.Div([
    dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select Files')
        ]),
        style={
            'width': '90%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin':"auto",
        },
        multiple=True
    ),
    html.Br(),
    html.Div([
        "Cost Input: ",
        dcc.Input(id='costInput', type='number'),
    ],style={
        'width':"90%",
        'margin':'auto'
    }),
    html.Br(),
    html.Div([
            "Requested Cost Output:",
            html.Div(
                id="costOutput",
                style={
                    'paddingLeft':'10px'
                }
            ),
            ],
            style={
                'margin':'auto',
                'width': '90%',
                'display':'flex',
                'flexDirection':'row',
            }),
    html.Br(),
    html.Div(id='output-data-upload',
            style={
                'width':'90%',
                'margin':'auto'
            }),
    html.Div(id="histogram")
])

def parse_contents(contents, filename, date):
    content_type, content_string = contents.split(',')

    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(
                io.StringIO(decoded.decode('utf-8')))
        elif 'xls' in filename:
            # Assume that the user uploaded an excel file
            df = pd.read_excel(io.BytesIO(decoded),skiprows=13)
    except Exception as e:
        print(e)
        return html.Div([
            'There was an error processing this file.'
        ])

    return df

def cleanDataFrame(dataFrame):
    dataFrame = dataFrame.drop(columns=["Publisher", "Publisher_ID", "Platform", "DOI", "Proprietary_ID",
                              "Print_ISSN", "Online_ISSN", "URI", "Metric_Type"])
    if dataFrame['Title'].iloc[-1] =="Total unique item requests:":
        dataFrame = dataFrame[:-1]
        return dataFrame
    else:
        return dataFrame

@app.callback(Output('output-data-upload', 'children'),
              Input('upload-data', 'contents'),
              State('upload-data', 'filename'),
              State('upload-data', 'last_modified'))
def update_output(list_of_contents, list_of_names, list_of_dates):
    children = [html.Div(
         dbc.Alert("Please upload a data file", color="primary", style={
            'width':'100%',
            "margin":'auto'
         })
    )]
    if list_of_contents is not None:
        for c, n, d in zip(list_of_contents, list_of_names, list_of_dates):
            df = parse_contents(c,n,d)
        df = cleanDataFrame(df)
        children = [
            html.Div([dash_table.DataTable(
            df.to_dict('records'),
            [{'name': i, 'id': i} for i in df.columns],
            style_data={
                'whiteSpace': 'None',
                'height': 'auto',
                'width': 'auto',
                'lineHeight': 1,
            },
        )],style={
            'overflowY':'Scroll',
            'height':'500px',
            'margin':'auto'})]
    return children

@app.callback(Output('costOutput','children'),
            Input('upload-data', 'contents'),
            State('upload-data', 'filename'),
            State('upload-data', 'last_modified'),
            Input('costInput','value'))

def costCalculation(list_of_contents, list_of_names, list_of_dates,costInput):
    cost = 0
    if list_of_contents is None:
        return cost
    else:
        cost = 0
        for c, n, d in zip(list_of_contents, list_of_names, list_of_dates):
            df = parse_contents(c,n,d)
        if df['Title'].iloc[-1] =="Total unique item requests:":
            cost = df['Reporting_Period_Total'].iloc[-1]
        else:
            cost = df['Reporting_Period_Total'].sum()
        if costInput is None:
            return 0
        else:
            return costInput / cost

@app.callback(
    Output("histogram","children"),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename'),
    State('upload-data', 'last_modified'),
)

def histrogram (list_of_contents, list_of_names, list_of_dates):
    children = []
    if list_of_contents is None:
        return children
    else:
        for c, n, d in zip(list_of_contents, list_of_names, list_of_dates):
            df = parse_contents(c,n,d)
        df = cleanDataFrame(df)
        titles = defaultdict(list)
        occurrences = collections.Counter(df["Reporting_Period_Total"])
        for index, row in df.iterrows():
            titles[row["Reporting_Period_Total"]].append(row['Title'])
        data = {
            "Reporting_Period_Total": [key for key, _ in occurrences.items()],
            "Occurrences": [val for _, val in occurrences.items()],
            "Titles": [val for _, val in titles.items()]}
        dff = pd.DataFrame(data)
        fig = px.bar(dff, x = "Reporting_Period_Total", y = "Occurrences", hover_name="Titles")
        #fig = px.histogram(dff, x = "Reporting_Period_Total", y = "Occurrences")
        #fig = go.Figure(data=[go.Histogram(x = dff["Reporting_Period_Total"], y=dff["Occurrences"], histfunc="count")])
        #fig.update_traces(hovertemplate = )
        children = [dcc.Graph(figure = fig)]
        return children
if __name__ == '__main__':
    app.run_server(debug=True)
