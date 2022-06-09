from dash import Dash, Input, Output, html
from dash.long_callback import DiskcacheLongCallbackManager
import dash_bootstrap_components as dbc
from dash.dash_table import DataTable
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import diskcache
import traceback

from src import update
from src.logger import create_logger

logger = create_logger('bg_municipal_updates', 'logs')


# setup diskcache
cache = diskcache.Cache('./cache')
long_callback_manager = DiskcacheLongCallbackManager(cache)


# set selenium to run on the backend
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--headless')


app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    long_callback_manager=long_callback_manager,
    title='MuNews - Новини от български общини',
    update_title='MuNews - Нoвини от български общини'
)


app.layout = dbc.Container([
    dbc.Row(
        dbc.Col([
            html.H1('MuNews'),
            html.P('Новини от български общини')
        ])
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
                striped=True
            ),
            width=9
        )
    ]),
    dbc.Row(
        dbc.Col(
            html.P('', id='error-message', style={'color': 'red'})
        )
    ),
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
        Output('scrape-button', 'disabled'),
        Output('error-message', 'children')
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
def scrape_data(set_progress, n_clicks):
    def progress(percent):
        set_progress((
            f'Извличане: {percent}%',
            percent
        ))

    if n_clicks == 1:
        try:
            logger.info('Starting the scraping process...')
            progress(10)

            logger.info('Loading Chrome webdriver...')
            driver = webdriver.Chrome(
                executable_path=ChromeDriverManager().install(),
                options=chrome_options
            )
            progress(40)

            logger.info('Scraping website: Pernik ViK')
            pernik_vik_updates = update.PernikVikUpdates(driver)
            progress(70)

            logger.info('Quitting Chrome webdriver...')
            driver.quit()
            progress(80)

            logger.info('Preparing the data to be displayed on the Dash table...')
            updates = pernik_vik_updates.updates.copy(deep=True)
            updates['date'] = updates['date'].dt.strftime('%Y-%m-%d %H:%M:%S')
            updates['link'] = updates['url'].apply(
                lambda u: f'[Източник]({u})'
            )
            progress(100)

            logger.info('Done scraping.')
            return [
                updates.to_dict(orient='records'),
                True,
                ''
            ]

        except Exception as e:
            logger.error(str(e) + '\n' + traceback.format_exc())
            return [
                [],
                True,
                'Възникна грешка! Свържете се с разработчика!'
            ]


if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0')
