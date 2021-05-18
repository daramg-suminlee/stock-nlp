
import datetime
from datetime import date, timedelta
import pandas as pd
import requests
from requests_html import HTMLSession, HTMLResponse
from typing import Dict, List
import urllib

def get_yfnews_overview(
    tickers: List[str],
    start_date: datetime.date=date.today()-timedelta(days=7),
    end_date: datetime.date=date.today(),
    max_page: int=3
) -> pd.DataFrame:

    yfnews_url = 'https://finance.yahoo.com/news'
    
    df = pd.DataFrame(columns=['ticker', 'date', 'title', 'summary'])
    for ticker in tickers:
        news_search = get_google_news_search(ticker, yfnews_url, start_date, end_date, max_page)
        for news in news_search:
            url = news['url']
            news_detail = get_yfnews_detail(url)
            
            df_tmp = pd.DataFrame.from_dict([{'ticker' : ticker.upper(), 
                                              'date'   : news_detail['date'], 
                                              'title'  : news_detail['title'],
                                              'summary': news['summary'],
                                              'url'    : url}])
            df = df.append(df_tmp, ignore_index=True)

    return df.sort_values(by=['ticker', 'date'], ignore_index=True)

def get_yfnews_detail(news_url: str):

    css_date = 'time'
    css_title= 'h1'
    css_body = '.caas-body'

    response = __get_source(news_url)
    detail = {
        'date' : datetime.datetime.strptime(response.html.find(css_date, first=True).text, '%B %d, %Y, %I:%M %p'),
        'title': response.html.find(css_title, first=True).text,
        'body' : response.html.find(css_body, first=True).text,
    }
    return detail

def get_google_news_search(
    word: str,
    url: str,
    start_date: datetime.date=date.today()-timedelta(days=7), 
    end_date: datetime.date=date.today(), 
    max_page: int=3
) -> List[Dict[str, str]]:

    if max_page < 1:
        raise Exception('max_page must be positive integer')

    search_url = 'https://www.google.com/search?q='
    inurl = ' inurl:' + url
    after = ' after:' +  start_date.strftime('%Y-%m-%d')
    before = ' before:' + end_date.strftime('%Y-%m-%d')

    css_result = '.dbsr'
    css_url = '.dbsr a'
    css_summary = '.Y3v8qd'

    searches = []
    for page_idx in range(max_page):
        num_page = 10 * page_idx
        quote = word + inurl + after + before
        quote_url = search_url + urllib.parse.quote_plus(quote) + f'&tbm=nws&start={num_page}'

        response = __get_source(quote_url)
        results = response.html.find(css_result)
        if not results: break

        search = []
        for result in results:
            item = {
                'url': result.find(css_url, first=True).attrs['href'],                
                'summary': result.find(css_summary, first=True).text,
            }
            search.append(item)
        searches += search

    return searches

def __get_source(url: str) -> HTMLResponse:

    try:
        session = HTMLSession()
        response = session.get(url)
        return response
    except requests.exceptions.RequestException as e:
        print(e)