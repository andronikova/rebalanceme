from flask import Flask, render_template, request, redirect, session
import sqlite3 as sql
import math


from helpers import apiprice, error_page, load_portfolio, rebalance_suggestion

app = Flask(__name__)

DATABASE = 'portfolio.db'
userid = 1 #TODO - download from session
app.secret_key = 'xyz'

@app.route('/', methods=['GET','POST'])
def index_page():
    if request.method == "GET":
        #check session for portfolio infromation
        if session.get('portfolio') is None:
            boolres = load_portfolio(userid, DATABASE)

            #new user
            if boolres == False:
                return render_template('index_newuser.html')

        # for user WITH PORTFOLIO
        portfolio = session.get('portfolio')
        cash = session.get('cash')
        total = session.get('total')
        date = session.get('datetime')

        return render_template('index.html', portfolio=portfolio,length=len(portfolio),total=total, cash=cash,date=date)

    if request.method == "POST":
        if request.form.get("refresh") is not None:
            print('refreshing page')

            load_portfolio(userid, DATABASE)
            portfolio = session.get('portfolio')
            cash = session.get('cash')
            total = session.get('total')
            date = session.get('datetime')

            return render_template('index.html', portfolio=portfolio, length=len(portfolio), total=total, cash=cash, date=date)


@app.route("/rebalance")
def rebalance_page():
    portfolio, total, cash = load_portfolio(userid, DATABASE)

    # for new user
    if portfolio is None:
        return redirect("/rebalance/addnew")

    return render_template("rebalance.html", portfolio=portfolio,length=len(portfolio),total=total)

@app.route('/addnewticker', methods=['GET','POST'])
def addnewticker():
    if request.method == "GET":
        return render_template("addnewticker.html")

    if request.method == "POST":
        # check new ticker and load ticker price
        ticker = request.form.get("newticker")

        ticker_info = apiprice(ticker)
        if  ticker_info is None:
            print("apology")
            return error_page("Ticker name is not correct!")

        # change portfolio
        with sql.connect(DATABASE) as con:
            con.row_factory = sql.Row
            cur = con.cursor()

            # check that this ticker is not in portfolio
            cur.execute("SELECT number FROM portfolio WHERE userid == :userid AND ticker == :ticker", {"userid":userid, "ticker":ticker})
            row = cur.fetchall()

            if len(row) != 0:
                return error_page("You already have  such ticker!")


            tmpdict = {"ticker":ticker, "number":0, "fraction":0, "userid":userid}
            cur.execute("INSERT INTO portfolio (ticker,number,fraction,userid) VALUES (:ticker,:number,:fraction,:userid)", tmpdict)

        con.close()



        # change history
        # rewrite info in session

        return redirect("/changefraction")

@app.route('/changefraction', methods=['GET','POST'])
def change_fraction():
    if request.method == "GET":

        return render_template("change_fraction.html")

if __name__ == "__main__":
    app.run(debug=True)