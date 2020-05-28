from flask import Flask, render_template, request
import sqlite3 as sql
import math


from helpers import apiprice, error_page

app = Flask(__name__)

DATABASE = 'portfolio.db'
userid = 1 #TODO - download from session

@app.route('/', methods=['GET'])
def index_page_landing():

    with sql.connect(DATABASE) as con:
        # to have result of .execute as dictionary
        con.row_factory = sql.Row
        cur = con.cursor()

        cur.execute("SELECT * FROM portfolio WHERE userid == :userid", {"userid":userid})
        rows = cur.fetchall()

        # for new user
        if len(rows) == 0:

            return render_template('index_newuser.html')

        # for user WITH PORTFOLIO
        i = 0
        row_api = {}
        total = 0 # for whole portfolio
        for row in rows:
            res = apiprice(row['ticker'])
            if res is not None:
                row_api[i] = {'fullName': res['name'], 'price': res['price'],'fullPrice' : res['price'] * row['number']}
                total += row_api[i]['fullPrice']
                i += 1
            else:
                error_page('Could not load price')

        # real fraction calculation
        for j in range(i):
            row_api[j]["realFraction"] = math.floor(100 * row_api[j]['fullPrice'] / total)

        return render_template('index.html', row=rows, row_api=row_api,length=i, total=total)
        con.close()

@app.route('/rebalance', methods=['GET','POST'])
def rebalance_page():
    if request.method == "GET":
        return render_template("rebalance.html")



if __name__ == "__main__":
    app.run(debug=True)