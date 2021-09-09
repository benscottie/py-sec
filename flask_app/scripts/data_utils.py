# Libraries
from sec_edgar_downloader import Downloader
from bs4 import BeautifulSoup
import os
import glob
import shutil
import re
import numpy as np

def get_audits(ticker: str, before_yr: int, after_yr: int, output_dir: str) -> list:
    """
    Downloads 10-Ks for specified company and years to specified directory
    and returns list of paths for htmls of the filings. 

    :param ticker: the stock ticker of the company for which the 10-K filings should be downloaded
    :type ticker: str
    :param before_yr: the year before which the 10-K filings should be downloaded
    :type before_yr: int
    :param after_yr: the year after which the 10-K filings should be downloaded
    :type after_yr: int
    :output_dir: the directory where the downloaded 10-Ks are stored
    :output_dir: str

    :return: list of file paths to downloaded 10-K htmls
    :rtype: list
    """
    dl = Downloader(output_dir)
    # dl.get('10-K', ticker, amount=1)
    dl.get('10-K', ticker, after=f'{after_yr}-01-01', before=f'{before_yr}-01-01')
    files = glob.glob(f"sec-edgar-filings/{ticker}/10-K/**/*.html", recursive = False)
    return files

def load_html(fpath: str) -> str:
    """
    Load html text for 10-K filing

    :param fpath: paths to downloaded 10-K html file
    :type fpath: str

    :return: html for 10-K filing
    :rtype: str
    """
    with open(fpath, 'r') as f:
        return f.read()

def del_sec_dir(output_dir: str) -> None:
    """
    Delete downloaded 10-K filings once relevant data has been utilized
    by application and stored to database

    :param output_dir: the directory where the downloaded 10-Ks are stored
    :type output_dir: str

    :rtype: None
    """
    shutil.rmtree(os.path.join(output_dir, 'sec-edgar-filings'))

def get_date(txt: str) -> str:
    """
    Retrieve filing date from HTML

    :param txt: filing text extracted from html
    :type txt: str

    :return: filing date (format January 1, 2000)
    :rtype: str
    """
    date = txt.split('fiscal year ended')[1].split()[0:3]
    date[2] = re.sub('\D', '', date[2])
    return ' '.join(date).capitalize()

def get_sections(items: list) -> list:
    """
    Split Item 7 (MD&A) into subsections

    :param items: list of Item 7 text lines from extracted filing
    :type items: list

    :return: list containing subsections for each Item 7
    :rtype: list
    """
    sections = []
    txt = []
    # Add Text to Current Section
    for i, item in enumerate(items):
        if item.endswith('.'): # if text line ends with period
            txt.append(item)
        elif any(s.isalpha() for s in item)==True: # or text contains an alphabetic character
            txt.append(item)
        elif (item.isnumeric()) & (len(item)==4): # or text line is numeric and 4 characters long
            txt.append(item)
        
        # Identify New Section / Header & Combine + Store Text from Previous Section
        if i < (len(items)-1):
            if (items[i+1][0].isalpha()) & ('.' not in items[i+1]) & (txt[-1].endswith('.')):
                sections.append(' '.join(txt))
                txt = []

    sections = [s for s in sections if s !=  'item 7.']
    return [' '.join(s.split()) for s in sections]

def parse_item_sections(fpath: str, ticker:str) -> dict:
    """
    Parses Item 7 and subsections from html text of extracted filing

    :param fpath: path to downloaded 10-K filing
    :type fpath: str
    :param ticker: the stock ticker of the company for which the 10-K filing should be downloaded
    :type ticker: str
    
    :return: dictionary containing company name, date of filing, Item 7 text, and text for subsections (list)
    :rtype: dict
    """
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
        idx_start = [i for i,s in enumerate(txt) if 'item 7.' in s] # find start index for Item 7
        idx_end = [i for i,s in enumerate(txt) if 'item 7a.' in s] # find end index
        idx_item = np.argmax([e-s for e,s in zip(idx_end, idx_start)]) # only keep correct indices
        items = txt[idx_start[idx_item]: idx_end[idx_item]] # subset text to include only Item 7
        # Clean Item 7 Text Sections
        items = [s for s in items if '10-k' not in s]
        items = list(filter(None, items))
        # Parse & Clean Final Item 7 Text Sections
        sections = get_sections(items)
    except IndexError as e:
        print(e)
        sections = []
    except ValueError as v:
        print(v)
        sections = []
    # Get Full Item 7 Text Split By Paragraph Indicators
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
