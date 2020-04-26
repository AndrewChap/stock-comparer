import logging
from flask import Flask

# Dash for plots
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
# Numpy for arrays
import numpy as np

import yfinance as yf

from pandas import Series, DataFrame
# Datetime for dealing with stock dates
from datetime import datetime
import datetime as dt
from dateutil.relativedelta import relativedelta
# pdb for debugging
import pdb
from collections import OrderedDict
db = pdb.set_trace

server = Flask(__name__)

# Create stock objects
class Stock:
    def __init__(self,name,dateBegin,dateEnd,comparator=None):
        self.name = name
        self.dateBegin = dateBegin
        self.dateEnd = dateEnd
        self.comparator = comparator
        #self.df = pdr.get_data_yahoo(self.name, dateBegin, dateEnd)
        self.ticker = yf.Ticker(self.name)
        self.df = self.ticker.history(period='1d', start=dateBegin, end=dateEnd)
        self.vals = self.df['Close'].values
        self.time = self.df.index
        self.norm_by_index(0)
        self.update_comparator(comparator) # if comparator is None, this just sets valsCompared=valsNorm
        
    def norm_by_index(self,normIndex):
        self.valsNorm = self.vals/self.vals[normIndex]
    def update_comparator(self,comparator):
        if comparator:
            self.valsCompared = [v/n for v,n in zip(self.valsNorm,comparator.valsNorm)]
        else:
            self.valsCompared = self.valsNorm
    def remove_comparator(self):
        self.valsCompared = self.valsNorm

    def norm_by_date(self,dateNorm):
        dates = [ind.to_pydatetime() for ind in self.df.index]
        # Find closest date to the input date
        normIndex = 0
        for i,date in enumerate(dates):
            if dateNorm <= date:
                dateNorm = date
                normIndex = i
                break
        # Only needed if we wanted to return what date we are actually norming on
        if normIndex == 0:
            dateNorm = dates[0]
        self.norm_by_index(normIndex)
        #self.valsNorm = self.vals/self.vals[normIndex]
    def __repr__(self):
        return 'stock({},{},{})'.format(self.name,self.dateBegin,self.dateEnd)
        
class Stocks:
    def __init__(
        self,
        listOfStockSymbols = [],
        dateBegin = datetime.now() - relativedelta(years=1),
        dateEnd = datetime.now()
    ):
        self.dateBegin = dateBegin
        self.dateEnd = dateEnd
        self.time = None
        self.comparatorName = ''
        self.listOfStocks = []
        self.listOfStockSymbols = listOfStockSymbols
        for stockSymbol in listOfStockSymbols:
            stock = Stock(stockSymbol,dateBegin=dateBegin,dateEnd=dateEnd)
            self.listOfStocks.append(stock)
            self.set_global_time(othertime = stock.time)
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
        if (self.dateBegin != dateBegin) or (self.dateEnd != dateEnd):
            self.dateBegin = dateBegin
            self.dateEnd = dateEnd
            self.listOfStocks = []
            self.listOfStockSymbols = []
            self.comparator = None
            self.comparatorName = ''
        else:
            pass
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

    def update_comparators(self,comparatorName):
        if self.comparatorName != comparatorName:
            if comparatorName == '':
                for stock in self.listOfStocks:
                    stock.remove_comparator()
            else:
                self.comparatorName = comparatorName
                # Create a new stock for the comparator.  Note that the comparator itself cannot *have* a comparator
                self.comparator = Stock(name=comparatorName,dateBegin=self.dateBegin,dateEnd=self.dateEnd,comparator=None)
                for stock in self.listOfStocks:
                    stock.update_comparator(self.comparator)

    #def norm_by_index(self,normIndex):
    #    for stock in self.listOfStocks:
    #        stock.norm_by_index(normIndex)
    def norm_by_date(self,dateNorm):
        for stock in self.listOfStocks:
            stock.norm_by_date(dateNorm)

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
dashApp.title = 'Stock Plotter'
dashApp.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        <script data-ad-client="ca-pub-5585892045097111" async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js"></script>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''


dashApp.scripts.config.serve_locally = True
dashApp.config.suppress_callback_exceptions = True


plotButton = html.Button(id='plotstocks',className='plotButton',
    n_clicks=0,children="re-plot")

def format_date(date):
    return date.strftime("%m/%d/%Y")

def add_explanation(obj, text=""):
    """ add hover-explanation on mouse-over for objects, automatic for dropdowns """
    if (not text):
        try:
            title = obj.placeholder
        except:
            title = "??"
    return html.Abbr(obj, title=title)

add_explanation(
    dcc.Dropdown(
        placeholder="Select your desired elements",
        id="sample_element",
        options=['a','b','c']
    )
)

def tooltip(text):
    return html.Div(['?',
            html.Span(text,className='tooltiptext')],
            className="tooltip")

def tooltip_label(label,tip):
    return html.Label([
            html.Div(label,className='leftLabel'),
            html.Div(['?',
                html.Span(tip,className='tooltiptext')],
                className="tooltip")
            ],
            className='inputLabel')

bothbox = html.Div(
    [
        tooltip_label('Stocks','List of stocks tickers to plot'),
        dcc.Textarea(id='stocksbox',autoFocus='true',
            className='box',
            rows=8,
            value=initialStockSymbols),
        tooltip_label('Comparator','Stock performance to plot relative to'),
        dcc.Input(id='comparator',className='date',
            value=''),
        tooltip_label('Start Date','Date on the left side of the plot'),
        dcc.Input(id='dateBegin',className='date',
            value=(datetime.now()-relativedelta(years=1)).strftime("%m/%d/%Y")),
        tooltip_label('End Date','Date on the right side of the plot'),
        dcc.Input(id='dateEnd',className='date',
            value=datetime.now().strftime("%m/%d/%Y")),
        tooltip_label('Norm Date','Normalization date: the date at which all stocks have a relative value of 1.0'),
        dcc.Input(id='dateNorm',className='date',
            value=''),
        html.Div(plotButton)
    ], className='pinput pretty-container'
)
# https://dash.plotly.com/dash-daq/colorpicker

# https://stackoverflow.com/questions/1260122/expand-a-div-to-fill-the-remaining-width
# Right panel: the output plot
rightPanel = html.Div(
    html.Div(    
        dcc.Graph( id = 'main-plot',style={'width':'100%'}),
        className='panel',
    ),
    className='right',
)

titleNav = html.Div(
    [
        html.Img(src='/assets/splogo.png', style={'width':'40px'}),
        html.Button('Help'),
        html.Button('Examples'),
        html.A(
            html.Img(
                src='/assets/github.png',
                style={'opacity':'0.8','width':'80px'}
            ),
            href='https://github.com/AndrewChap/stock-comparer'
        ),
        html.H2("stock-plotter.com!", className='title',),
        html.H3("By Andrew Chap", className='author',)
    ],
    className = 'title-nav',
)

dashApp.layout = html.Div(
    [
        html.Div(
            [
                titleNav,
                html.Div(bothbox, className='leftside'),
                html.Div(
                    [
                        dcc.Graph(id='main-plot',style={'width':'100%'}),
                    ],
                    className='rightside'),
            ],
            className = 'contents',
        ),
    ]
)


def parse_dates(dateAsString):
    dateAsList = dateAsString.split('/')
    date = datetime(int(dateAsList[2]),int(dateAsList[0]),int(dateAsList[1]))
    return date
def parse_dates2(dateAsString):
    dateAsList = dateAsString.split('-')
    date = datetime(int(dateAsList[0]),int(dateAsList[1]),int(dateAsList[2]))
    return date

@dashApp.callback(
        Output('main-plot'  , 'figure'),
        [Input('plotstocks' , 'n_clicks')],
        [State('stocksbox'  , 'value'),
         State('comparator' , 'value'),
         State('dateBegin'  , 'value'),
         State('dateEnd'    , 'value'),
         State('dateNorm'   , 'value')]
    )
def update_figure(n_clicks,stocksbox,comparatorName,dateBeginAsString,dateEndAsString,dateNormAsString):
    dateBegin = parse_dates(dateBeginAsString)
    dateEnd = parse_dates(dateEndAsString)
    dateNorm = parse_dates(dateNormAsString) if dateNormAsString != '' else dateBegin
    listOfStockSymbols = stocksbox.strip('\n').split('\n')
    stocks.set_dates(dateBegin = dateBegin.date(), dateEnd = dateEnd.date())
    stocks.update_list_of_stock_symbols(newListOfStockSymbols = listOfStockSymbols)
    stocks.update_comparators(comparatorName)
    #stocks.norm_by_index(normIndex = sliderValue)
    stocks.norm_by_date(dateNorm = dateNorm)
    data = [ 
            {
                'x': stock.time,
                'y': stock.valsCompared,
                'name': stock.name,
            } for stock in stocks.listOfStocks
        ]
    maxY = max([max(stock.valsCompared) for stock in stocks.listOfStocks])
    minY = min([min(stock.valsCompared) for stock in stocks.listOfStocks])
    data.append(
            {
                'x': [dateNorm, dateNorm],
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
