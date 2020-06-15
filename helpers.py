import os, urllib.parse, requests, math
import sqlite3 as sql
from flask import Flask, render_template, request, redirect, session
import time

def apiprice(ticker):
    # load price from NY
    try:
        API_KEY = os.environ.get('myAPI_KEY_finnhub')
        response = requests.get(f"https://finnhub.io/api/v1/quote?symbol={urllib.parse.quote_plus(ticker)}&token={API_KEY}")
        response.raise_for_status()

    except requests.RequestException:
        return None

    try:
        resp = response.json()
        return{
            "price": float(resp['c'])
        }

    except (KeyError, TypeError, ValueError):
        return None


def apiexchange():
    try:
        API_KEY = os.environ.get('myAPI_KEY_finnhub')
        base = 'usd'
        response = requests.get(f"https://finnhub.io/api/v1/forex/rates?base={base}&token={API_KEY}")
        response.raise_for_status()

    except requests.RequestException:
        return None

    try:
        resp = response.json()
        print(f"test response {resp['quote']['EUR']}")
        return{
            "euro": float(resp['quote']['EUR']),
            "rub" : float(resp['quote']['RUB'])
        }

    except (KeyError, TypeError, ValueError):
        return None

def error_page(message):
    return render_template("error_page.html",message=message)


def load_portfolio(userid, database,loadprice):
    # loading portfolio information from portfolio db and cash info from cash db
    # loading ticker price using api
    # loadprice = true - loading price, else: take price from session

    # clear portfolio, cash and total info in session
    session.pop('total', None)

    if loadprice == True:
        session.pop('portfolio', None)
        session.pop('datetime', None)
        session.pop('cash', None)

    else:
        # save price and fullName in temp dict before deleting portfolio in session
        oldprice = {}
        tmpportfolio = session.get('portfolio')

        for key in tmpportfolio:
            oldprice[key] = {'price':tmpportfolio[key]['price']}

        session.pop('portfolio', None)

        # save old exchange prices befire clear cash info in session
        oldexchange = {}
        oldexchange['rub'] = session.get('cash')['rub']["tousd"]
        oldexchange['euro'] = session.get('cash')['euro']["tousd"]

        session.pop('cash', None)


    # to load portfolio data from db and combine in with results of API query
    with sql.connect(database) as con:
        # to have result of .execute as dictionary
        con.row_factory = sql.Row
        cur = con.cursor()

        cur.execute("SELECT * FROM portfolio WHERE userid == :userid", {"userid":userid})
        rows = cur.fetchall()

        # check new user
        if len(rows) == 0:
            return False

        # for user WITH not empty PORTFOLIO
        portfolio = {}
        total = 0 # for whole portfolio

        for row in rows:
            portfolio[row['ticker']] = {'number': row['number'], 'fraction': row['fraction']}

            # load new price
            if loadprice == True:
                res = apiprice(row['ticker'])
                if res is not None:
                    portfolio[row['ticker']].update({'price': res['price'], 'fullPrice' : res['price'] * row['number']})
                else:
                    error_page('Could not load price')

            # use old price from session
            else:
                portfolio[row['ticker']].update({'price': oldprice[row['ticker']]['price'], 'fullPrice': oldprice[row['ticker']]['price'] * row['number']})

            # use full price to calculate total sum
            total += portfolio[row['ticker']]['fullPrice']

        # load cash info from db
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute("SELECT rub, usd, euro FROM cash WHERE userid == :userid", {"userid": userid})
        cashres = cur.fetchall()

        # load exchange info: rub to USD and EURO to USD
        if loadprice == True:
            exchange = apiexchange()
            if exchange is None:
                error_page("Could not load exchange rates")
        else:
            exchange = oldexchange

        # save cash and exchange info
        cash = {}
        cash["rub"] = {"value":cashres[0]["rub"],"usdprice": exchange["rub"]*cashres[0]["rub"],"tousd": exchange["rub"],"symbol":"₽"}
        cash["usd"] = {"value": cashres[0]["usd"], "usdprice": cashres[0]["usd"],"tousd": 1,"symbol":"$"}
        cash["euro"] = {"value": cashres[0]["euro"],"usdprice": exchange["euro"]*cashres[0]["euro"],"tousd": exchange["euro"],"symbol":"€"}

        # add to total cash in usd
        total = total + cash["rub"]["usdprice"] + cash["euro"]["usdprice"] + cash["usd"]["usdprice"]

        # calculate fraction for cash
        for key in cash:
            cash[key]['realFraction'] = math.floor(100 * cash[key]["usdprice"] / total)

        # real fraction calculation
        for key in portfolio:
            portfolio[key]["realFraction"] = math.floor(100 * portfolio[key]['fullPrice'] / total)
            portfolio[key]["suggestion"] = rebalance_suggestion(portfolio[key]["number"],portfolio[key]["price"],portfolio[key]["fraction"],total)

    con.close()
    # print(portfolio)

    # save results in session
    # TODO clear session after 12 hours
    session['portfolio'] = portfolio
    session['cash'] = cash
    session['total'] = total

    # case we reload prices
    if session.get('datetime') is None:
        session['datetime'] = time.strftime("%d-%m-%Y, %H:%M")

    return True


def rebalance_suggestion(number, price, fraction, total):
    # calculate number for ticker based on desired fraction
    if price != 0:
        newnumber = round(total * fraction / 100 / price)
        res = newnumber - number
        return res
    else:
        return None