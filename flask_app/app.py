from flask import Flask, request, jsonify
from scripts.get_scores import ItemSentiment

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def results():
    """data = [{
        'company': 'AAPL',
        'before_year': 2020,
        'after_year': 2018
    }]"""
    data = request.json
    scorer = ItemSentiment(data[0])
    records = scorer.run()
    return jsonify(records)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
