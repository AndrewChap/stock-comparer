# VTXVX VTWNX VTTVX VTHRX VTTHX VFORX VTIVX VFIFX VFFVX VTTSX VLXVX
STOCK_INTERFACE = 'yfinance' # 'google' or 'yahoo' or 'yfinance'
PICKLING = True

import logging
from flask import Flask

# Dash for plots
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
# Numpy for arrays
import numpy as np
import pandas as pd
import os
import pickle
import glob

import yfinance as yf

from pandas import Series, DataFrame
import pandas_datareader
import pandas_datareader.data as web
# Datetime for dealing with stock dates
from datetime import datetime
import datetime as dt
from dateutil.relativedelta import relativedelta
# pdb for debugging
import pdb
from collections import OrderedDict
db = pdb.set_trace

server = Flask(__name__)

class RawStock:
    def __init__(self,name,dateBegin,dateEnd):
        self.name = name.upper()
        self.dateBegin = dateBegin
        self.dateEnd = dateEnd
        # CLEANUP - test deleting next two lines
        print('Getting stock data for {}'.format(self.name))
        self.ticker = yf.Ticker(self.name)
        self.shortName = None
        self.logo = None

        # CLEANUP figure out why this try/except is needed, fix it
        try:
            pickleName = '{}_{}_{}.pickle'.format(self.name,dateBegin.date(),dateEnd.date())
        except:
            pickleName = '{}_{}_{}.pickle'.format(self.name,dateBegin,dateEnd)
        #dfPickleName = 'df-'+pickleName
        #tickerPickleName = 'ticker-'+pickleName
        # CLeanup: make more pythonic methods for saving/loading
        # CLEANUP: create pickle directory if it doesn't exist
        if not os.path.exists('pickles'):
            os.mkdir('pickles')
            picks = glob.glob('*.pickle*')
            for pick in picks:
                os.remove(pick)
        # FUTURE: use redis because it can put lifetimes on files https://cloud.google.com/appengine/docs/standard/python3/using-memorystore
        if os.path.exists(pickleName) and PICKLING:
            print('loading {} from pickle...'.format(pickleName))
            self.df = pd.read_pickle(pickleName)
            print('getting ticker name')
            #self.info = pickle.load(pickleName+'.info')
            with open(pickleName + '.info', 'rb') as handle:
                self.info = pickle.load(handle)
            print('Finished loading {} from pickle'.format(pickleName))
        else:
            print('Fetching data for {}'.format(pickleName))
            self.ticker = yf.Ticker(self.name)
            self.df = self.ticker.history(period='1d', start=dateBegin, end=dateEnd)
            self.info = self.ticker.info
            try:
                self.df.to_pickle(pickleName)
            except:
                pass
            with open(pickleName+'.info', 'wb') as handle:
                pickle.dump(self.info, handle, protocol=pickle.HIGHEST_PROTOCOL)
        self.shortName = self.info['shortName']
        self.vals = self.df['Close'].values
        self.time = self.df.index

class RawStocksPool:
    def __init__(self):
        self.rawStocks = list()
    def get_raw_stock(self,name,dateBegin,dateEnd):
        for rawStock in self.rawStocks:
            if rawStock.name == name and rawStock.dateBegin == dateBegin and rawStock.dateEnd == dateEnd:
                print('already had data for {}'.format(name))
                return rawStock
        print('Need to fetch data for {}'.format(name))
        newRawStock = RawStock(name,dateBegin,dateEnd)
        self.rawStocks.append(newRawStock)
        return newRawStock

rawStocksPool = RawStocksPool()

## Object to hold all the stocks that the app requests,
## so we dont have to re-request any thatt weve alrwady requested
# Create stock objects
class Stock:
    def __init__(self,name,dateBegin,dateEnd,comparator=None):
        self.name = name.upper()
        self.dateBegin = dateBegin
        self.dateEnd = dateEnd
        self.comparator = None
        
        self.ticker = yf.Ticker(self.name)
        print('get_raw_stock')
        rawStock = rawStocksPool.get_raw_stock(name=self.name,dateBegin=self.dateBegin,dateEnd=self.dateEnd)
        print('done')
        self.df = rawStock.df
        self.logo = rawStock.logo
        self.shortName = rawStock.shortName
        self.vals = rawStock.vals
        self.time = rawStock.time
        #self.time = self.df.index
        print('norm')
        self.norm_by_index(0)
        print('update_comparator')
        self.update_comparator(comparator) # if comparator is None, this just sets valsCompared=valsNorm
        self.success = not self.df.empty
        print('finished')

        
    def norm_by_index(self,normIndex):
        self.valsNorm = self.vals/self.vals[normIndex]
    def update_comparator(self,comparator):
        if comparator:
            self.valsCompared = [v/n for v,n in zip(self.valsNorm,comparator.valsNorm)]
        else:
            self.valsCompared = self.valsNorm
    def remove_comparator(self):
        print('{} removing comparator'.format(self.name))
        self.comparator = None
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
        self.comparator = None
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
                self.listOfStocks.append(Stock(name = stockSymbol, dateBegin = self.dateBegin, dateEnd = self.dateEnd, comparator = self.comparator))
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
                self.remove_comparators()
            else:
                self.comparatorName = comparatorName
                # Create a new stock for the comparator.  Note that the comparator itself cannot *have* a comparator
                self.comparator = Stock(name=comparatorName,dateBegin=self.dateBegin,dateEnd=self.dateEnd,comparator=None)
                for stock in self.listOfStocks:
                    stock.update_comparator(self.comparator)
    def remove_comparators(self):
        self.comparator = None
        self.comparatorName = ''
        for stock in self.listOfStocks:
            stock.remove_comparator()

    #def norm_by_index(self,normIndex):
    #    for stock in self.listOfStocks:
    #        stock.norm_by_index(normIndex)
    def norm_by_date(self,dateNorm):
        for stock in self.listOfStocks:
            stock.norm_by_date(dateNorm)

MKT='SPY'
BND='BND'
initialStockSymbols='{}\n{}'.format(MKT,BND)
listOfStockSymbols = ''#initialStockSymbols.strip('\n').split('\n')
#Set start and end as one year ago to now
dateEnd = datetime.now()
dateBegin = dateEnd - relativedelta(years=1)
stocks = Stocks(listOfStockSymbols = listOfStockSymbols, dateBegin = dateBegin.date(), dateEnd = dateEnd.date())
#stocks.set_dates(dateBegin = dateBegin.date(), dateEnd = dateEnd.date())
#print("before:{} ".format(stocks.listOfStocks))
#stocks.update_list_of_stock_symbols(newListOfStockSymbols = listOfStockSymbols)

# CLEANUP use make_plot for ALL plots
def make_plot(stocks,yVals,dateNorm=None):
    data = [ 
            {
                'x': stock.time,
                'y': getattr(stock,yVals),
                'name': '<b>'+stock.name+'</b>' + ((' (' + stock.shortName + ')') if stock.shortName is not None else '')
            } for stock in stocks.listOfStocks
        ]
    maxY = max([max(getattr(stock,yVals)) for stock in stocks.listOfStocks])
    minY = min([min(getattr(stock,yVals)) for stock in stocks.listOfStocks])
    if dateNorm is not None:
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
            'legend': {'x':0.01, 'y':1.05},
            'yaxis': {'range': [minY,maxY]},
            'margin': {'l': 40, 'r': 40, 't': 30, 'b': 30},
            'showlegend': True
        }
    }

dashApp = dash.Dash(
    __name__,
    server=server,
    #routes_pathname_prefix='/dash/'
)
#CUSTOM HTML for Google Adsense
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
        dcc.Graph(id = 'main-plot',style={'width':'100%'}),
        className='panel',
    ),
    className='right',
)

titleNav = html.Div(
    [
        dcc.Link(
            html.Img(src='/assets/splogo.png', style={'width':'30px'}),
            href='/',
            #style={'font-size':'0'}
            className='imgLink topButton topLeft'
        ),
        dcc.Link('Help',className='topButton topLeft',
            href='/help'
        ),
        #html.A('Examples',className='topButton',
        #    href='/examples'
        #),
        html.Div(
            [
                html.H2("Stock-plotter.com",className='title'),
                html.Hr(style={'margin':'0','padding':'0'}),
                html.P("A(n) Historical Performance Comparison Tool",className='subtitle')
            ],
            className='titleBox'
        ),
        html.A('About',className='topButton',
            href='/about'
        ),
        html.A('Contact',className='topButton topRight',
            href='/contact'
        ),
        html.A(
            html.Img(
                src='/assets/github_logo.png',
                style={'opacity':'1.0','width':'23px'}
            ),
            #className = 'author',
            href='https://github.com/AndrewChap/stock-comparer',
            target='_blank',
            className='imgLink topButton topRight'
        )
    ],
    className = 'title-nav',
)

dashApp.layout = html.Div(
    [
        dcc.Location(id='url', refresh=False),
        html.Div(
            [
                titleNav,
                html.Div(id='page-content')
            ],
            className = 'contents',
        ),
    ]
)

mainPage = [
    html.Div(bothbox, className='leftside'),
    html.Div(
        [
            dcc.Graph(id='main-plot',style={'width':'100%'}),
        ],
        className='rightside'
    ),
]


helpStocks = Stocks(listOfStockSymbols=(MKT,BND),dateBegin=dateBegin,dateEnd=dateEnd)
helpStocksNorm = Stocks(listOfStockSymbols=(MKT,BND),dateBegin=dateBegin,dateEnd=dateEnd)
helpStocksNorm.norm_by_date(datetime(2020,2,19))
googleStocks=Stocks(listOfStockSymbols=['GOOGL'],dateBegin=datetime(2009,3,9),dateEnd=datetime(2020,2,21))
googleStocksComp=Stocks(listOfStockSymbols=['GOOGL'],dateBegin=datetime(2009,3,9),dateEnd=datetime(2020,2,21))
googleStocksComp.update_comparators('SPY')
make_plot(stocks=helpStocks,yVals='vals')
def make_plot_help_page(**kwargs):
    return html.Div(
            html.Div(
                dcc.Graph(
                    figure=make_plot(**kwargs),
                    className='staticGraph',
                    style={'height': '300px'}
                ),
                className='staticGraphDiv'
            ), 
            className='staticGraphDivContainer'
        )
fig1 = make_plot_help_page(stocks=helpStocks,yVals='vals')
fig2 = make_plot_help_page(stocks=helpStocks,yVals='valsNorm')
fig3 = make_plot_help_page(stocks=helpStocksNorm,yVals='valsNorm',dateNorm=datetime(2020,2,19))
fig4 = make_plot_help_page(stocks=googleStocks,yVals='valsCompared')
fig5 = make_plot_help_page(stocks=googleStocksComp,yVals='valsCompared')

helpPage = html.Div(
    [
        html.H3('How Stock-plotter works'),
        html.Hr(),
        html.P(
            '''Stock Plotter is a tool for comparing historical performance of various stocks,
            by graphing their growth relative to their price at a given date.
            Below is a quick introduction to what this means:
            '''
        ),
        html.H5('Plotting stocks'),
        html.P(
            '''Plotting different stock tickers on the same graph isn't always helpful.  
            Here is a plot of an S&P 500 index fund ({MKT}) along with
            a bonds index fund ({BND}) over the last year:'''.format(MKT=MKT,BND=BND)
        ),
        fig1,
        dcc.Markdown(
            '''It looks like **{BND}** is significantly less volitile than **{MKT}**,
            but the lower price of **{BND}** skews this difference.  A more representative
            approach to comparing their performance is to plot them each relative to their
            starting price
            '''.format(BND=BND,MKT=MKT)
        ),
        fig2,
        html.P(
            '''What if we want to compare them from the point of the COVID crash?  If we 
            normalize them to their value at the market peak of Feb 19th, 2020, we can see 
            how each has done since then.
            '''
        ),
        fig3,
        dcc.Markdown(
            '''Notice how their values are each **1** on February 19th 2020.  This allows us 
            to see how each fared since the date of the crash.
            '''
        ),
        html.H5('The comparator'),
        dcc.Markdown(
            '''The "comparator" tool is used to plot how a stock has performed relative to 
            another stock (usually an index).  Say we want to see how GOOGL's stock did during

            '''
        ),
        # Expansion from March 6th 2009 to Feb 19th 2020
        dcc.Markdown(
            '''The "comparator" tool is used to plot how a stock has performed relative to 
            another stock (usually an index).  For example, let's see how Google's stock did 
            during the expansion from March 9th 2009 to February 19th 2020:
            '''
        ),
        fig4,
        dcc.Markdown(
            '''That's a growth factor of 10.43, which makes that stock look like quite a smart buy.
            But the rest of the market was doing splendidly during that time too.  Setting the 
            "comparator" to {MKT} shows us how well Google did *relative* to {MKT}:
            '''.format(MKT=MKT)
        ),
        fig5,
        dcc.Markdown(
            '''Plotting the relative growth, we see that Google outperformed the market by a factor
            of 1.7 during the 11-year expansion.'''
        ),
    ],
    className='wholePage'
)
aboutPage = html.Div(
    [
        html.H3('About'),
        html.Hr(),
        dcc.Markdown(
            '''Stock Plotter is a tool for comparing historical performance of various stocks,
            by graphing their growth relative to their price at a given date.
            '''
        ),
        dcc.Markdown(
            '''This tool was created by Andrew Chap.  Please see more of my work
            [www.andrewchap.com](http://www.andrewchap.com/).
            '''
        ),
    ],
    className='wholePage'
)
contactPage = html.Div(
    [
        html.H3('Contact'),
        html.Hr(),
        dcc.Markdown(
            '''For bug reports, feature requests, or any other inquiries please contact me at
            <andrew@andrewchap.com>.
            '''
        ),
    ],
    className='wholePage'
)

def parse_dates(dateAsString):
    dateAsList = dateAsString.split('/')
    date = datetime(int(dateAsList[2]),int(dateAsList[0]),int(dateAsList[1]))
    return date
def parse_dates2(dateAsString):
    dateAsList = dateAsString.split('-')
    date = datetime(int(dateAsList[0]),int(dateAsList[1]),int(dateAsList[2]))
    return date

@dashApp.callback(Output('page-content', 'children'),
                 [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/':
        return mainPage
    elif pathname == '/help':
        return helpPage
    elif pathname == '/examples':
        return html.Div([
            html.H3('Examples be here')
        ])
    elif pathname == '/about':
        return aboutPage
    elif pathname == '/contact':
        return contactPage



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
    listOfStockSymbols = stocksbox.upper().strip('\n').split('\n')
    stocks.set_dates(dateBegin = dateBegin.date(), dateEnd = dateEnd.date())
    stocks.update_list_of_stock_symbols(newListOfStockSymbols = listOfStockSymbols)
    stocks.update_comparators(comparatorName)
    #stocks.norm_by_index(normIndex = sliderValue)
    stocks.norm_by_date(dateNorm = dateNorm)
    data = [ 
            {
                'x': stock.time,
                'y': stock.valsCompared,
                'name': '<b>'+stock.name+'</b>' + ((' (' + stock.shortName + ')') if stock.shortName is not None else '')
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
            'legend': {'x':0.01, 'y':1.05},
            'yaxis': {'range': [minY,maxY]},
            'margin': {'l': 40, 'r': 40, 't': 30, 'b': 30},
            'showlegend': True,
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
