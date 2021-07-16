import os, urllib.parse, requests, math, time
from flask import render_template, session
from sqlalchemy import desc
from flask_mail import Mail, Message

def apiprice_marketstack(ticker):

    try:
        API_KEY = os.environ.get('myAPI_KEY_marketstack')
        response = requests.get(f"http://api.marketstack.com/v1/eod/latest?access_key={API_KEY}&symbols={urllib.parse.quote_plus(ticker)}")
        response.raise_for_status()

    except requests.RequestException:
        print(f'exception in loading price for {ticker} using marketstack')
        print(f'response error is {response.json()["error"]}')
        return None

    try:
        print(f"ticket price for {ticker} ist loaded from marketstack")
        resp = response.json()
        return{
            "price": float(resp['data'][0]['close'])
        }

    except (KeyError, TypeError, ValueError):
        print(f"failed to load price for {ticker}, KeyError is {KeyError}, TypeError is {TypeError}, ValueError is {ValueError}.")
        return None


def apiprice_finnhub(ticker):
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


def apiexchange(base, exchange_currency):
    try:
        API_KEY = os.environ.get('myAPI_KEY_finnhub')
        response = requests.get(f"https://finnhub.io/api/v1/forex/rates?base={base}&token={API_KEY}")
        response.raise_for_status()

    except requests.RequestException:
        return None

    try:
        resp = response.json()
        return resp['quote'][exchange_currency]

    except (KeyError, TypeError, ValueError):
        return None

def error_page(message):
    return render_template("error_page.html",message=message)


def load_portfolio_info(userid,ticker_db,cash_db, class_db, user_db, loadprice):
    # def: main function to load all necessary data from databases, calculate suggestions, save everything in session
    # load info for this user from user_id
    datas= user_db.query.filter_by(userid=userid).all()

    # check user existance
    if len(datas) == 0:
        return error_page("Such user doesn't exist")

    min_rebalance_sum = datas[0].minsum
    currency_of_min_sum = datas[0].currency

    # load currency exchange data
    if loadprice == True:
       exchange = load_exchange_info()
       main_currency = datas[0].currency

    else:
        # use old exchange info
        exchange = session.get('exchange')
        main_currency = session.get('main_currency')

    # save in session
    session['exchange'] = exchange
    session['main_currency'] = main_currency

    # load cash info: rub, euro, usd, rub in usd, rub in euro, usd in euro, euro in usd
    portfolio_cash = load_cash_info(userid, cash_db)
    session['portfolio_cash'] = portfolio_cash
    print(f"\ncash info is loaded and saved in dict\n {portfolio_cash}")

    # calculate total cash in usd and euro
    total_cash = calc_total_cash(portfolio_cash, exchange)
    print(f"\ntotal cash is\n{total_cash}")

    # load ticker info: number, price, fullPrice, currency, classname
    print(f'\nloading ticker info. load new price = {loadprice}\n')
    portfolio_ticker = load_ticker_info(userid, ticker_db, loadprice)

    # I put it before check to have empty session in case there is no ticker in portfolio
    session.pop('portfolio_ticker', None)

    # if there is no ticker in portfolio - redirect user to create_portfolio page
    if portfolio_ticker == False:
        return False

    print(f"\nticker info is loaded and saved in dictionary\n {portfolio_ticker}")

    # calculate total (sum of all tickers and cash) in usd and euro
    total = calc_total(portfolio_ticker, total_cash, exchange)
    session['total_cash'] = total_cash
    print(f"\ntotal is\n{total}")

    # load class info : desired fraction, real fraction, active ticker
    portfolio_class = load_class_info(userid, class_db, portfolio_ticker, exchange, total)
    print(f"\nclasses info is loaded and saved in dict\n {portfolio_class}")
    if portfolio_class == False:
        return False

    # calculate rebalance suggestion
    suggestion = calc_rebalance_suggestion(portfolio_ticker, portfolio_class, total, total_cash, exchange)
    print(f"\n rebalance suggestions are \n{suggestion}")

    # check that rebalance sum in class more than min_operation_sum, in this case set 0 for rebalancing
    suggestion = rebalance_sum_more_than_minsum(suggestion, min_rebalance_sum, currency_of_min_sum)
    print(f"\n rebalance suggestions after check for > min_sum \n{suggestion}")

    suggestion = check_that_suggestion_less_than_cash(suggestion, total_cash, exchange)

    # create message with rebalance recommendation
    recommendation = calc_recommendation(suggestion)

    # clear session
    session.pop('portfolio_class', None)
    session.pop('total', None)
    session.pop('suggestion', None)
    session.pop('recommendation', None)

    # save everything in session
    # TODO clear session after 12 hours
    session['portfolio_ticker'] = portfolio_ticker
    session['portfolio_class'] = portfolio_class
    session['total'] = total
    session['suggestion'] = suggestion
    session['recommendation'] = recommendation

    # case we reload prices
    if loadprice is True:
        session['datetime'] = time.strftime("%Y-%m-%d %H:%M")
        #TODO make heroku set right time zone

    return True


def load_exchange_info():
    exchange = dict.fromkeys(['USD', 'EUR', 'RUB'])

    for key in exchange:
        exchange[key] = {key: 1}

        for key2 in exchange:
            if key != key2:
                exchange[key].update({ key2: apiexchange(key, key2) })

    print(f"\nexchange info is loaded via api request and saved in dict\n {exchange}")

    return exchange


def load_ticker_info(userid, ticker_db, loadprice):
# function to fill in portfolio_ticker: number, price, full_price, currency, classname

    # load data from db tickers
    datas = ticker_db.query.filter_by(userid=userid).order_by(desc(ticker_db.classname)).all()
    print(f"\nExtracted from ticker_db data is {datas}")

    # check new user
    if len(datas) == 0:
        print('return false')
        return False

    portfolio_ticker = {}
    # load from db tickers: number, currency
    for row in datas:
        portfolio_ticker[row.ticker] = {
            'number': row.number,
            'currency': row.currency,
            'classname': row.classname
        }

    # load new prices from api request
    if loadprice == True:
        for row in datas:
            res = apiprice_marketstack(row.ticker)
            # TODO: check error messages

            if res is not None:
                portfolio_ticker[row.ticker].update(
                    {
                        'price': res['price'],
                        'fullPrice': res['price'] * row.number
                    })
                # print('ticker price is loaded from marketstack')
            else:
                portfolio_ticker[row.ticker].update(
                    {
                        'price': None,
                        'fullPrice': None
                    })
                print(f'failed to load new price for {row.ticker}')
                # error_page('ERROR. Could not load price')

    # load old prices from session for every tck, check the existence of such tck in session
    if loadprice == False:
        old_ticker_info = session.get('portfolio_ticker')

        for row in datas:
            if row.ticker in old_ticker_info:
                portfolio_ticker[row.ticker].update(
                {
                    'price': old_ticker_info[row.ticker]['price'],
                    'fullPrice': old_ticker_info[row.ticker]['price'] * row.number
                })
            else:
                # if there is no such ticker old version of portfolio
                portfolio_ticker[row.ticker].update({
                        'price': None,
                        'fullPrice': None
                    })
                print('Loading ticket price from session. There is no such ticker in old version of portfolio, put None instead price')

    return portfolio_ticker


def load_cash_info(userid, cash_db):
# load cash info: rub, euro, usd, rub in usd, rub in euro, total_euro, total_usd
    datas = cash_db.query.filter_by(userid=userid).all()
    print(f"Extracted from cash_db data is {datas}")

    # check new user
    if len(datas) == 0:
        return False

    # new dict
    portfolio_cash = dict.fromkeys(['USD','EUR','RUB'])

    for key in portfolio_cash:
        # write in dict value for the currency
        portfolio_cash[key] = datas[0].__dict__[key] / 100

    return portfolio_cash


def load_class_info(userid, class_db, portfolio_ticker, exchange, total):
    # load data from class_db
    datas = class_db.query.filter_by(userid=userid).all()
    print(f"Extracted from class_db data is {datas}")

    # check new user
    if len(datas) == 0:
        return False

    portfolio_class = {}
    # for every class
    for row in datas:
        portfolio_class[row.classname] = {
            'fraction' : row.fraction,
            'diapason' : row.diapason,
            'activeticker' : row.activeticker,
            'USD' : 0
        }

        # calculate total sum of ticks in every class
        for key in portfolio_ticker:
            if portfolio_ticker[key]['classname'] == row.classname:
                koeff = exchange[portfolio_ticker[key]['currency']]['USD']
                portfolio_class[row.classname]['USD'] += koeff * portfolio_ticker[key]['fullPrice']

        koeff = exchange['USD']['EUR']
        portfolio_class[row.classname].update({ 'EUR' : koeff * portfolio_class[row.classname]['USD'] })

        # calculate real fraction for class
        if total['USD'] != 0:
            real_fraction = round(100 * portfolio_class[row.classname]['USD'] / total['USD'])
        else:
            real_fraction = 100

        # update dictionary
        portfolio_class[row.classname].update({ 'realfraction' : real_fraction })

    return portfolio_class


def calc_rebalance_suggestion(portfolio_ticker, portfolio_class, total, total_cash, exchange):
    suggestion = {}
    rebalance_sum = 0

    for classname in portfolio_class:

        # calculate deviation
        real_fraction = portfolio_class[classname]['realfraction']
        real_deviation = portfolio_class[classname]['fraction'] - real_fraction
        acceptable_deviation = portfolio_class[classname]['fraction'] * portfolio_class[classname]['diapason'] / 100

        print(f"\nreal deviation for {classname} is {real_deviation}, while acceptable deviation is {acceptable_deviation}")

        suggestion[classname] = {'number': 0, 'USD': 0, 'EUR': 0, 'message':""}

        print(f" portfolio_class[classname]['activeticker'] is {portfolio_class[classname]['activeticker']}")

        #load price for active ticker
        if portfolio_class[classname]['activeticker'] != 'None':
            ticker_currency = portfolio_ticker[portfolio_class[classname]['activeticker']]['currency']
            ticker_price = portfolio_ticker[portfolio_class[classname]['activeticker']]['price']

        # case when active ticker is None
        else:
            ticker_currency = 'USD'
            ticker_price = 0

        # compare with diapason
        if acceptable_deviation < abs(real_deviation):
            if ticker_price != 0:
                suggestion[classname]['number'] = math.floor(real_deviation * total[ticker_currency] / ticker_price /100)

                suggestion[classname]['USD'] = suggestion[classname]['number'] * exchange[ticker_currency]['USD'] * ticker_price
                suggestion[classname]['EUR'] = suggestion[classname]['USD'] * exchange['USD']['EUR']
            else:
                suggestion[classname] = {'number': None, 'USD': 0, 'EUR': 0}

        # calculate total rebalancing sum
        rebalance_sum += suggestion[classname]['USD']
        print(f"\ntotal rabalance sum is {rebalance_sum}")

    return suggestion


def rebalance_sum_more_than_minsum(suggestion, min_rebalance_sum, currency_of_min_sum):
    for classname in suggestion:
        if abs(suggestion[classname][currency_of_min_sum]) < min_rebalance_sum:
            suggestion[classname]["EUR"] = 0
            suggestion[classname]["USD"] = 0
            suggestion[classname]['number'] = 0

    return suggestion


def check_that_suggestion_less_than_cash(suggestion, total_cash, exchange):
    # routine to check that total rebalancing sum is less than total cash
    rebalance_sum = 0

    # calc total sum of rebalancing
    for classname in suggestion:
        rebalance_sum += suggestion[classname]['USD']


    if rebalance_sum > total_cash['USD']:
        print('total rabalance sum is bigger than cash, the number of tck for rebalancing will be decreased')
        lowest_price = 100000000
        lowest_classname = ''

        # searching for class with cheepest active ticker
        for classname in suggestion:
            if suggestion[classname]['USD'] != 0:
                price = suggestion[classname]['USD']/suggestion[classname]['number']
                if  price < lowest_price:
                    lowest_price = price
                    lowest_classname = classname

        # decrease suggested number in class with cheepest active ticker by 1
        if lowest_classname != '':
            price = suggestion[lowest_classname]['USD']/suggestion[lowest_classname]['number']
            suggestion[lowest_classname]['number'] -= 1
            suggestion[lowest_classname]['USD'] = price * suggestion[lowest_classname]['number']
            suggestion[lowest_classname]['EUR'] = suggestion[lowest_classname]['USD'] * exchange['USD']['EUR']

    return suggestion


def calc_recommendation(suggestion):
    rebalance_sum = 0
    # calc total sum of rebalancing
    for classname in suggestion:
        rebalance_sum += suggestion[classname]['USD']

    if rebalance_sum == 0:
        text = 'No action needed. Your portfolio is balanced.'
    else:
        text = 'Your portfolio needs rebalancing. Go to rebalance page.'

    return text


def calc_total_cash(portfolio_cash, exchange):
    total_cash = {'USD': 0, 'EUR' : 0}

    for key_tot in total_cash:
        for key in portfolio_cash:
            total_cash[key_tot] = total_cash[key_tot] + portfolio_cash[key] * exchange[key][key_tot]

    return total_cash


def calc_total(portfolio_ticker, total_cash, exchange):
    total = {'USD':0}

    # calculate sum of all tickers in USD
    for tck in portfolio_ticker:
        koeff = exchange[ portfolio_ticker[tck]['currency'] ]['USD']
        total['USD'] += koeff * portfolio_ticker[tck]['fullPrice']

    # add cash
    total['USD'] += total_cash['USD']

    # transfer this sum in EUR
    total.update({'EUR': exchange['USD']['EUR'] * total['USD']})

    return total


def prepare_data_for_chart():
    portfolio_class = session.get('portfolio_class')
    total_cash = session.get('total_cash')
    total = session.get('total')

    if total['USD'] != 0:
        cash_percent = round(100 * total_cash['USD'] / total['USD'])
    else:
        cash_percent = 0

    value_list = [cash_percent]
    name_list = ["cash"]
    hover_list = ['cash, ' + str(cash_percent)  + " %"]
    for classname in portfolio_class:
        value_list.append(portfolio_class[classname]['realfraction'])
        name_list.append(classname)
        hover_list.append( classname + ', ' + str(portfolio_class[classname]['realfraction']) + " %")

    chart_data=({'value':value_list, 'names': name_list, 'hover':hover_list})

    return chart_data


def load_user_settings(user_db, week_db, userid):
    # load data from db tickers
    datas = user_db.query.filter_by(userid=userid).all()

    # check new user
    if len(datas) == 0:
        print('return false')
        return False

    # load info about report day
    datas_week = week_db.query.filter_by(userid=userid,).all()

    days=[]
    # choose only column with true value
    for day in datas_week[0].__dict__:
        if getattr(datas_week[0], day) is True:
            days.append(day)

    # write down all user info in dict
    for row in datas:
        user_settings = {
            'name': row.name,
            'email':row.email,
            'currency':row.currency,
            'minimal_operation_sum':row.minsum,
            'report_day': days
        }

    print(f'User settings are loaded in {user_settings}')
    return user_settings


def send_email(email, text, topic, app):
    with app.app_context():
        mail = Mail()
        mail.init_app(app)

        message = Message(topic, recipients=[email])

        message.body = text

        mail.send(message)
