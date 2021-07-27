from sqlalchemy import (create_engine, 
                        MetaData, 
                        Table, 
                        Column, 
                        Integer, 
                        String, 
                        Float, 
                        Date, 
                        insert, 
                        delete,
                        text)
import pandas as pd
from datetime import datetime

def create_postgress_engine(
    username: str,
    password: str,
    dialect_driver: str,
    host: str,
    port: str,
    database: str
    ):
    
    db_url = f'{dialect_driver}://{username}:{password}@{host}:{port}/{database}'
    ret_eng = create_engine(db_url)

    return ret_eng

def create_table(engine, table_name: str):
    meta = MetaData(bind=engine)
    table = Table(
        table_name, meta,
        Column('id', Integer, primary_key=True, autoincrement=True),
        Column('company', String),
        Column('date', Date),
        Column('year', Integer),
        Column('item_text', String),
        Column('sentiment_score', Float)
    )
    # meta.create_all(engine)
    table.create(engine)

def drop_table(engine, table_name):
    meta = MetaData()
    table = Table(
        table_name, meta,
        Column('id', Integer, primary_key=True, autoincrement=True),
        Column('company', String),
        Column('date', Date),
        Column('year', Integer),
        Column('item_text', String),
        Column('sentiment_score', Float)
    )
    # meta.drop_all(engine)
    table.drop(engine)

def add_filing_data(
    engine,
    filing_dict: dict,
    table_name: str,
    ):
    meta = MetaData()
    table = Table(table_name, meta, autoload=True, autoload_with=engine)

    stmt = insert(table).values(company=filing_dict['company'], 
                                date=filing_dict['date'],
                                year=datetime.strptime(filing_dict['date'], '%m/%d/%Y').year,
                                item_text=filing_dict['text'], 
                                sentiment_score=filing_dict['sentiment'])
    with engine.connect() as conn:
       result = conn.execute(stmt)

def delete_record(
    engine,
    idx: int,
    table_name: str,
    ):
    meta = MetaData()
    table = Table(table_name, meta, autoload=True, autoload_with=engine)
    stmt = delete(table).where(table.c.id==idx)
    with engine.connect() as conn:
        result = conn.execute(stmt)

def truncate_table(
    engine,
    table_name: str
    ):
    with engine.connect() as conn:
        result = conn.execute(text(f"TRUNCATE {table_name}"))

def select_record(
    engine,
    table_name: str,
    company: str,
    most_recent=True,
    year=None,
    sentiment_score=False,
    top_n=5
    ):
    meta = MetaData()
    table = Table(table_name, meta, autoload=True, autoload_with=engine)
    if most_recent==True:
        sql = f"select * from item_sentiment where company = '{company}'"
        with engine.connect() as con:
            df = pd.read_sql_query(sql, con=con)
        d = df.sort_values('date', ascending=False).head(1).to_dict('records')

    elif year:
        sql = f"""SELECT * from item_sentiment 
         WHERE company = '{company}' AND year = {year}"""
        with engine.connect() as con:
            df = pd.read_sql_query(sql, con=con)
        d = df.to_dict('records')

    elif sentiment_score==True:
        sql = f"select * from item_sentiment where company = '{company}'"
        with engine.connect() as con:
            df = pd.read_sql_query(sql, con=con)
        d = df.sort_values('sentiment_score', ascending=False).head(top_n).to_dict('records')
        d = [dict(item, rank=i+1) for i,item in enumerate(d)]
    
    return d
        