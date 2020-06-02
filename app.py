from flask import Flask, render_template, request, redirect
import sqlite3 as sql
import math


from helpers import apiprice, error_page, load_portfolio

app = Flask(__name__)

DATABASE = 'portfolio.db'
userid = 1 #TODO - download from session

@app.route('/', methods=['GET'])
def index_page_landing():
    portfolio, total = load_portfolio(userid, DATABASE)

    # for new user
    if portfolio is None:
        return render_template('index_newuser.html')

    # for user WITH PORTFOLIO
    return render_template('index.html', portfolio=portfolio,length=len(portfolio),total=total)

@app.route("/rebalance")
def rebalance_page():
    portfolio, total = load_portfolio(userid, DATABASE)

    # for new user
    if portfolio is None:
        return redirect("/rebalance/addnew")

    return render_template("rebalance.html", portfolio=portfolio,length=len(portfolio),total=total)

@app.route('/rebalance/addnew', methods=['GET','POST'])
def rebalance_page_addnew():
    if request.method == "GET":
        return render_template("rebalance_new.html", type=1)

    if request.method == "POST":
        # check new ticker and load ticker price
        ticker = request.form.get("newticker")

        if apiprice(ticker) is None:
            print("apology")
            return error_page("Ticker name is not correct!")

        price = apiprice(ticker)["price"]
        portfolio, total = load_portfolio(userid, DATABASE)

        return render_template("rebalance_new.html",type=2, ticker=ticker, price=price,total=total)


if __name__ == "__main__":
    app.run(debug=True)