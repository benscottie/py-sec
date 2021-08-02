from flask import Flask, request, jsonify, render_template
from scripts.get_scores import ItemSentiment

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def results():
    """data = [{
        'company': 'AAPL',
        'before_year': 2021,
        'after_year': 2000
    }]"""
    data = request.json
    scorer = ItemSentiment(data[0])
    records = scorer.run()
    return jsonify(records)

if __name__ == '__main__':
    app.run(debug=True)
