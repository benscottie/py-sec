# Libraries
from tqdm import tqdm
import multiprocessing
from datetime import datetime
import os
import time
from dotenv import load_dotenv

from scripts.data_utils import parse_item, get_audits, del_sec_dir
from scripts.db_utils import (create_postgress_engine,
                              add_filing_data)

COMPANY_LIST = ['AAPL', 'MSFT', 'GOOG']
BEFORE_YR = 2021
AFTER_YR = 2020
OUTPUT_DIR = ''
TABLE_NAME = 'item_sentiment'

load_dotenv()

def main(company_list, before_yr, after_yr, output_dir, table_name):

    print(f'Connecting to Database...')
    engine = create_postgress_engine(username=os.getenv('DB_USER'),
                                    password=os.getenv('DB_PASSWORD'), 
                                    dialect_driver='postgresql', 
                                    host='sec-test.csfr6b0gmrjt.us-east-1.rds.amazonaws.com',
                                    port='5432', 
                                    database=os.getenv('DB_NAME')) # connect

    for company in tqdm(company_list, desc='Retrieving & adding company filing(s) to database', unit='company'):
        
        print(f'Retrieving filing(s) for {company} between {after_yr} & {before_yr}...')
        fpaths = get_audits(company, before_yr, after_yr, output_dir)

        print(f'{len(fpaths)} file(s) retrieved, parsing items...')
        with multiprocessing.Pool(4) as pool:
            records = pool.starmap(parse_item, [(path, company, output_dir) for path in fpaths])
        
        # Get Year Value from Date
        year_fn = lambda x: datetime.strptime(x['date'], '%B %d, %Y').year
        records = [dict(r, year=year_fn(r)) for r in records]

        print(f'Adding {company} filing(s) to database...')
        add_filing_data(engine, records, table_name)
                
        print(f'{company} filing(s) stored to database')
        # Delete Downloaded Directory
        del_sec_dir(output_dir)

if __name__ == "__main__":
    start_time = time.time()
    main(COMPANY_LIST, BEFORE_YR, AFTER_YR, OUTPUT_DIR, TABLE_NAME)
    print(f'Storing of record(s) complete')
    print(f'Time Elapsed: {time.time()-start_time:.2f} seconds')
