# Libraries
import os
from dotenv import load_dotenv

import numpy as np
import multiprocessing
from datetime import datetime

import torch
import torch.nn.functional as F

from transformers import AutoTokenizer
from transformers import AutoModelForSequenceClassification

from scripts.db_utils import (create_postgress_engine,
                              select_record,
                              add_filing_data)

from scripts.data_utils import parse_item_sections, get_audits, del_sec_dir

load_dotenv()

def sections2sql(records):
    for d in records:
        for k,v in d.items():
            if k == 'sentiment_scores':
                d[k] = '\n'.join([str(n) for n in v])
    return records

def date_format(records):
    for r in records:
            r.update((k, datetime.strftime(v, '%B %d, %Y')) for k,v in r.items() if k == 'date') 
    return records

class ItemSentiment():
    def __init__(self, data):
        self.output_dir = ''
        self.table_name = 'item_sentiment'
        self.company = data['company']
        self.before_yr = data['before_year']
        self.after_yr = data['after_year']
        self.top_n = 5

        self.batch_size = 4
        self.model_path = 'ProsusAI/finbert'
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
    
    def predict(self, sections):
        # Get sentiment score for each section in Item 7 of filing
        sentiment = []
        batches = [sections[i:i+self.batch_size] for i in range(0, len(sections), self.batch_size)]
        for batch in batches:
            input_ids = self.tokenizer(batch, truncation=True, padding=True, return_tensors='pt').input_ids.to(self.device)
            with torch.no_grad():
                logits = self.model(input_ids).logits

            # score = F.softmax(logits, dim=1).squeeze().tolist()[1]
            # sentiment.append(round(score, 4))
            scores = F.softmax(logits, dim=1)
            neg_scores = [round(s[1], 4)for s in scores.tolist()]
            sentiment.extend(neg_scores)
        return sentiment

    def run(self):
        # Search DataBase for Records
        print(f'Connecting to Database...')
        engine = create_postgress_engine(username=os.getenv('DB_USER'),
                                        password=os.getenv('DB_PASSWORD'), 
                                        dialect_driver='postgresql', 
                                        host='sec-test.csfr6b0gmrjt.us-east-1.rds.amazonaws.com',
                                        port='5432', 
                                        database=os.getenv('DB_NAME')) # connect
        
        print(f'Checking Database for Filing(s) for {self.company} between {self.after_yr} & {self.before_yr}...')
        records = select_record(engine, 
                        self.table_name, 
                        company=self.company, 
                        after_yr=self.after_yr, 
                        before_yr=self.before_yr)
        # change date format
        records = date_format(records)
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
                records_new = pool.starmap(parse_item_sections, [(path, self.company, self.output_dir) for path in fpaths])
            
            # Get Year Value from Date
            year_fn = lambda x: datetime.strptime(x['date'], '%B %d, %Y').year
            records_new = [dict(r, year=year_fn(r)) for r in records_new]
            # Only Keep Missing Records
            records_new = [r for r in records_new if r['year'] in missing_dates]
            
            print(f'Record(s) parsed, predicting sentiment for item(s)...')
            sections = [r['item_sections'] for r in records_new]
            with multiprocessing.Pool(4) as pool:
                sentiment_scores = pool.map(self.predict, sections)

            records_new = [dict(r, sentiment_scores=scores) for r,scores in zip(records_new, sentiment_scores)] # add sentiment scores for each section to records
            records_new = [dict(r, average_sentiment_score=round(np.mean(scores), 4) if scores else 0.0) for r, scores in zip(records_new, sentiment_scores)] # add average sentiment score for each filing (across all sections) to records
            records_new = [dict(r, maximum_sentiment_score=np.max(scores, initial=0.0)) for r, scores in zip(records_new, sentiment_scores)] # add lowest sentiment score for each filing (across all sections) to records
            max_idx = [np.argmax(score) if score else None for score in sentiment_scores]
            records_new = [dict(r, negative_section=r['item_sections'][idx] if idx else '') for r, idx in zip(records_new, max_idx)] # add text corresponding to lowest sentiment score for each filing

            # Combine Records
            records = records + records_new
            
            print(f'Adding new filing(s) to database...')
            records_sql = sections2sql(records_new)
            add_filing_data(engine, records_sql, self.table_name)
            
            # Delete Downloaded Directory
            del_sec_dir(self.output_dir)
        
        # Sort and Rank Records
        records = sorted(records, key = lambda i: i['maximum_sentiment_score'], reverse=True)
        records = [dict(r, rank=i+1) for i,r in enumerate(records)]
        print(f'Information ready')

        # return records[:self.top_n]
        return records
