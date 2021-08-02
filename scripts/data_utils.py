# Libraries
from sec_edgar_downloader import Downloader
from bs4 import BeautifulSoup
import os
import glob
import shutil
import re
import numpy as np

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

def get_sections(items: list):
    sections = []
    txt = []
    for i, item in enumerate(items):
        if item.endswith('.'):
            txt.append(item)
        elif any(s.isalpha() for s in item)==True:
            txt.append(item)
        elif (item.isnumeric()) & (len(item)==4):
            txt.append(item)
    
        if i < (len(items)-1):
            if (items[i+1][0].isalpha()) & ('.' not in items[i+1]) & (txt[-1].endswith('.')):
                sections.append(' '.join(txt))
                txt = []
    sections = [s for s in sections if s !=  'item 7.']
    return [' '.join(s.split()) for s in sections]

def parse_item_sections(fpath: str, ticker:str, output_dir: str):
    # Load HTML
    filing = load_html(fpath)
    # Initialize BeautifulSoup Object
    soup = BeautifulSoup(filing, 'html.parser')
    # Get Text Sections
    try:
        txt = [s.get_text().lower().strip() for s in soup.find_all('font')]
        txt = [s.get_text().lower().strip() for s in soup.find_all('span')] if not txt else txt
        txt = [s.replace('\xa0', ' ').strip() for s in txt]
        txt = [re.sub('\n', '', s) for s in txt]
        # Get Text Sections for Item 7
        idx_start = [i for i,s in enumerate(txt) if 'item 7.' in s]
        idx_end = [i for i,s in enumerate(txt) if 'item 7a.' in s]
        idx_item = np.argmax([e-s for e,s in zip(idx_end, idx_start)])
        items = txt[idx_start[idx_item]: idx_end[idx_item]]
        # Clean Text Sections
        items = [s for s in items if '10-k' not in s]
        items = list(filter(None, items))
        # Parse & Clean Final Text Sections
        sections = get_sections(items)
    except IndexError as e:
        print(e)
        sections = []
    except ValueError as v:
        print(v)
        sections = []
    # Get Full Text Split By Paragraph Indicators
    item_text = '\n\n'.join(sections)
    # Get Filing Date
    full_txt = soup.get_text().lower()
    date = get_date(full_txt)

    return {'company': ticker,
            'date': date,
            'item_text': item_text,
            'item_sections': sections}

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
        item = ' '.join(item.split())
    
    except IndexError as e:
        print(e)
        item = ''
    except AttributeError as a:
        print(a)
        item = ''

    # Delete Downloaded Directory
    # del_sec_dir(output_dir)

    return {'company': ticker,
            'date': date,
            'item_text': item}
