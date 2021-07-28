# py-sec

## setting up environment
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

## run app
The app can be run by calling either `flask run` or `python app.py` from the command line
within the root directory and specificed virutal environment.