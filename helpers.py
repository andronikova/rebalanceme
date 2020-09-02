import os, urllib.parse, requests, math
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


def apiexchange(base):
    try:
        API_KEY = os.environ.get('myAPI_KEY_finnhub')
        response = requests.get(f"https://finnhub.io/api/v1/forex/rates?base={base}&token={API_KEY}")
        response.raise_for_status()

    except requests.RequestException:
        return None

    try:
        resp = response.json()
        return resp['quote']['USD']

    except (KeyError, TypeError, ValueError):
        return None

def error_page(message):
    return render_template("error_page.html",message=message)


def load_portfolio(userid, portfolio_db,cash_db,loadprice):
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
        # save prices in temp dict before deleting portfolio in session
        oldprice = {}
        tmpportfolio = session.get('portfolio')

        for key in tmpportfolio:
            oldprice[key] = {'price':tmpportfolio[key]['price']}

        session.pop('portfolio', None)

        # save old exchange prices before clear cash info in session
        oldexchange = {}
        oldexchange['rub'] = session.get('cash')['rub']["tousd"]
        oldexchange['euro'] = session.get('cash')['euro']["tousd"]

        session.pop('cash', None)


    # to load portfolio data from db and combine in with results of API query
    datas = portfolio_db.query.filter_by(userid=userid).all()

    # check new user
    if datas is None:
        return False

    # if user exists in database
    portfolio = {}
    total = 0 # for whole portfolio

    for row in datas:
        portfolio[row.ticker] = {
            'number': row.number,
            'fraction': row.fraction
        }

        # load new price
        if loadprice == True:
            res = apiprice(row.ticker)
            if res is not None:
                print('saving new prices')
                portfolio[row.ticker].update(
                    {
                    'price': res['price'],
                    'fullPrice' : res['price'] * row.number
                    })
            else:
                error_page('Could not load price')

        # use old price from session
        else:
            portfolio[row.ticker].update({
                'price': oldprice[row.ticker]['price'],
                'fullPrice': oldprice[row.ticker]['price'] * row.number
            })

        # use full price to calculate total sum
        total += portfolio[row.ticker]['fullPrice']

    print(f"total before cash {total}")

    # PREPARE CASH INFO
    # load exchange info: rub to USD and EURO to USD
    if loadprice == True:
        exchange = {
            "euro": apiexchange('EUR'),
            "rub" : apiexchange('RUB')
        }

        print(exchange)

        if exchange is None:
            error_page("Could not load exchange rates")

    else:
        exchange = oldexchange

    # load cash info from db
    cash_datas = cash_db.query.filter_by(userid=userid).all()

    if cash_datas is None:
        cash = {}
    else:
        cashres = cash_datas[0]

        # save cash and exchange info
        cash = {}
        cash["rub"] = {
            "value":cashres.rub,
            "usdprice": exchange["rub"]*cashres.rub,
            "tousd": exchange["rub"],
            "symbol":"₽"
        }
        cash["usd"] = {
            "value": cashres.usd,
            "usdprice": cashres.usd,
            "tousd": 1,
            "symbol":"$"
        }
        cash["euro"] = {
            "value": cashres.euro,
            "usdprice": exchange["euro"]*cashres.euro,
            "tousd": exchange["euro"],
            "symbol":"€"
        }

    # CALCULATE TOTAL SUM AND FRACTION
    # add to total sum cash in usd
    total = total + cash["rub"]["usdprice"] + cash["euro"]["usdprice"] + cash["usd"]["usdprice"]

    # calculate fraction for cash
    for key in cash:
        cash[key]['realFraction'] = math.floor(100 * cash[key]["usdprice"] / total)

    # real fraction calculation
    for key in portfolio:
        portfolio[key]["realFraction"] = math.floor(100 * portfolio[key]['fullPrice'] / total)
        portfolio[key]["suggestion"] = rebalance_suggestion(portfolio[key]["number"],portfolio[key]["price"],portfolio[key]["fraction"],total)


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

