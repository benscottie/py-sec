# py-sec

## objective
This library provides a tool for:
1. Extracting `SEC 10-K Filings` for Specified Companies and Years
2. Parsing `Item 7 (MD&A)` and Subsections from the extracted 10-K Filings
3. Determining patterns of negative sentiment scores with these sections
4. Serving results through a `Flask API`
5. Storing results in `PostgreSQL Database`
6. Visualizing results through a `Streamlit Dashboard`
7. Enabling Deployment of the frontend dashboard and backend API in a `Dockerized` environment

## setting up python environment
1. `git clone` repository
2. Set up virtual environment: `python -m venv py-sec`
3. Install dependencies: `pip install -r requirements.txt`

## setting up flask environment
1. In the root directory create a file called `.env`
2. Inside the file add the following environment variables:
   
    ```
    FLASK_APP=app.py
    FLASK_ENV=development
    FLASK_DEBUG=0
    DB_NAME=<database name>
    DB_USER=<your username>
    DB_PASSWORD=<database password>
    ```

## run flask api
The api/app can be run by calling either `flask run` or `python app.py` from the command line
within the `flask_app` directory and specificed virutal environment.

## run streamlit dashboard
The streamlit dashboard can be run by calling `streamlit run dash.py` from the command line
within the `dash_app` directory and specified virtual environment. The `flask api` must be served simultaneously
with streamlit, as the dashboard acquires the necessary data by making a request to the api endpoint.

## deployment
The `flask api` and `streamlit dashboard` can be served simultaneously using `Docker`.  Run `docker-compose up` to initiate the
`docker-compose.yml` file and serve the api and dashboard in separate Docker containers. The containers are connected over a network,
so that the dashboard can make calls to the api endpoint. The streamlit dashboard is available from the specified port. No virtual environment or
dependencies are necessary through this method.

