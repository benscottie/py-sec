# Libraries
from sec_edgar_downloader import Downloader
from bs4 import BeautifulSoup
import os
import glob
import shutil
import re

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

def get_date(txt: str):
    date = txt.split('fiscal year ended')[1].split()[0:3]
    date[2] = re.sub('\D', '', date[2])
    return ' '.join(date).capitalize()

def parse_item(fpath:str, ticker: str, output_dir: str):
    # Download Filing
    # fpath = get_audits(ticker, output_dir)
    # Load HTML
    filing = load_html(fpath)

    # Get & Clean Text from HTML
    soup = BeautifulSoup(filing, 'html.parser')
    txt = soup.get_text().lower()
    txt = txt.replace('\xa0', ' ')
    txt = re.sub('\n', '', txt)

    # Get Filing Date
    date = get_date(txt)
      
    # Parse Item 7
    try:
        item = txt.split("item 7.")
        if len(item) == 3:
            if len(item[2]) > len(item[1]):
                item = item[2]
            elif len(item[1]) > len(item[2]):
                item = item[1]
        elif len(item)==2:
            item = item[1]
        item = item.split("item 7a.")[0].strip()
    except IndexError as e:
        print(e)
        item = ''
        pass

    # Delete Downloaded Directory
    # del_sec_dir(output_dir)

    return {'company': ticker,
            'date': date,
            'item_text': item}

