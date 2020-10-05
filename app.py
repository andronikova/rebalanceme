from flask import Flask, render_template, request, redirect, session
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
        portfolio = session.get("portfolio")

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

@app.route('/addnewticker', methods=['GET','POST'])
def addnewticker():
    if request.method == "GET":
        return render_template("addnewticker.html")

    if request.method == "POST":
        # check new ticker and load ticker price
        ticker = request.form.get("newticker")

        ticker_info = apiprice(ticker)

        if  ticker_info['price'] == 0:
            print("apology")
            return error_page("Error! Could not load price for such ticker. Probably, ticker name is not correct!")

        # check that this ticker is not in portfolio
        datas = portfolio_db.query.filter_by(userid=userid).all()

        if len(datas) != 0:
            for row in datas:
                if row.ticker == ticker:
                    return error_page("You already have  such ticker!")

        # change portfolio
        new_row = portfolio_db(userid=userid,ticker=ticker, number=0, fraction= 0)

        db.session.add(new_row)
        db.session.commit()

        # reload  new portfolio in session
        load_portfolio(userid, portfolio_db, cash_db, True)
        print("new portfolio is loaded")
        print(session.get('portfolio'))

    return redirect("/changefraction")


@app.route('/changefraction', methods=['GET','POST'])
def changefraction():
    if request.method == "GET":
        return render_template("change_fraction.html",portfolio=session.get('portfolio'), total=session.get('total'),
                                   cash=session.get('cash'), date=session.get('datetime'))

    if request.method == "POST":
        # saving new fraction in portfolio and history
        for key in session["portfolio"]:
            newfraction = request.form.get(key)

            portfolio_db.query.filter_by(userid=userid,ticker=key).update({'fraction':newfraction})
            db.session.commit()

        load_portfolio(userid, portfolio_db,cash_db, False)
        return redirect("/")


@app.route('/history', methods=['GET','POST'])
def history():
    if request.method == "GET":
        return redirect("/")
#         with sql.connect(DATABASE) as con:
#             con.row_factory = sql.Row
#             cur = con.cursor()
#
#             cur.execute("SELECT * FROM history WHERE userid == :userid", {"userid":userid})
#             history = cur.fetchall()
#
#             for row in history:
#                 print(row['eventtype'])
#
#         return render_template('history.html', history=history)
#
#
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


@app.route('/classes', methods=['GET','POST'])
def classes():
    if request.method == "GET":
        return render_template('classes.html', portfolio_class=session.get('portfolio_class'))

    if request.method == "POST":
        if request.form.get("changeclassinfo") is not None:
            return redirect('/change_class_info')


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
        return redirect("/classes")


if __name__ == "__main__":
    app.run(debug=True)
    with app.app_context():
        db.create_all()
        db.session.commit()