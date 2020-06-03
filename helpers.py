import os, urllib.parse, requests, math
import sqlite3 as sql
from flask import Flask, render_template, request, redirect, session
from datetime import datetime

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


def apiexchange():
    # simulation of api query
    resp = {"rub":0.01,"euro":2}
    return resp

    # try:
    #     API_KEY = os.environ.get('myAPI_KEY')
    #     response = requests.get(f"https://cloud.iexapis.com/stable/fx/convert?symbols=USDJPY,USDCAD&amount=100&token={API_KEY}")
    #
    #     response.raise_for_status()
    #
    #     return response
    # except requests.RequestException:
    #     return None

    # try:
    #     resp = response.json()
    #     return {
    #         "name": resp['companyName'],
    #         "price": float(resp['latestPrice'])
    #     }
    # except (KeyError, TypeError, ValueError):
    #     return None


def error_page(message):
    return render_template("error_page.html",message=message)


def load_portfolio(userid, database):
    # to load portfolio data from db and combine in with results of API query
    with sql.connect(database) as con:
        # to have result of .execute as dictionary
        con.row_factory = sql.Row
        cur = con.cursor()

        cur.execute("SELECT * FROM portfolio WHERE userid == :userid", {"userid":userid})
        rows = cur.fetchall()

        # for new user
        if len(rows) == 0:
            return False

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

        # load cash info from db
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute("SELECT rub, usd, euro FROM cash WHERE userid == :userid", {"userid": userid})
        cashres = cur.fetchall()

        # load exchange info: rub to USD and EURO to USD
        exchange = apiexchange()

        # save cash and exchange info
        cash = {}
        cash["rub"] = {"value":cashres[0]["rub"],"usdprice": exchange["rub"]*cashres[0]["rub"],"tousd": exchange["rub"],"symbol":"₽"}
        cash["usd"] = {"value": cashres[0]["usd"], "usdprice": cashres[0]["usd"],"tousd": 1,"symbol":"$"}
        cash["euro"] = {"value": cashres[0]["usd"],"usdprice": exchange["euro"]*cashres[0]["euro"],"tousd": exchange["euro"],"symbol":"€"}

        # add to total cash in usd
        total = total + cash["rub"]["usdprice"] + cash["euro"]["usdprice"] + cash["usd"]["usdprice"]

        # calculate fraction of cash
        for key in cash:
            cash[key]['realFraction'] = math.floor(100 * cash[key]["usdprice"] / total)

        # real fraction calculation
        for j in range(i):
            portfolio[j]["realFraction"] = math.floor(100 * portfolio[j]['fullPrice'] / total)


    con.close()

    print(portfolio)
    # save results in session
    # TODO clear session after 12 hours
    session['portfolio'] = portfolio
    session['cash'] = cash
    session['total'] = total
    session['datetime'] = datetime.now()

    return True
