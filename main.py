import os
import datetime
import csv
import argparse
import logging
logging.basicConfig(level=logging.INFO)
import re

from requests.exceptions import HTTPError
from urllib3.exceptions import MaxRetryError

import news_page_objects as news
from common import config

is_well_formed_url= re.compile(r'^https?://.+/.+$') # i.e. https://www.somesite.com/something
is_root_path = re.compile(r'^/.+$') # i.e. /some-text
logger = logging.getLogger(__name__)


def _news_scraper(news_site_uid):
    host = config()['news_sites'][news_site_uid]['url']

    logging.info('Beginning scraper for {}'.format(host))
    logging.info('Finding links in homepage...')

    homepage = news.HomePage(news_site_uid, host)

    # Recorremos cada unos de los vinculos encontrados en el home page
    articles = []
    for link in homepage.article_links:
        article = _fetch_article(news_site_uid, host, link)

        if article:
            logger.info('Article fetched!')
            articles.append(article)
            # break
    
    _save_articles(news_site_uid, articles)


def _save_articles(news_site_uid,articles):
    try:
        if not os.path.isdir('./news'):
            os.mkdir('news')
    except OSError as e:
        print('there was an error creating the folder')
        raise

    now = datetime.datetime.now().strftime('%Y_%m_%d')
    out_file_name = './news/{}_{}_articles.csv'.format(news_site_uid,now)
    csv_headers = list(filter(lambda property: not property.startswith('_'), dir(articles[0])))
    with open(out_file_name, mode='w+', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(csv_headers)

        for article in articles:
            row = [str(getattr(article, prop)) for prop in csv_headers]
            writer.writerow(row)

# Analizamos si el articulo cumple con los requisitos
def _fetch_article(news_site_uid, host, link):
    logger.info('Start fetching article at {}'.format(link))

    article = None
    try:
        article = news.ArticlePage(news_site_uid, _build_link(host, link))
    except (HTTPError, MaxRetryError) as e:
        logger.warn('Error while fetching article!', exc_info=False)

    if article and not article.body:
        logger.warn('Invalid article. There is no body.')
        return None

    return article


def _build_link(host, link):
    if is_well_formed_url.match(link):
        return link
    elif is_root_path.match(link):
        return '{host}{uri}'.format(host=host, uri=link)
    else:
        return '{host}/{uri}'.format(host=host, uri=link)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    news_site_choices = list(config()['news_sites'].keys())
    parser.add_argument('news_site',
        help='The news site that you want to scrape',
        type=str,
        choices=news_site_choices
    )

    args = parser.parse_args()
    _news_scraper(args.news_site)
