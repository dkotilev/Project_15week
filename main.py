import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
from dash import Dash, html, dcc
from dash.dependencies import Input, Output

import config
from api import API
from diana.exceptions import ApiError

dash_app = Dash(__name__)
dash_app.layout = html.Div([
    html.H1('Погода'),
    html.Div(id='error', style={'color': 'red'}),
    dcc.Input(id='num_cities', type='number', value=2, min=1, step=1,
              placeholder='Введите количество городов'),
    dcc.Input(id='num_days', type='number', value=3, min=1, max=5, step=1,
              placeholder='Введите количество дней'),
    html.Button('Обновить', id='update_cities_button', n_clicks=0),
    html.Div(id='inputs', children=[]),
    html.Button('Получить погоду', id='get_weather_button', n_clicks=0),
    dcc.Graph(id='temp'),
    dcc.Graph(id='rain'),
    dcc.Graph(id='humidity'),
    dcc.Graph(id='wind'),
    dcc.Graph(id='map'),
])
colors = px.colors.qualitative.Plotly


@dash_app.callback(
    Output('inputs', 'children'),
    Input('update_cities_button', 'n_clicks'),
    Input('num_cities', 'value')
)
def update_city_inputs(n_clicks, num_cities):
    if n_clicks > 0 and num_cities is not None:
        return [dcc.Input(
            id=f'city{index}',
            type='text',
            placeholder='Введите город'
        ) for index in range(num_cities)]
    return []


dfs = {}


@dash_app.callback(
    Output('temp', 'figure'),
    Output('rain', 'figure'),
    Output('humidity', 'figure'),
    Output('wind', 'figure'),
    Output('map', 'figure'),
    Output('error', 'children'),
    Input('get_weather_button', 'n_clicks'),
    Input('inputs', 'children'),
    Input('num_days', 'value'),
)
def update_graph(n_clicks, city_inputs, num_days):
    fig_temp = go.Figure()
    fig_rain = go.Figure()
    fig_humidity = go.Figure()
    fig_wind = go.Figure()
    map_fig = go.Figure()

    errors = []

    if n_clicks > 0:
        names = []
        for input_component in city_inputs:
            try:
                names.append(input_component['props']['value'])
            except KeyError:
                errors.append(f'Город не введен')

        api = API(config.api_key)
        for name in names:
            try:
                if dfs.get(name, pd.DataFrame()).empty:
                    weather = api.weather(name)
                    dfs[name] = pd.DataFrame(weather)

            except ApiError as err:
                errors.append(f'Ошибка для города {name}: {err.message}')
                continue

        for i, (city, df) in enumerate(dfs.items()):
            color = colors[i % len(colors)]
            df = df[:num_days]
            fig_temp.add_trace(go.Scatter(
                x=df['date'],
                y=df['temperature'],
                mode='lines+markers',
                name=f'Средняя температура в {names[i]}',
                line={'color': color},
            ))
            fig_rain.add_trace(go.Scatter(
                x=df['date'],
                y=df['rain'],
                mode='lines+markers',
                name=f'Вероятность дождика в {names[i]}',
                line={'color': color},
            ))
            fig_humidity.add_trace(go.Scatter(
                x=df['date'],
                y=df['humidity'],
                mode='lines+markers',
                name=f'Примерная влажность в {names[i]}',
                line={'color': color},
            ))
            fig_wind.add_trace(go.Scatter(
                x=df['date'],
                y=df['wind'],
                mode='lines+markers',
                name=f'Сила ветра в {names[i]}',
                line={'color': color},
            ))

        fig_temp.update_layout(title=f'Прогноз температуры на {num_days} дней',
                               xaxis_title='Дата',
                               yaxis_title='Температура, °C',
                               legend_title='Города')

        fig_rain.update_layout(title=f'Прогноз дождика на {num_days} дней',
                               xaxis_title='Дата',
                               yaxis_title='Вероятность, %',
                               legend_title='Города')

        fig_humidity.update_layout(title=f'Прогноз влажности на {num_days} дней',
                                   xaxis_title='Дата',
                                   yaxis_title='Влажность, %',
                                   legend_title='Города')

        fig_wind.update_layout(title=f'Прогноз ветра на {num_days} дней',
                               xaxis_title='Дата',
                               yaxis_title='Скорость, км/час',
                               legend_title='Города')
        dfs_for_map = pd.concat(list(dfs.values()))
        map_fig = px.scatter_mapbox(
            dfs_for_map,
            lat='lat',
            lon='lot',
            hover_name='city',
            mapbox_style='carto-positron',
            hover_data=["city", "temperature", "rain", "humidity",
                        "wind"],
            zoom=5,
        )

    return fig_temp, fig_rain, fig_humidity, fig_wind, map_fig, 'Ошибочки: ' + ', '.join(errors)


if __name__ == '__main__':
    dash_app.run(host="127.0.0.1", port=8080, debug=True)
