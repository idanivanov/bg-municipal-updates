from dash import Dash, Input, Output, html
from dash.long_callback import DiskcacheLongCallbackManager
import dash_bootstrap_components as dbc
from dash.dash_table import DataTable
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import diskcache
import traceback
import requests
import json

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
    update_title='MuNews - Нoвини от български общини',
    external_scripts=['https://www.google.com/recaptcha/api.js?render=explicit']
)


# recaptcha sitkey and secret
app.server.config['RECAPTCHA_SITEKEY'] = '<fill-your-value>'
app.server.config['RECAPTCHA_SECRET'] = '<fill-your-value>'


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
        dbc.Col([
            html.Div(id='scrape-recaptcha'),
            html.Div(id='scrape-recaptcha-response', style={'display': 'none'}),
        ])
    ),
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
                        'name': 'Дата (ISO)',
                        'id': 'date_iso',
                        'type': 'datetime'
                    },
                    {
                        'name': 'Дата',
                        'id': 'date_bg',
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
                hidden_columns=['date_iso'],
                filter_action='native',
                sort_action='native',
                sort_by=[
                    {
                        'column_id': 'date_iso',
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


app.clientside_callback(
    '''
    function(n_clicks) {
        if (n_clicks == 0){
            grecaptcha.render('scrape-recaptcha', {'sitekey' : '_sitekey'});
        }
        if (n_clicks > 0){
            var recaptcha_response = document.getElementById('g-recaptcha-response');
            return recaptcha_response.value;
        }
    }
    '''.replace('_sitekey', app.server.config['RECAPTCHA_SITEKEY']),
    Output('scrape-recaptcha-response', 'children'), 
    Input('scrape-button', 'n_clicks')
)


@app.long_callback(
    output=[
        Output('scraped-data', 'data'),
        Output('scrape-button', 'disabled'),
        Output('error-message', 'children')
    ],
    inputs=[
        Input('scrape-button', 'n_clicks'),
        Input('scrape-recaptcha-response', 'children')
    ],
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
def scrape_data(set_progress, n_clicks, recaptcha_response):
    def recaptcha_success():
        if recaptcha_response is None \
           or recaptcha_response.strip() == '':
            return False
        request_headers = {
            'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8'
        }
        request_url = 'https://www.google.com/recaptcha/api/siteverify?secret={0}&response={1}'.format(
            app.server.config['RECAPTCHA_SECRET'],
            recaptcha_response
        )
        response = requests.post(
            request_url,
            headers=request_headers
        )
        response_json = json.loads(response.text)
        return response_json['success']

    def progress(percent):
        set_progress((
            f'Извличане: {percent}%',
            percent
        ))

    if n_clicks >= 1 and recaptcha_success():
        try:
            logger.info('Starting the scraping process...')
            progress(10)

            logger.info('Loading Chrome webdriver...')
            driver = webdriver.Chrome(
                executable_path=ChromeDriverManager().install(),
                options=chrome_options
            )
            progress(30)

            logger.info('Scraping website: Pernik ViK')
            pernik_vik_updates = update.PernikVikUpdates(driver)
            progress(50)

            logger.info('Scraping website: Pernik Toplo')
            pernik_toplo_updates = update.PernikToploUpdates(driver)
            progress(70)

            logger.info('Quitting Chrome webdriver...')
            driver.quit()
            progress(80)

            logger.info('Preparing the data to be displayed on the Dash table...')
            updates = pd.concat([
                pernik_vik_updates.updates,
                pernik_toplo_updates.updates
            ])
            updates['date_iso'] = updates['date'].dt.strftime('%Y-%m-%d %H:%M:%S')
            updates['date_bg'] = updates['date'].dt.strftime('%d.%m.%Y %H:%M:%S')
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
    app.run_server(debug=False, host='0.0.0.0')
