FROM python:3.9.1
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
ENTRYPOINT [ "streamlit", "run" ]
CMD ["dash.py"]