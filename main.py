import dash
import dash_table
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Input, Output
from selenium import webdriver

from src import update


app = dash.Dash(__name__)

app.layout = html.Div([
    html.H3('Bulgarian Municipal Updates'),
    html.Button('Scrape', id='scrape-button', n_clicks=0),
    dash_table.DataTable(
        data=[],
        columns=[
            # {'name': 'Municipality', 'id': 'municipality'},
            {'name': 'Date', 'id': 'date'},
            {'name': 'Institution', 'id': 'institution'},
            {'name': 'Label', 'id': 'label'},
            {'name': 'Title', 'id': 'title'},
            {'name': 'Content', 'id': 'content'},
        ],
        id='scraped-data'
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
        return pernik_vik_updates.updates


if __name__ == '__main__':
    app.run_server(debug=True)
