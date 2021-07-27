from flask import Flask, request, jsonify, render_template
from scripts.get_scores import ItemSentiment

app = Flask(__name__)

"""
@app.route('/')
def home():
    return render_template('home.html')
"""

@app.route('/', methods=['GET', 'POST'])
def results():
    data = {
        'company': 'GOOG',
        'year': 2020
    }
    #data = {
      #  'company': request.form['company'],
       # 'year': request.form['year']
    # }
    scorer = ItemSentiment(data)
    records = scorer.run()
    return jsonify(records)

if __name__ == '__main__':
    app.run(debug=True)
