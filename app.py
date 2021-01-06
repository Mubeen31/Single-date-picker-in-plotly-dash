import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import pandas as pd
from datetime import date

url_confirmed = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv'
url_deaths = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_global.csv'
url_recovered = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_recovered_global.csv'

confirmed = pd.read_csv(url_confirmed)
deaths = pd.read_csv(url_deaths)
recovered = pd.read_csv(url_recovered)

# Unpivot data frames
date1 = confirmed.columns[4:]
total_confirmed = confirmed.melt(id_vars = ['Province/State', 'Country/Region', 'Lat', 'Long'], value_vars = date1,
                                 var_name = 'date', value_name = 'confirmed')
date2 = deaths.columns[4:]
total_deaths = deaths.melt(id_vars = ['Province/State', 'Country/Region', 'Lat', 'Long'], value_vars = date2,
                           var_name = 'date', value_name = 'death')
date3 = recovered.columns[4:]
total_recovered = recovered.melt(id_vars = ['Province/State', 'Country/Region', 'Lat', 'Long'], value_vars = date3,
                                 var_name = 'date', value_name = 'recovered')

# Merging data frames
covid_data = total_confirmed.merge(right = total_deaths, how = 'left',
                                   on = ['Province/State', 'Country/Region', 'date', 'Lat', 'Long'])
covid_data = covid_data.merge(right = total_recovered, how = 'left',
                              on = ['Province/State', 'Country/Region', 'date', 'Lat', 'Long'])

# Converting date column from string to proper date format
covid_data['date'] = pd.to_datetime(covid_data['date'])

# Check how many missing value naN
covid_data.isna().sum()

# Replace naN with 0
covid_data['recovered'] = covid_data['recovered'].fillna(0)

# Calculate new column
covid_data['active'] = covid_data['confirmed'] - covid_data['death'] - covid_data['recovered']

covid_data['Province/State'] = covid_data['Province/State'].fillna('No Data')


covid_data1 = covid_data[['Country/Region', 'Lat', 'Long']]

list_locations = covid_data1.set_index('Country/Region')[['Lat', 'Long']].T.to_dict('dict')


app = dash.Dash(__name__, meta_tags=[{"name": "viewport", "content": "width=device-width"}])


app.layout = html.Div([
        html.Div([
            html.Div([
                html.H2("Covid - 19 Dashboard", style = {'text-align': 'center'}),
                html.P('Select Region'),
                html.Div([
                   dcc.Dropdown(
                                id = 'select_country',
                                multi = False,
                                clearable = True,
                                disabled = False,
                                style = {'display': True},
                                value = 'Brazil',
                                placeholder = 'Select state',
                                options = [{'label': c, 'value': c}
                                           for c in (covid_data['Country/Region'].unique())]),

                ], className='fix_dropdown'),

                html.Div([
                   dcc.RadioItems(id = 'radio_items',
                                  labelStyle = {"display": "inline-block"},
                                  options = [{'label': 'Confirmed', 'value': 'confirmed1'},
                                             {'label': 'Deaths', 'value': 'deaths1'},
                                             {'label': 'Recovered', 'value': 'recovered1'},
                                             {'label': 'Active', 'value': 'active1'}],
                                  value = 'confirmed1')
                ], className='fix_dropdown'),

                html.Div([

                   dcc.DatePickerSingle(
                                    id="date_picker",
                                    min_date_allowed=date(2020, 1, 1),
                                    max_date_allowed=date(2021, 12, 31),
                                    initial_visible_month=date(2021, 1, 4),
                                    date=date(2021, 1, 4),
                                    display_format="MMMM D, YYYY",
                                    style={"border": "0px solid black"},
                                )

                ], className='fix_dropdown'),
                html.P('Last Updated: ' + str(covid_data['date'].iloc[-1].strftime("%B %d, %Y")) + '  00:01 (UTC)',
                       style={'color': 'orange'}),

    ], className="three columns left_pane"),

            html.Div([
                    dcc.Graph(id='map_chart'),
                    dcc.Graph(id='bar_chart'),

                ], className="nine columns fix_charts bg_color"),

            ], className="row"),

 ])

@app.callback(Output('map_chart', 'figure'),
              [Input('select_country', 'value')],
              [Input('radio_items', 'value')],
              [Input('date_picker', 'date')])
def update_graph(select_country, radio_items, date):
    covid_data_1 = covid_data.groupby(['date', 'Province/State', 'Country/Region', 'Lat', 'Long'])['confirmed', 'death', 'recovered', 'active'].sum().reset_index()
    covid_data_2 = covid_data_1[(covid_data_1['Country/Region'] == select_country) & (covid_data_1['date'] == date)]

    if radio_items == 'confirmed1':


     return {
        'data': [go.Scattermapbox(
            lon = covid_data_2['Long'],
            lat = covid_data_2['Lat'],
            mode = 'markers',
            marker=go.scattermapbox.Marker(
                size = covid_data_2['confirmed'] / 400,
                color = 'orange',
                sizemode = 'area'),

            hoverinfo = 'text',
            hovertext =
            '<b>Country</b>: ' + covid_data_2['Country/Region'].astype(str) + '<br>' +
            '<b>Province/State</b>: ' + covid_data_2['Province/State'].astype(str) + '<br>' +
            '<b>Date</b>: ' + covid_data_2['date'].astype(str) + '<br>' +
            '<b>Lat</b>: ' + [f'{x:.4f}' for x in covid_data_2['Lat']] + '<br>' +
            '<b>Long</b>: ' + [f'{x:.4f}' for x in covid_data_2['Long']] + '<br>' +

            '<b>Confirmed</b>: ' + [f'{x:,.0f}' for x in covid_data_2['confirmed']] + '<br>'

        )],

        'layout': go.Layout(
             margin={"r": 0, "t": 0, "l": 0, "b": 0},
             hovermode='closest',
             mapbox=dict(
                accesstoken='pk.eyJ1IjoicXM2MjcyNTI3IiwiYSI6ImNraGRuYTF1azAxZmIycWs0cDB1NmY1ZjYifQ.I1VJ3KjeM-S613FLv3mtkw',  # Create free account on Mapbox site and paste here access token
                center=dict(lat=list_locations[select_country]['Lat'], lon=list_locations[select_country]['Long']),
                # style='open-street-map',
                style='dark',
                zoom=3,
                bearing = 0
             ),
             autosize=True,

        )

    }

    elif radio_items == 'deaths1':


     return {
        'data': [go.Scattermapbox(
            lon = covid_data_2['Long'],
            lat = covid_data_2['Lat'],
            mode = 'markers',
            marker=go.scattermapbox.Marker(
                size = covid_data_2['death'] / 300,
                color = '#dd1e35',
                sizemode = 'area'),

            hoverinfo = 'text',
            hovertext =
            '<b>Country</b>: ' + covid_data_2['Country/Region'].astype(str) + '<br>' +
            '<b>Province/State</b>: ' + covid_data_2['Province/State'].astype(str) + '<br>' +
            '<b>Date</b>: ' + covid_data_2['date'].astype(str) + '<br>' +
            '<b>Lat</b>: ' + [f'{x:.4f}' for x in covid_data_2['Lat']] + '<br>' +
            '<b>Long</b>: ' + [f'{x:.4f}' for x in covid_data_2['Long']] + '<br>' +

            '<b>Deaths</b>: ' + [f'{x:,.0f}' for x in covid_data_2['death']] + '<br>'

        )],

        'layout': go.Layout(
             margin={"r": 0, "t": 0, "l": 0, "b": 0},
             hovermode='closest',
             mapbox=dict(
                accesstoken='pk.eyJ1IjoicXM2MjcyNTI3IiwiYSI6ImNraGRuYTF1azAxZmIycWs0cDB1NmY1ZjYifQ.I1VJ3KjeM-S613FLv3mtkw',  # Create free account on Mapbox site and paste here access token
                center=dict(lat=list_locations[select_country]['Lat'], lon=list_locations[select_country]['Long']),
                # style='open-street-map',
                style='dark',
                zoom=3,
                bearing = 0
             ),
             autosize=True,

        )

    }

    elif radio_items == 'recovered1':


     return {
        'data': [go.Scattermapbox(
            lon = covid_data_2['Long'],
            lat = covid_data_2['Lat'],
            mode = 'markers',
            marker=go.scattermapbox.Marker(
                size = covid_data_2['recovered'] / 300,
                color = 'green',
                sizemode = 'area'),

            hoverinfo = 'text',
            hovertext =
            '<b>Country</b>: ' + covid_data_2['Country/Region'].astype(str) + '<br>' +
            '<b>Province/State</b>: ' + covid_data_2['Province/State'].astype(str) + '<br>' +
            '<b>Date</b>: ' + covid_data_2['date'].astype(str) + '<br>' +
            '<b>Lat</b>: ' + [f'{x:.4f}' for x in covid_data_2['Lat']] + '<br>' +
            '<b>Long</b>: ' + [f'{x:.4f}' for x in covid_data_2['Long']] + '<br>' +

            '<b>Recovered</b>: ' + [f'{x:,.0f}' for x in covid_data_2['recovered']] + '<br>'

        )],

        'layout': go.Layout(
             margin={"r": 0, "t": 0, "l": 0, "b": 0},
             hovermode='closest',
             mapbox=dict(
                accesstoken='pk.eyJ1IjoicXM2MjcyNTI3IiwiYSI6ImNraGRuYTF1azAxZmIycWs0cDB1NmY1ZjYifQ.I1VJ3KjeM-S613FLv3mtkw',  # Create free account on Mapbox site and paste here access token
                center=dict(lat=list_locations[select_country]['Lat'], lon=list_locations[select_country]['Long']),
                # style='open-street-map',
                style='dark',
                zoom=3,
                bearing = 0
             ),
             autosize=True,

        )

    }

    elif radio_items == 'active1':


     return {
        'data': [go.Scattermapbox(
            lon = covid_data_2['Long'],
            lat = covid_data_2['Lat'],
            mode = 'markers',
            marker=go.scattermapbox.Marker(
                size = covid_data_2['active'] / 300,
                color = '#e55467',
                sizemode = 'area'),

            hoverinfo = 'text',
            hovertext =
            '<b>Country</b>: ' + covid_data_2['Country/Region'].astype(str) + '<br>' +
            '<b>Province/State</b>: ' + covid_data_2['Province/State'].astype(str) + '<br>' +
            '<b>Date</b>: ' + covid_data_2['date'].astype(str) + '<br>' +
            '<b>Lat</b>: ' + [f'{x:.4f}' for x in covid_data_2['Lat']] + '<br>' +
            '<b>Long</b>: ' + [f'{x:.4f}' for x in covid_data_2['Long']] + '<br>' +

            '<b>Active</b>: ' + [f'{x:,.0f}' for x in covid_data_2['active']] + '<br>'

        )],

        'layout': go.Layout(
             margin={"r": 0, "t": 0, "l": 0, "b": 0},
             hovermode='closest',
             mapbox=dict(
                accesstoken='pk.eyJ1IjoicXM2MjcyNTI3IiwiYSI6ImNraGRuYTF1azAxZmIycWs0cDB1NmY1ZjYifQ.I1VJ3KjeM-S613FLv3mtkw',  # Create free account on Mapbox site and paste here access token
                center=dict(lat=list_locations[select_country]['Lat'], lon=list_locations[select_country]['Long']),
                # style='open-street-map',
                style='dark',
                zoom=3,
                bearing = 0
             ),
             autosize=True,

        )

    }


@app.callback(Output('bar_chart', 'figure'),
              [Input('select_country', 'value')])
def update_graph(select_country):
    # main data frame
    covid_data_2 = covid_data.groupby(['date', 'Country/Region'])[['confirmed', 'death', 'recovered', 'active']].sum().reset_index()
    # daily confirmed
    covid_data_3 = covid_data_2[covid_data_2['Country/Region'] == select_country][['Country/Region', 'date', 'confirmed']].reset_index()
    covid_data_3['daily confirmed'] = covid_data_3['confirmed'] - covid_data_3['confirmed'].shift(1)
    covid_data_3['Rolling Ave.'] = covid_data_3['daily confirmed'].rolling(window = 7).mean()

    return {
        'data': [go.Bar(x = covid_data_3[covid_data_3['Country/Region'] == select_country]['date'].tail(30),
                        y = covid_data_3[covid_data_3['Country/Region'] == select_country]['daily confirmed'].tail(30),

                        name = 'Daily confirmed',
                        marker = dict(
                            color = 'orange'),
                        hoverinfo = 'text',
                        hovertext =
                        '<b>Date</b>: ' + covid_data_3[covid_data_3['Country/Region'] == select_country]['date'].tail(30).astype(str) + '<br>' +
                        '<b>Daily confirmed</b>: ' + [f'{x:,.0f}' for x in covid_data_3[covid_data_3['Country/Region'] == select_country]['daily confirmed'].tail(30)] + '<br>' +
                        '<b>Country</b>: ' + covid_data_3[covid_data_3['Country/Region'] == select_country]['Country/Region'].tail(30).astype(str) + '<br>'

                        ),
                 go.Scatter(x = covid_data_3[covid_data_3['Country/Region'] == select_country]['date'].tail(30),
                            y = covid_data_3[covid_data_3['Country/Region'] == select_country]['Rolling Ave.'].tail(30),
                            mode = 'lines',
                            name = 'Rolling average of the last seven days - daily confirmed cases',
                            line = dict(width = 3, color = '#FF00FF'),
                            # marker=dict(
                            #     color='green'),
                            hoverinfo = 'text',
                            hovertext =
                            '<b>Date</b>: ' + covid_data_3[covid_data_3['Country/Region'] == select_country]['date'].tail(30).astype(str) + '<br>' +
                            '<b>Rolling Ave.(last 7 days)</b>: ' + [f'{x:,.0f}' for x in covid_data_3[covid_data_3['Country/Region'] == select_country]['Rolling Ave.'].tail(30)] + '<br>'
                            )],

        'layout': go.Layout(
            plot_bgcolor = '#192444',
            paper_bgcolor = '#192444',
            title = {
                'text': 'Last 30 Days Confirmed Cases : ' + (select_country),
                'y': 0.93,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top'},
            titlefont = {
                'color': 'white',
                'size': 15},

            hovermode = 'x',
            # margin = dict(b=140),



            xaxis = dict(title = '<b></b>',
                         color = 'white',
                         showline = True,
                         showgrid = False,
                         linecolor = 'white',
                         linewidth = 1,
                         showticklabels = True,
                         ticks = 'outside',
                         tickfont = dict(
                             family = 'Arial',
                             size = 12,
                             color = 'white'
                         )

                         ),

            yaxis = dict(title = '<b></b>',


                         color = 'white',
                         showline = False,
                         showgrid = False,
                         showticklabels = False,
                         linecolor = 'white',

                         ),

            legend = {
                'orientation': 'h',
                'bgcolor': '#192444',
                'x': 0.5,
                'y': 1.1,
                'xanchor': 'center',
                'yanchor': 'top'},

            font = dict(
                family = "sans-serif",
                size = 15,
                color = 'white'),

        )

            }


if __name__ == "__main__":
    app.run_server(debug=True)
