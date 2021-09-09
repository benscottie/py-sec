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
        Column('sentiment_scores', String),
        Column('average_sentiment_score', Float),
        Column('maximum_sentiment_score', Float),
        Column('negative_section', String)
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
        Column('sentiment_scores', String),
        Column('average_sentiment_score', Float),
        Column('maximum_sentiment_score', Float),
        Column('negative_section', String)
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
    
    with engine.connect() as conn:
        result = conn.execute(insert(table),
                              filing_dict)
                              
    """stmt = insert(table).values(company=filing_dict['company'], 
                                date=filing_dict['date'],
                                year=datetime.strptime(filing_dict['date'], '%Y%m%d').year,
                                item_text=filing_dict['text'], 
                                sentiment_score=filing_dict['sentiment'])
    with engine.connect() as conn:
       result = conn.execute(stmt)"""

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
    after_yr: int,
    before_yr: int
    ):
    sql = f"""SELECT * from {table_name}
          WHERE company = '{company}'
          AND year BETWEEN {after_yr} AND {before_yr}"""
    with engine.connect() as con:
        df = pd.read_sql_query(sql, con=con)
    d = df.to_dict('records')
    
    return d
        