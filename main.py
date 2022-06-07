import dash
import dash_table
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Input, Output
from selenium import webdriver

from src import update


app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1('Новини от български общини'),
    html.H2('Община Перник'),
    html.Button('Извлечи', id='scrape-button', n_clicks=0),
    dash_table.DataTable(
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
])

@app.callback(
    Output('scraped-data', 'data'),
    Input('scrape-button', 'n_clicks')
)
def scrape_updates(n_clicks):
    if n_clicks == 1:
        chromedriver_path = '../../chromedriver_mac64_m1'
        driver = webdriver.Chrome(chromedriver_path)
        pernik_vik_updates = update.PernikVikUpdates(driver)
        driver.quit()
        # prepare the data for the table
        updates = pernik_vik_updates.updates.copy(deep=True)
        updates['date'] = updates['date'].dt.strftime("%Y-%m-%d %H:%M:%S")
        updates['link'] = updates['url'].apply(
            lambda u: f'[Източник]({u})'
        )
        return updates.to_dict(orient='records')


if __name__ == '__main__':
    app.run_server(debug=True)
