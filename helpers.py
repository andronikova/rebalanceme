import os, urllib.parse, requests, math
import sqlite3 as sql

def apiprice(ticker):
    # load price from NY

    try:
        API_KEY = os.environ.get('myAPI_KEY')
        response = requests.get(f"https://cloud-sse.iexapis.com/stable/stock/{urllib.parse.quote_plus(ticker)}/quote?token={API_KEY}")
        response.raise_for_status()
    except requests.RequestException:
        return None

    try:
        resp = response.json()
        return{
            "name": resp['companyName'],
            "price": float(resp['latestPrice'])
        }
    except (KeyError, TypeError,ValueError):
        return None


def error_page(message):
    return render_template("error_page.html",message=message)

def load_portfolio(userid, database):
    # to load portfolio data from db and comine in with results of API query
    with sql.connect(database) as con:
        # to have result of .execute as dictionary
        con.row_factory = sql.Row
        cur = con.cursor()

        cur.execute("SELECT * FROM portfolio WHERE userid == :userid", {"userid":userid})
        rows = cur.fetchall()

        # for new user
        if len(rows) == 0:
            return None

        # for user WITH PORTFOLIO
        i = 0
        portfolio = {}
        total = 0 # for whole portfolio
        for row in rows:
            res = apiprice(row['ticker'])
            if res is not None:
                portfolio[i] = {'fullName': res['name'], 'price': res['price'],'fullPrice' : res['price'] * row['number'],'ticker' : row['ticker'], 'number' : row['number'], 'fraction' : row['fraction']}

                total += portfolio[i]['fullPrice']
                i += 1
            else:
                error_page('Could not load price')

        # real fraction calculation
        for j in range(i):
            portfolio[j]["realFraction"] = math.floor(100 * portfolio[j]['fullPrice'] / total)

    con.close()
    return portfolio
