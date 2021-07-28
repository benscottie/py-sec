# Libraries
from sec_edgar_downloader import Downloader
from bs4 import BeautifulSoup
import os
import glob
import shutil

def get_audits(ticker: str, before_yr: int, after_yr: int, output_dir: str):
    dl = Downloader(output_dir)
    # dl.get('10-K', ticker, amount=1)
    dl.get('10-K', ticker, after=f'{after_yr}-01-01', before=f'{before_yr}-01-01')
    files = glob.glob(f"sec-edgar-filings/{ticker}/10-K/**/*.html", recursive = False)
    return files

def load_html(fpath: str):
    with open(fpath, 'r') as f:
        return f.read()

def del_sec_dir(output_dir: str):
    shutil.rmtree(os.path.join(output_dir, 'sec-edgar-filings'))

def parse_item(fpath:str, ticker: str, output_dir: str):
    # Download Filing
    # fpath = get_audits(ticker, output_dir)
    # Load HTML
    filing = load_html(fpath)

    # Get Filing Date and Text from HTML
    soup = BeautifulSoup(filing, 'html.parser')
    txt = soup.get_text().lower()
    txt = txt.replace('\xa0', ' ')
      
    # Parse Item 7
    date = '20200101'
    item = 'hello world'
    """try:
        date = soup.title.get_text().split('-')[1]
        item = txt.split('item 7.')
        if len(item) == 3:
            item = item[2]
        elif len(item) == 2:
            item = item[1]
        else:
            print('ERROR')
        item = item.split('Item 8.')[0]
        item = item.replace('\xa0', '')
    except:
        item = ''
        date = '19960106'"""

    # Delete Downloaded Directory
    # del_sec_dir(output_dir)

    return {'company': ticker,
            'date': date,
            'item_text': item}

