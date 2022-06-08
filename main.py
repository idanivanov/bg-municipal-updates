from dash import Dash, Input, Output, html
from dash.long_callback import DiskcacheLongCallbackManager
import dash_bootstrap_components as dbc
from dash.dash_table import DataTable
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import diskcache

from src import update


# setup diskcache
cache = diskcache.Cache('./cache')
long_callback_manager = DiskcacheLongCallbackManager(cache)


app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    long_callback_manager=long_callback_manager
)


app.layout = dbc.Container([
    dbc.Row(
        dbc.Col(
            html.H1('Новини от български общини')
        )
    ),
    dbc.Row(
        dbc.Col(
            html.H2('Община Перник')
        )
    ),
    dbc.Row([
        dbc.Col(
            dbc.Button(
                'Извлечи',
                color='outline-info',
                id='scrape-button',
                n_clicks=0
            )
        ),
        dbc.Col(
            dbc.Progress(
                id='progress-bar',
                color='info',
                striped=True,
                style={
                    'height': '100%',
                    'visibility': 'hidden'
                }
            ),
            width=9
        )
    ]),
    dbc.Row(
        dbc.Col(
            DataTable(
                id='scraped-data',
                data=[],
                columns=[
                    {
                        'name': 'Дата',
                        'id': 'date',
                        'type': 'datetime'
                    },
                    {
                        'name': 'Институция',
                        'id': 'institution',
                        'type': 'text'
                    },
                    {
                        'name': 'Категория',
                        'id': 'label',
                        'type': 'text'
                    },
                    {
                        'name': 'Заглавие',
                        'id': 'title',
                        'type': 'text'
                    },
                    {
                        'name': 'Съдържание',
                        'id': 'content',
                        'type': 'text'
                    },
                    {
                        'name': 'Връзка',
                        'id': 'link',
                        'type': 'text',
                        'presentation': 'markdown'
                    }
                ],
                filter_action='native',
                sort_action='native',
                sort_by=[
                    {
                        'column_id': 'date',
                        'direction': 'desc'
                    }
                ],
                style_as_list_view=True,
                style_header={
                    'backgroundColor': 'rgb(30, 30, 30)',
                    'color': 'white'
                },
                style_filter={
                    'backgroundColor': 'rgb(30, 30, 30)',
                    'color': 'white'
                },
                style_data={
                    'backgroundColor': 'rgb(50, 50, 50)',
                    'color': 'white'
                },
                style_cell={
                    'whiteSpace': 'pre-line',
                    'textAlign': 'left',
                    'padding': '5px'
                }
            )
        )
    )
])


@app.long_callback(
    output=[
        Output('scraped-data', 'data'),
        Output('scrape-button', 'color')
    ],
    inputs=Input('scrape-button', 'n_clicks'),
    running=[
        (
            Output('progress-bar', 'style'),
            {'height': '100%', 'visibility': 'visible'},
            {'height': '100%', 'visibility': 'hidden'}
        )
    ],
    progress=[
        Output('progress-bar', 'label'),
        Output('progress-bar', 'value')
    ]
)
def callback(set_progress, n_clicks):
    def progress(percent):
        set_progress((
            f'Извличане: {percent}%',
            percent
        ))

    if n_clicks == 1:
        progress(0)

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
        progress(40)

        pernik_vik_updates = update.PernikVikUpdates(driver)
        progress(70)

        driver.quit()
        progress(80)

        # prepare the data for the table
        updates = pernik_vik_updates.updates.copy(deep=True)
        updates['date'] = updates['date'].dt.strftime('%Y-%m-%d %H:%M:%S')
        updates['link'] = updates['url'].apply(
            lambda u: f'[Източник]({u})'
        )
        progress(100)

        return [
            updates.to_dict(orient='records'),
            True
        ]


if __name__ == '__main__':
    app.run_server(debug=True)
