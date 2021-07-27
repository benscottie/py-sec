# Libraries
from sec_edgar_downloader import Downloader
from bs4 import BeautifulSoup
import os
import glob
import shutil

def get_audits(ticker: str, output_dir: str):
    dl = Downloader(output_dir)
    dl.get('10-K', ticker, amount=1)
    file = glob.glob(f"sec-edgar-filings/{ticker}/10-K/**/*.html", recursive = False)[0]
    return file

def load_html(fpath: str):
    with open(fpath, 'r') as f:
        return f.read()

def del_sec_dir(output_dir: str):
    shutil.rmtree(os.path.join(output_dir, 'sec-edgar-filings'))

def parse_item(ticker: str, output_dir: str):
    # Download Filing
    fpath = get_audits(ticker, output_dir)
    # Load HTML
    filing = load_html(fpath)

    # Get Filing Date and Text from HTML
    soup = BeautifulSoup(filing, 'html.parser')
    date = soup.title.get_text().split('-')[1]
    txt = soup.get_text()

    # Parse Item 7
    item = txt.split('Item 7.')[2]
    item = item.split('Item 8.')[0]
    item = item.replace('\xa0', '')

    # Delete Downloaded Directory
    del_sec_dir(output_dir)

    return {'company': ticker,
            'date': date,
            'text': item,}

