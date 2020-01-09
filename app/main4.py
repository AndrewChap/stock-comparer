import logging
from flask import Flask

# Dash for plots
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
# Numpy for arrays
import numpy as np
# Pandas for reading stocks
import pandas as pd
import pandas_datareader
import pandas_datareader.data as web
from pandas import Series, DataFrame
# Datetime for dealing with stock dates
from datetime import datetime
from dateutil.relativedelta import relativedelta
# pdb for debugging
import pdb
from collections import OrderedDict
db = pdb.set_trace

server = Flask(__name__)

# Create stock objects
class Stock:
    def __init__(self,name,dateBegin,dateEnd):
        self.name = name
        self.dateBegin = dateBegin
        self.dateEnd = dateEnd
        self.df = web.DataReader(self.name, 'yahoo', dateBegin, dateEnd)
        self.vals = self.df['Adj Close'].values
        self.time = self.df.index
        self.valsNorm = self.vals/self.vals[0]
    def norm_by_date(self,normIndex):
        self.valsNorm = self.vals/self.vals[normIndex]
    def __repr__(self):
        return 'stock({},{},{})'.format(self.name,self.dateBegin,self.dateEnd)
        
class Stocks:
    def __init__(
        self,
        listOfStockSymbols = [],
        dateBegin = datetime.now() - relativedelta(years=1),
        dateEnd = datetime.now()):
        self.dateBegin = dateBegin
        self.dateEnd = dateEnd
        self.time = None
        self.listOfStocks = []
        self.listOfStockSymbols = listOfStockSymbols
        for stockSymbol in listOfStockSymbols:
            try:
                stock = Stock(stockSymbol,dateBegin=dateBegin,dateEnd=dateEnd)
                self.listOfStocks.append(stock)
                self.set_global_time(othertime = stock.time)
            except pandas_datareader._utils.RemoteDataError as e:
                print(e)
    def set_global_time(self,othertime):
        if self.time is None:
            self.time = othertime
        else:
            if othertime[0] < self.time[0]:
                for i in range(len(othertime)):
                    if othertime[i] == self.time[0]:
                        index = i-1
                self.time = othertime[0:index] + self.time
            if othertime[-1] > self.time[-1]:
                for i in range(len(othertime)):
                    if othertime[-1-i] == self.time[-1]:
                        index = i-1
                self.time = self.time + othertime[index:]

    def set_dates(self,dateBegin,dateEnd):
        if self.dateBegin != dateBegin and self.dateEnd != dateEnd:
            print('setting dates!')
            self.dateBegin = dateBegin
            self.dateEnd = dateEnd
            self.listOfStocks = []
            self.listOfStockSymbols = []
    def update_list_of_stock_symbols(self,newListOfStockSymbols):
        # Create new list from old list only if items' symbols are in input list:
        newListOfStocks = [stock for stock in self.listOfStocks if stock.name in newListOfStockSymbols]
        self.listOfStocks = newListOfStocks
         
        # Add new stocks to list that are not in the original list
        for stockSymbol in newListOfStockSymbols:
            if stockSymbol not in self.listOfStockSymbols:
                print('adding stock {}'.format(stockSymbol))
                self.listOfStocks.append(Stock(name = stockSymbol, dateBegin = self.dateBegin, dateEnd = self.dateEnd))
        self.listOfStockSymbols = newListOfStockSymbols

        # Correct the order
        newListOfStocks = []
        for stockSymbol in newListOfStockSymbols:
            for stock in self.listOfStocks:
                if stock.name == stockSymbol:
                    newListOfStocks.append(stock)
                    break
        self.listOfStocks = newListOfStocks        

    def norm_by_date(self,normIndex):
        for stock in self.listOfStocks:
            stock.norm_by_date(normIndex)


initialStockSymbols='VTI\nBND'
listOfStockSymbols = initialStockSymbols.strip('\n').split('\n')
#Set start and end as one year ago to now
dateEnd = datetime.now()
dateBegin = dateEnd - relativedelta(years=1)
stocks = Stocks(listOfStockSymbols = listOfStockSymbols, dateBegin = dateBegin.date(), dateEnd = dateEnd.date())
#stocks.set_dates(dateBegin = dateBegin.date(), dateEnd = dateEnd.date())
#print("before:{} ".format(stocks.listOfStocks))
#stocks.update_list_of_stock_symbols(newListOfStockSymbols = listOfStockSymbols)


dashApp = dash.Dash(
    __name__,
    server=server,
    #routes_pathname_prefix='/dash/'
)
dashApp.scripts.config.serve_locally = True
dashApp.config.suppress_callback_exceptions = True
#plotButton = html.Button(id='plotstocks',n_clicks=0,children="Plot 'em!")
#
#datesBox = html.Div(
#        [
#            html.Label('Starting Date'),
#            dcc.Input(id='dateBegin',className='date',
#                value=(datetime.now()-relativedelta(years=1)).strftime("%m/%d/%Y")),
#            html.Label('End Date'),
#            dcc.Input(id='dateEnd',className='date',
#                value=datetime.now().strftime("%m/%d/%Y")),
#            ], className='pinput pretty-container'
#        )
#stocksBox = html.Div(
#        [
#            html.Label('Stocks to Plot'),
#            dcc.Textarea(id='stocksbox',autoFocus='true',className='stocksbox',value='VTI\nBND'),
#        ], className='pinput pretty-container'
#)
#
#bothbox = html.Div(
#    [
#        html.Label('Stocks to Plot'),
#        dcc.Textarea(id='stocksbox',autoFocus='true',className='stocksbox',rows=8,value='VTI\nBND',style={'height':'100px'}),
#        html.Label('Starting Date'),
#        dcc.Input(id='dateBegin',className='date',
#            value=(datetime.now()-relativedelta(years=1)).strftime("%m/%d/%Y")),
#        html.Label('End Date'),
#        dcc.Input(id='dateEnd',className='date',
#            value=datetime.now().strftime("%m/%d/%Y")),
#        plotButton,
#    ], className='pinput pretty-container'
#)
plotButton = html.Button(id='plotstocks',n_clicks=0,children="Plot 'em!")

def format_date(date):
    return date.strftime("%m/%d/%Y")

datesBox = html.Div(
        [
            html.Label('Starting Date'),
            dcc.Input(id='dateBegin',className='date',
                value=format_date(datetime.now()-relativedelta(years=1))),
            html.Label('End Date'),
            dcc.Input(id='dateEnd',className='date',
                value=format_date(datetime.now())),
            ], className='pinput pretty-container'
        )
stocksBox = html.Div(
        [
            html.Label('Stocks to Plot'),
            dcc.Textarea(id='stocksbox',autoFocus='true',className='stocksbox',value='VTI\nBND'),
        ], className='pinput pretty-container'
)

bothbox = html.Div(
    [
        html.Label('Stocks to Plot'),
        dcc.Textarea(id='stocksbox',autoFocus='true',className='stocksbox',rows=8,value=initialStockSymbols,style={'height':'100px'}),
        html.Label('Starting Date'),
        dcc.Input(id='dateBegin',className='date',
            value=(datetime.now()-relativedelta(years=1)).strftime("%m/%d/%Y")),
        html.Label('End Date'),
        dcc.Input(id='dateEnd',className='date',
            value=datetime.now().strftime("%m/%d/%Y")),
        plotButton,
    ], className='pinput pretty-container'
)

topBar = html.Div(
            [
                #html.Button(id='plotstocks',n_clicks=0,children='Plot them stocks!'),
                html.Img(src='/assets/splogo.png'),
                html.H1(
                    "stoock-plotter.com!",
                    className='title',
                ),
                html.H3(
                    "By Andrew Chap",
                    className='author',
                )
            ],
            className = 'title-nav',
        ),
leftPanel = html.Div(
    html.Div([stocksBox, datesBox],className='input-wrapper'),
    className='left',
)
# https://stackoverflow.com/questions/1260122/expand-a-div-to-fill-the-remaining-width
# Right panel: the output plot
rightPanel = html.Div(
    html.Div(    
        dcc.Graph( id = 'main-plot',style={'width':'100%'}),
        className='panel',
    ),
    className='right',
)

dashApp.layout = html.Div(
    [
        html.Div(
            [
                html.Div(
                    [
                        #html.Button(id='plotstocks',n_clicks=0,children='Plot them stocks!'),
                        html.Img(src='/assets/splogo.png', style={'width':'40px'}),
                        html.H1(
                            "stock-plotter.com!",
                            className='title',
                            ),
                        html.H3(
                            "By Andrew Chap",
                            className='author',
                            )
                        ],
                    className = 'title-nav',
                    ),
                html.Div(
                    bothbox,
                    className='leftside'),
                html.Div(
                    [
                        dcc.Graph(id='main-plot',style={'width':'100%'}),
                        html.Div(
                            [
                                html.Div(id='slider-var'),
                                html.Div(id='slider-output-container')
                            ]
                        )
                    ],
                    className='rightside'),
            ],
            className = 'contents',
        ),
    ]
)

@dashApp.callback(
    Output('slider-output-container', 'children'),
    [Input('norm-slider', 'value')],
    [State('dateBegin','value'),
     State('dateEnd'  ,'value')])
def update_output(sliderValue,dateBeginAsString,dateEndAsString):
    normDate = stocks.time[sliderValue]
    #dateBegin,dateEnd = parse_dates(dateBeginAsString,dateEndAsString)
    #normDate = dateBegin + relativedelta(days=sliderValue)
    return 'Normalization date: {}'.format(format_date(normDate))

def parse_dates(dateBeginAsString,dateEndAsString):
    dateBeginAsList = dateBeginAsString.split('/')
    dateEndAsList = dateEndAsString.split('/')
    dateBegin = datetime(int(dateBeginAsList[2]),int(dateBeginAsList[0]),int(dateBeginAsList[1]))
    dateEnd = datetime(int(dateEndAsList[2]),int(dateEndAsList[0]),int(dateEndAsList[1]))
    return dateBegin,dateEnd

@dashApp.callback(
        Output('main-plot'  , 'figure'),
        [Input('plotstocks' , 'n_clicks'),
         Input('norm-slider', 'value')],
        [State('stocksbox'  , 'value'),
         State('dateBegin'  , 'value'),
         State('dateEnd'    , 'value')]
    )
def update_figure(n_clicks,sliderValue,stocksbox,dateBeginAsString,dateEndAsString):
    dateBegin,dateEnd = parse_dates(dateBeginAsString,dateEndAsString)
    normDate = dateBegin + relativedelta(days=sliderValue)
    normDate = stocks.time[sliderValue]
    listOfStockSymbols = stocksbox.strip('\n').split('\n')
    print(listOfStockSymbols)
    stocks.set_dates(dateBegin = dateBegin.date(), dateEnd = dateEnd.date())
    print("before:{} ".format(stocks.listOfStocks))
    stocks.update_list_of_stock_symbols(newListOfStockSymbols = listOfStockSymbols)
    print("after: {} ".format(stocks.listOfStocks))
    stocks.norm_by_date(normIndex = sliderValue)
    data = [ 
            {
                'x': stock.time,
                'y': stock.valsNorm,
                'name': stock.name,
            } for stock in stocks.listOfStocks
        ]
    maxY = max([max(stock.valsNorm) for stock in stocks.listOfStocks])
    minY = min([min(stock.valsNorm) for stock in stocks.listOfStocks])
    data.append(
            {
                'x': [normDate, normDate],
                'y': [minY, maxY],
                'mode': 'lines',
                'line': {'color': 'rgba(0,0,0,0.18)'},
                'showlegend': False,
            }
    )
    return {
        'data': data,
        'layout': {
            'yaxis': {'range': [minY,maxY]},
            'margin': {'l': 40, 'r': 40, 't': 30, 'b': 30},
        }
    }

@dashApp.callback(
        Output('slider-var', 'children'),
        [Input('plotstocks' , 'n_clicks')],
        [State('dateBegin', 'value'),
         State('dateEnd'  , 'value')]   
    )
def update_slider(n_clicks,dateBeginAsString,dateEndAsString):
    dateBegin,dateEnd = parse_dates(dateBeginAsString,dateEndAsString)
    numberOfDays = abs((dateBegin - dateEnd).days)
    print('totalDays is {}'.format(numberOfDays))
    len(stocks.time)

    slider = dcc.Slider(
        id='norm-slider',
        min=0,
        #max=numberOfDays,
        max=len(stocks.time)-1,
        step=1,
        value=0,
    )
    return slider


@server.errorhandler(500)
def server_error(e):
    logging.exception('An error occurred during a request.')
    return """
    An internal error occurred: <pre>{}</pre>
    See logs for full stacktrace.
    """.format(e), 500


if __name__ == '__main__':
    # This is used when running locally. Gunicorn is used to run the
    # application on Google App Engine. See entrypoint in app.yaml.
    #dashApp.run_server(host='127.0.0.1', port=8080, debug=True)
    dashApp.run_server(debug=True)
    #server.run(host='127.0.0.1', port=8080, debug=True)


# [END gae_flex_quickstart]
