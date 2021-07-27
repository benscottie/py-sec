# Libraries
import torch
from transformers import AutoTokenizer
from transformers import AutoModelForSequenceClassification

from scripts.db_utils import (create_postgress_engine,
                              select_record,
                              add_filing_data)

# from scripts.data_utils import get_audits, parse_audits

class ItemSentiment():
    def __init__(self, data):
        self.table_name = 'item_sentiment'
        self.company = data['company']
        self.year = data['year']

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
        engine = create_postgress_engine(username='',
                                        password='', 
                                        dialect_driver='postgresql', 
                                        host='sec-test.csfr6b0gmrjt.us-east-1.rds.amazonaws.com',
                                        port='5432', 
                                        database='sec_db') # connect
        
        records = select_record(engine, 
                        self.table_name, 
                        company=self.company, 
                        most_recent=False, 
                        year=None, 
                        sentiment_score=True)
        
        # If records returned from database, send records
        # If no records returned from database, retrieve, parse, score, and store filings
        if not records:
            # filing = get_audits()
            # parsed_filing = parse_audits(filing)
            parsed_filing = {'company': 'GOOG', 'date': '09/02/2020', 'text': 'hello world'}
            sentiment_score = self.predict(parsed_filing['text'])
            records = parsed_filing
            records['sentiment'] = round(sentiment_score, 4)

            add_filing_data(engine, records, table_name=self.table_name)
        
        return records
