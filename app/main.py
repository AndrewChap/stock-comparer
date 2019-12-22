# Copyright 2015 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# [START gae_flex_quickstart]
import logging

from flask import Flask
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output


server = Flask(__name__)

x = [0.,1.,2.,3.]
y = [2.,1.,4.,3.]

dashApp = dash.Dash(
    __name__,
    server=server,
    #routes_pathname_prefix='/dash/'
)
dashApp.scripts.config.serve_locally = True


dashApp.layout = html.Div(children=[
    html.H1(children='Hello Dash!!',
	    style={
                'textAlign' : 'center',
		}
),
    html.Div(children='''
        Dash: A
    '''),
    dcc.Graph(
        id = 'main-plot',
    ),
    html.Label('Text Input'),
    dcc.Input(id='mir-input', value='3.5', type='text'),
    html.Div(id='mir-div')
])

@dashApp.callback(
    Output(component_id='mir-div', component_property='children'),
    [Input(component_id='mir-input', component_property='value')]
)
def update_output_div(input_value):
    input_float = float(input_value)
    return 'Rate = {:.2f}%, x[0] = {}'.format(input_float,y[0])

@dashApp.callback(
    Output('main-plot', 'figure'),
    [Input('mir-input', 'value')])
def update_figure(input_value):
    input_float = float(input_value)
    return {
        'data': [
            {'x': x, 'y': y+input_float,
             'type': 'line', 'name': 'SF'},
        ],
        'layout': {
            'title': 'Dash Data Visualization'
        }
    }


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
