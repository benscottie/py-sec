# Libraries
import multiprocessing
from datetime import datetime
import os
from dotenv import load_dotenv

import torch
from transformers import AutoTokenizer
from transformers import AutoModelForSequenceClassification

from scripts.db_utils import (create_postgress_engine,
                              select_record,
                              add_filing_data)

from scripts.data_utils import parse_item, get_audits, del_sec_dir

load_dotenv()

class ItemSentiment():
    def __init__(self, data):
        self.output_dir = ''
        self.table_name = 'item_sentiment'
        self.company = data['company']
        self.before_yr = data['before_year']
        self.after_yr = data['after_year']
        self.top_n = 5

        self.model_path = 'lvwerra/bert-imdb'
        self.device = self.get_device('cpu')
        self.model = self.get_model()
        self.tokenizer = self.get_tokenizer()
    
    def get_device(self, dtype):
        if dtype=='gpu' and torch.cuda.is_available():
            dname = 'cuda'
        else:
            dname = 'cpu'
        return torch.device(dname)
    
    def get_model(self):
        model = AutoModelForSequenceClassification.from_pretrained(self.model_path)
        return model.to(self.device)
    
    def get_tokenizer(self):
        return AutoTokenizer.from_pretrained(self.model_path)
    
    def predict(self, text):
        input_ids = self.tokenizer(text, truncation=True, padding=True, return_tensors='pt').input_ids.to(self.device)
        logits = self.model(input_ids).logits
        score = torch.sigmoid(logits).squeeze().tolist()[1]
        return score
    
    def run(self):
        # Search DataBase for Records
        print(f'Connecting to Database...')
        engine = create_postgress_engine(username=os.getenv('DB_USER'),
                                        password=os.getenv('DB_PASSWORD'), 
                                        dialect_driver='postgresql', 
                                        host='sec-test.csfr6b0gmrjt.us-east-1.rds.amazonaws.com',
                                        port='5432', 
                                        database=os.getenv('DB_NAME')) # connect
        
        print(f'Checking Database for Filing(s)...')
        records = select_record(engine, 
                        self.table_name, 
                        company=self.company, 
                        after_yr=self.after_yr, 
                        before_yr=self.before_yr)
        
        # If records returned from database, send records
        # If full records are not returned from database, retrieve, parse, score, and store new filings
        available_dates = [r['year'] for r in records]
        requested_dates = [i for i in range(self.after_yr, self.before_yr)]
        missing_dates = list(set(requested_dates) - set(available_dates))
        print(f'Missing Records for Year(s) {missing_dates}')

        if missing_dates:
            print(f'Filing(s) not in database, retrieving filing(s) for {self.company} between {self.after_yr} & {self.before_yr}...')
            fpaths = get_audits(self.company, self.before_yr, self.after_yr, self.output_dir)
            
            print(f'{len(fpaths)} file(s) retrieved, parsing items...')
            with multiprocessing.Pool(4) as pool:
                records_new = pool.starmap(parse_item, [(path, self.company, self.output_dir) for path in fpaths])
            
            # Get Year Value from Date
            year_fn = lambda x: datetime.strptime(x['date'], '%B %d, %Y').year
            records_new = [dict(r, year=year_fn(r)) for r in records_new]
            # Only Keep Missing Records
            records_new = [r for r in records_new if r['year'] in missing_dates]
            
            print(f'Record(s) parsed, predicting sentiment for item(s)...')
            text = [r['item_text'] for r in records_new]
            with multiprocessing.Pool(4) as pool:
                sentiment_scores = pool.map(self.predict, text)
            records_new = [dict(r, sentiment_score=round(score, 4)) for r,score in zip(records_new, sentiment_scores)]
            
            # Sort and Rank Records
            records = records + records_new
            records = sorted(records, key = lambda i: i['sentiment_score'], reverse=True)
            records = [dict(r, rank=i+1) for i,r in enumerate(records)]
            
            print(f'Adding new filing(s) to database...')
            add_filing_data(engine, records_new, self.table_name)
            
            print(f'Information ready')
            # Delete Downloaded Directory
            del_sec_dir(self.output_dir)

        return records[:self.top_n]
