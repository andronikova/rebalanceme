from flask import Flask, render_template, request, redirect, session, flash
import math, time
from flask_mail import Mail, Message
import os

# from apscheduler.scheduler import Scheduler
# from flask_apscheduler import APScheduler

from helpers import apiprice, error_page, load_portfolio_info

from send_email import scheduling
from flask_migrate import Migrate
app = Flask(__name__)


userid = 1 #TODO - download from session

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or \
                           "fg45hjkrgrJJKJLDSV890000jkjk"
app.config['MAIL_SERVER'] = 'smtp.yandex.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'andronikova.daria@ya.ru'  # введите свой адрес электронной почты здесь
app.config['MAIL_DEFAULT_SENDER'] = 'andronikova.daria@ya.ru'  # и здесь
app.config['MAIL_PASSWORD'] = 'assa1221'  # введите пароль

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or \
                                        "postgresql://postgres:1111111@localhost:5432/rebalanceme"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


# with app.app_context():
#     scheduling(app)

# load databases
from models import db, portfolio_db, cash_db, ticker_db, class_db

#
# database settings and creation of tables
with app.app_context():
    db.init_app(app)
    migrate = Migrate(app,db)


@app.route('/', methods=['GET','POST'])
def index_page():
    if request.method == "GET":
        #check session for portfolio information
        if session.get('portfolio_ticker') is None:
            boolres = load_portfolio_info(userid, ticker_db, cash_db, class_db, True)

            if boolres == False:
                return render_template("index_newuser.html")

        symbols = {"USD": '$', "EUR": '€'}
        main_currency = 'EUR'

        # for user WITH PORTFOLIO
        return render_template('index.html',
                               portfolio_ticker=session.get('portfolio_ticker'),
                               portfolio_cash=session.get('portfolio_cash'),
                               portfolio_class=session.get('portfolio_class'),
                               total=session.get('total'),
                               total_cash=session.get('total_cash'),
                               suggestion=session.get('suggestion'),
                               date=session.get('datetime'),
                               symbol=symbols,
                               main_currency=main_currency
                               )

    if request.method == "POST":
        if request.form.get("refresh") is not None:
            print("refreshing page")

            boolres = load_portfolio_info(userid, ticker_db, cash_db, class_db, True)

            if boolres == False:
                return render_template("index_newuser.html")

            return redirect("/")


@app.route("/rebalance", methods=['GET','POST'])
def rebalance():
    if request.method == "GET":
        # return redirect("/")
        portfolio = session.get("portfolio_ticker")

        # create dict of id input formsload_portfolio in rebalence.html
        ids = {}
        idtag = ['price','realFraction','newnumber','oldnumber']
        for key in portfolio:
            ids[key] = {}
            for tag in idtag:
                ids[key].update({tag: tag + "_" + key})

        # calculate all cash in usd
        cash = session.get('cash')
        total_cash = cash['rub']['usdprice'] + cash['euro']['usdprice'] +  cash['usd']['usdprice']

        total = session.get('total')
        total_ticker = total - total_cash

        return render_template("rebalance.html",portfolio=portfolio, total=total,
                                   total_cash=total_cash, total_ticker=total_ticker,
                                    date=session.get('datetime'), ids=ids )
    if request.method == "POST":
        # load new number and price
        # change cash
        # change number in portfolio_db
        # if newnumber = 0 -> delete
        # reload portfolio in session
        return redirect("/")


@app.route('/settings', methods=['GET','POST'])
def settings():
    if request.method == "GET":
      return redirect("/")
#         return render_template('settings.html')
#
#     if request.method == "POST":
#         if request.form.get("send") is not None:
#             sending_email()
#             return redirect("/settings")

@app.route('/newuser', methods=['GET','POST'])
def newuser():
    #TODO  create new row in cash_db with zero money
    return redirect("/")


@app.route('/cash', methods=['GET','POST'])
def cash():
    if request.method == "GET":
        return render_template('cash.html', portfolio_cash=session.get('portfolio_cash'),
                           exchange=session.get('exchange')
                           )

    if request.method == "POST":
        if request.form.get("cashvalue") is not None:
            print('get new cash values from user')
            # value from cash page
            cash = float(request.form.get('cashvalue'))
            currency = request.form.get('currency')

            # value from cash in session
            oldcash = session.get('portfolio_cash')
            print(f"old cash is {oldcash}")
            newcash = oldcash[currency] + cash

            # in case of decreasing of cash - check do we have such money
            if newcash < 0:
                return error_page("You don't have enough cash.")

            # change cash db
            cash_db.query.filter_by(userid=userid).update({currency:newcash})
            db.session.commit()

            # reload portfolio
            load_portfolio_info(userid, ticker_db, cash_db, class_db, False)

            return redirect('/cash')


@app.route('/class_and_tickers', methods=['GET','POST'])
def class_and_tickers():
    if request.method == "GET":
        return render_template('class_and_tickers.html',
                               portfolio_class=session.get('portfolio_class'),
                               portfolio_ticker=session.get('portfolio_ticker'))


@app.route('/change_class_info', methods=['GET','POST'])
def change_class_info():
    if request.method == "GET":
        portfolio_class = session.get('portfolio_class')

        # create dict of id : classname +_realfraction /fraction_diap / active ticker
        ids = {}
        idtag = ['fraction','diapason','activeticker']
        for key in portfolio_class:
            ids[key] = {}
            for tag in idtag:
                ids[key].update({tag: tag + "_" + key})

        print(ids)
        return render_template('classes_change.html', portfolio_class=portfolio_class,
                               portfolio_ticker=session.get('portfolio_ticker'),
                               ids = ids
                               )

    if request.method == "POST":
        if request.form.get("submit") is not None:
            portfolio_class = session.get("portfolio_class")

            for classname in portfolio_class:
                # load new fraction from website
                tag = 'fraction_' + classname
                new_fraction = request.form.get(tag)
                # print(f"new fraction for {tag} is {new_fraction}")

                #load new diapason from website
                tag = 'diapason_' + classname
                new_diapason = request.form.get(tag)
                # print(f"new fraction for {tag} is {new_diapason}")

                # load new active ticker
                tag = 'activeticker_' + classname
                new_activeticker = request.form.get(tag)
                # print(f"new active ticker for {tag} is {new_activeticker}")

                # save new values in db
                class_db.query.filter_by(userid=userid,classname=classname).update({
                    'fraction': new_fraction,
                    'diapason' : new_diapason,
                    'activeticker' : new_activeticker
                })
                db.session.commit()

        # reload portfolio
        load_portfolio_info(userid, ticker_db, cash_db, class_db, False)
        return redirect("/class_and_tickers")

@app.route('/change_ticker_info', methods=['GET','POST'])
def change_ticker_info():
    if request.method == "GET":
        # create dict of id : ticker + '_' + currency|class
        ids = {}
        idtag = ['currency', 'classname']
        for tck in session.get('portfolio_ticker'):
            ids[tck] = {}
            for tag in idtag:
                ids[tck].update({tag: tag + "_" + tck})

        return render_template('tickers_change.html',
                               portfolio_ticker=session.get('portfolio_ticker'),
                               portfolio_class=session.get('portfolio_class'),
                               ids=ids
                               )

    if request.method == "POST":
        portfolio_ticker = session.get("portfolio_ticker")

        for tck in portfolio_ticker:
            # load new currency and class from website
            tag = 'currency_' + tck
            new_currency = request.form.get(tag)

            tag = 'classname_' + tck
            new_class = request.form.get(tag)
            old_class = portfolio_ticker[tck]['classname']

            # if class was changed, check if it was active ticker
            if new_class != old_class and old_class != 'None':
                portfolio_class = session.get('portfolio_class')
                if portfolio_class[old_class]['activeticker']==tck:
                    # put None in active ticker cell for this class
                    class_db.query.filter_by(userid=userid, classname=old_class).update({
                            'activeticker': 'None'})
                    db.session.commit()

            # save new values in db
            ticker_db.query.filter_by(userid=userid, ticker=tck).update({
                'currency': new_currency,
                'classname': new_class
            })
            db.session.commit()

        # reload portfolio
        load_portfolio_info(userid, ticker_db, cash_db, class_db, False)

        return redirect('/class_and_tickers')


@app.route('/add_ticker', methods=['GET','POST'])
def add_ticker():
    if request.method == "GET":
        return render_template('add_ticker.html',
                               portfolio_ticker=session.get('portfolio_ticker'),
                               portfolio_class=session.get('portfolio_class')
                               )

    if request.method == "POST":
        # check new ticker and load ticker price
        ticker = request.form.get("newticker")

        ticker_info = apiprice(ticker)

        if  ticker_info['price'] == 0:
            print("apology")
            return error_page("Error! Could not load price for such ticker. Probably, ticker name is not correct!")

        # load other info about this ticker
        classname = request.form.get("classname")
        currency = request.form.get('currency')

        # check that this ticker is not in portfolio
        datas = ticker_db.query.filter_by(userid=userid,ticker=ticker).all()
        print(f"check the db for such ticker {datas}")

        if len(datas) != 0:
            return error_page("You already have  such ticker!")

        # load last id from ticker_db and put new id by hand (to avoid IntegrityError duplicate key violates unique-constraint)
        max_id = ticker_db.query.order_by(ticker_db.id.desc()).first().id

        # change portfolio
        new_row = ticker_db(id=max_id+1, userid=userid,
                            ticker=ticker, number=0,classname=classname,currency=currency )

        db.session.add(new_row)
        db.session.commit()

        # reload  new portfolio in session
        load_portfolio_info(userid, ticker_db, cash_db, class_db, True)

    return redirect("/class_and_tickers")


@app.route('/delete_ticker', methods=['GET','POST'])
def delete_ticker():
    if request.method == "GET":
        return render_template('delete_ticker.html',
                               portfolio_ticker=session.get('portfolio_ticker'))

    if request.method == "POST":
        # load ticker name
        ticker = request.form.get("ticker")

        # check if it is active ticker for some class
        portfolio_class = session.get('portfolio_class')

        for classname in portfolio_class:
            if portfolio_class[classname]['activeticker']==ticker:
                # put None in active ticker cell for this class
                class_db.query.filter_by(userid=userid, classname=classname).update({
                    'activeticker': 'None'})
                db.session.commit()

        # delete this ticker from db
        ticker_db.query.filter_by(userid=userid,ticker=ticker).delete(synchronize_session='evaluate')
        db.session.commit()

        # reload info in session
        load_portfolio_info(userid, ticker_db, cash_db, class_db, False)

        return redirect('/class_and_tickers')

@app.route('/delete_class', methods=['GET','POST'])
def delete_class():
    if request.method == "GET":

        return render_template('delete_class.html', portfolio_class=session.get('portfolio_class'))

    if request.method == "POST":
        classname = request.form.get("classname")

        # change classname to None for all tickers in this class
        portfolio_ticker = session.get('portfolio_ticker')
        not_string = ""
        for ticker in portfolio_ticker:
            if portfolio_ticker[ticker]['classname'] == classname:
                not_string += " " + ticker
                ticker_db.query.filter_by(userid=userid, ticker=ticker).update({
                    'classname': 'None'})
                db.session.commit()

        # delete this class from db
        class_db.query.filter_by(userid=userid,classname=classname).delete(synchronize_session='evaluate')
        db.session.commit()

        # reload info in session
        load_portfolio_info(userid, ticker_db, cash_db, class_db, False)

        if len(not_string) >= 1:
            flash('Class deletion leads to None class in tickers:' + not_string)
        return redirect('/class_and_tickers')


@app.route('/add_class', methods=['GET','POST'])
def add_class():
    if request.method == "GET":
        return render_template('add_class.html', portfolio_ticker=session.get('portfolio_ticker') )

    if request.method == "POST":
        classname = request.form.get("classname")
        fraction = request.form.get("diapason")
        diapason = request.form.get("diapason")

        # check: is it new name for class
        for name in session.get('portfolio_class'):
            if name == classname:
                return error_page('Such class exists! Choose another name.')

        #check, that name consists of letters only
        if classname.isalpha() == False:
            return error_page('Class name should consist of letters only!')

        # check that name consist of english letter only
        eng_alphabet=("abcdefghijklmnopqrstuvwxyz")
        for one_char in classname:
            if one_char not in eng_alphabet:
                return error_page('Use only latin letters!')

        # load last id from class_db and put new id by hand (to avoid IntegrityError duplicate key violates unique-constraint)
        max_id = class_db.query.order_by(class_db.id.desc()).first().id

        # change portfolio
        new_row = class_db(id=max_id+1, userid=userid, classname=classname,
                           fraction=fraction, diapason=diapason,
                           activeticker="None")

        db.session.add(new_row)
        db.session.commit()

        # reload  new portfolio in session
        load_portfolio_info(userid, ticker_db, cash_db, class_db, False)

        return redirect("/class_and_tickers")



if __name__ == "__main__":
    app.run(debug=True)
    with app.app_context():
        db.create_all()
        db.session.commit()