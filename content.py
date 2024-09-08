from argparse import ArgumentParser
from bs4 import BeautifulSoup
from urllib.parse import unquote_plus, urljoin
from requests import get
from fake_useragent import UserAgent


def sanitize(soup):
    '''
    Return one div#content of decent manner.
    '''
    content = soup.find(id='content')
    for link in content.find_all('a'):
        if 'class' in link and 'new' in link['class']:      # red link
            del link['href']
        if 'href' not in link:
            continue
        href = link['href']
        href = href.split('/', 2)
        href[2] = href[2].replace('/', '\uff0f')
        href = '/'.join(href)
        link['href'] = unquote_plus(href)
    if (subtitle := soup.find(id='siteSub')) is not None:
        subtitle.string = 'From Shidinn Wiki'
    return content


def full_page(url, title):
    response = get(url, headers={'User-Agent': UserAgent().random})
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')
    result = '''<!DOCTYPE html>
    <head><title>{title} « Xdi8 Aho</title>
    <link rel=stylesheet href="/assets/main.css">
    <link rel=stylesheet href="/assets/reset.css">
    <meta charset=utf-8>
    <body>
    <header><a href="/"><img src="/assets/wikilogo.svg" alt="Shidinn Wiki mirror" /></a></header>
    {content}
    '''.format(title=title, content=sanitize(soup))
    return result


def allpages():
    '''
    Generator from Special:AllPages.
    '''
    namespaces = [0, 2, 4, 6, 14, 3824, 3826, 3828]
    url_nasa = 'https://wiki.xdi8.top/wiki/Special:AllPages?hideredirects=1&namespace={}'
    for namespace in namespaces:
        url = url_nasa.format(namespace)
        while True:
            response = get(url)
            html = response.text
            soup = BeautifulSoup(html, 'html.parser')
            ul = soup.find(class_='mw-allpages-chunk')
            for link in ul.find_all('a'):
                link['title'] = link['title'].replace('/', '\uff0f')
                link['href'] = urljoin(url, link['href'])
                yield link
            post = soup.find(class_='mw-allpages-nav')
            post = [i for i in post.children][-1]
            if post.getText().strip().startswith('下'):
                url = urljoin(url, post['href'])
            else:
                break

        
def recentchanges():
    '''
    Generator from Special:AllPages.
    '''
    url = 'https://wiki.xdi8.top/wiki/Special:RecentChanges?limit=50&days=1&enhanced=1&urlversion=2'
    response = get(url)
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')
    ul = soup.find(class_='mw-changeslist-title')
    for link in ul.find_all('a'):
        link['title'] = link['title'].replace('/', '\uff0f')
        link['href'] = urljoin(url, link['href'])
        yield link
        

def write_page(url, title, path):
    from os.path import join
    last = title.replace(' ', '_') + '.html'
    with open(join(path, last), 'w') as f:
        f.write(full_page(url, title))
    print('🌍 Written', title)


def force(path, pages):
    import os
    from concurrent.futures import ThreadPoolExecutor, as_completed
    os.makedirs(path, exist_ok=True)
    executor = ThreadPoolExecutor(max_workers=4)
    results = [executor.submit(write_page, i['href'], i['title'], path) for i in pages]
    for i in as_completed(results):
        try:
            i.result()
        except:
            import traceback
            print(traceback.format_exc())
    executor.shutdown(wait=True)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-o', '--output', help='Output path', default='./wiki')
    parser.add_argument('--all', help='Snow all the time', action='store_true')
    parser.add_argument('--day', help='Snow of yesterday', action='store_true')
    option = parser.parse_args()

    if option.day:
        force(option.output, recentchanges())
    elif option.all:
        force(option.output, allpages())
