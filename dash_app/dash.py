import streamlit as st
import requests
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

# URL to API Endpoint
URL = 'http://flask_app:5000/'

# Cache Results
@st.cache(show_spinner=False)

# Request records from API
def api_call(url, company, before_year, after_year):
    data = [{'company': company,
             'before_year': before_year,
             'after_year': after_year}]
    r = requests.post(url, 
                      json=data)

    return r.json()

# Title
st.title("SEC 10-K Sentiment Scores for Item 7.: Management's Discussion and Analysis")

# Get Data from Input Boxes
with st.sidebar.form(key='input form'):

    after_year = st.selectbox(
        'Select the years after which you would like to retrieve filings',
        [i for i in range(2000, 2022)])

    before_year = st.selectbox(
        'Select the years before which you would like to retrieve filings',
        [i for i in range(2000, 2022)])

    company = st.text_input(
        'Indicate the stock ticker or CIK of the company for which you would like to retrieve filings')
    
    plot_year = st.selectbox(
            'Select the year for which you would like to see the distribution of section sentiment scores',
            [i for i in range(after_year, before_year)])

    submit_button = st.form_submit_button(label='Submit')

with st.spinner():
    if submit_button:
        # Make Call to Flask API to get text + sentiment scores
        records = api_call(URL, company, before_year, after_year)

        # Display DataFrame of Top 5 Years (Most Negative Sections)
        st.subheader('Top 5 Filings by Negative Sentiment')
        df = pd.DataFrame(records)
        df = df[['company', 'date', 'maximum_sentiment_score', 'average_sentiment_score']]
        df = df.sort_values('maximum_sentiment_score', ascending=False).head(5)
        st.table(df)

        # Get Score and Text for Section with Highest Negative Sentiment
        records_first = [r for r in records if r['rank']==1][0]
        negative_section = records_first['negative_section']
        max_score = records_first['maximum_sentiment_score']
        max_year = records_first['year']
        st.subheader('Text for Section with Highest Negative Sentiment Score')
        st.write(f'Negative Sentiment Score: {max_score}')
        st.write(f'Year: {max_year}')
        st.write(negative_section)

        # Plot Distribution of Section Sentiment Scores for Each Year
        st.subheader(f'Distribution of Section Sentiment Scores (Negative) for {plot_year}')

        # sentiment_scores = [r['sentiment_scores'].split('\n') for r in records if r['year']==plot_year][0]
        # sentiment_scores = [float(s) for s in sentiment_scores]
        sentiment_scores = [r['sentiment_scores'] for r in records if r['year']==plot_year][0]
        
        fig, ax = plt.subplots()
        ax = sns.histplot(data=sentiment_scores, bins=10)
        ax.set_xlabel(f'Sentiment Scores ({plot_year})')
        st.pyplot(fig)
