from flask import Flask, render_template, request
import sqlite3 as sql
import math


from helpers import apiprice, error_page, load_portfolio

app = Flask(__name__)

DATABASE = 'portfolio.db'
userid = 1 #TODO - download from session

@app.route('/', methods=['GET'])
def index_page_landing():
    portfolio = load_portfolio(userid, DATABASE)

    # for new user
    if portfolio is None:
        return render_template('index_newuser.html')

    # for user WITH PORTFOLIO
    return render_template('index.html', portfolio=portfolio)

@app.route('/rebalance', methods=['GET','POST'])
def rebalance_page():
    if request.method == "GET":
        return render_template("rebalance.html")

@app.route('/books/<genre>')
def books(genre):
    return "All Books in {} category".format(genre)

if __name__ == "__main__":
    app.run(debug=True)