from flask import Flask, render_template, request, redirect, session
import math, time
from flask_mail import Mail, Message
import os


# from apscheduler.scheduler import Scheduler
# from flask_apscheduler import APScheduler

from helpers import apiprice, error_page, load_portfolio

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
from models import db, portfolio_db, cash_db

#
# database settings and creation of tables
with app.app_context():
    db.init_app(app)
    migrate = Migrate(app,db)


@app.route('/', methods=['GET','POST'])
def index_page():
    if request.method == "GET":
        #check session for portfolio information
        if session.get('portfolio') is None:
            boolres = load_portfolio(userid, portfolio_db, cash_db, True)

            #new user
            if boolres == False:
                return render_template('index_newuser.html')

        # for user WITH PORTFOLIO
        return render_template('index.html', portfolio=session.get('portfolio'),total=session.get('total'), cash=session.get('cash'),date=session.get('datetime'))

    if request.method == "POST":
        if request.form.get("refresh") is not None:
            print("refreshing page")

            load_portfolio(userid, portfolio_db, cash_db, True)
            return redirect("/")


        if request.form.get("cashvalue") is not None:
            cash = float(request.form.get('cashvalue'))
            currency = request.form.get('currency')

            oldcash = session["cash"][currency]["value"]
            newcash = oldcash + cash

            # in case of decreasing of cash - check do we have such money
            if newcash < 0:
                return error_page("You don't have enough cash.")

            # change cash db
            cash_db.query.filter_by(userid=userid).update({currency:newcash})
            db.session.commit()

            # reload portfolio
            load_portfolio(userid, portfolio_db, cash_db, False)

            return redirect("/")


@app.route("/rebalance", methods=['GET','POST'])
def rebalance():
    if request.method == "GET":
        return redirect("/")
#         portfolio = session.get("portfolio")
#
#         # create dict of id input formsload_portfolio in rebalence.html
#         ids = {}
#         idtag = ['number', 'price','realFraction','newnumber']
#         for key in portfolio:
#             ids[key] = {}
#             for tag in idtag:
#                 ids[key].update({tag: tag + "_" + key})
#         return render_template("rebalance.html",portfolio=portfolio, total=session.get('total'),
#                                    cash=session.get('cash'), date=session.get('datetime'), ids=ids )
#
#
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
#
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


if __name__ == "__main__":
    app.run(debug=True)
    with app.app_context():
        db.create_all()
        db.session.commit()