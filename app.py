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
app.config['SECRET_KEY'] = 'flmvt65mnnw50_jjjbdsd09n38bnyj'
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
    db.create_all()
    db.session.commit()

# DATABASE = 'portfolio.db'

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
    #
    #
    #     if request.form.get("cashvalue") is not None:
    #         cash = float(request.form.get('cashvalue'))
    #         currency = request.form.get('currency')
    #         type = request.form.get('cashtype')
    #
    #         oldcash = session["cash"][currency]["value"]
    #         newcash = oldcash + cash
    #
    #         # in case of decreasing of cash - check do we have such money
    #         if newcash < 0:
    #             return error_page("You don't have enough cash.")
    #
    #         # change cash db
    #         with sql.connect(DATABASE) as con:
    #             con.row_factory = sql.Row
    #             cur = con.cursor()
    #
    #             tmp = "UPDATE cash SET " + currency + "=:newcash WHERE userid==:userid"
    #             cur.execute(tmp, {"userid":userid, "newcash":newcash})
    #
    #             #TODO change history
    #
    #         con.close()
    #
    #         # reload portfolio
    #         load_portfolio(userid, DATABASE, False)
    #
    #         return redirect("/")


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
        # return render_template("addnewticker.html")
        return redirect("/")
#
#     if request.method == "POST":
#         # check new ticker and load ticker price
#         ticker = request.form.get("newticker")
#
#         ticker_info = apiprice(ticker)
#         if  ticker_info is None:
#             print("apology")
#             return error_page("Ticker name is not correct!")
#
#         # change portfolio
#         with sql.connect(DATABASE) as con:
#             con.row_factory = sql.Row
#             cur = con.cursor()
#
#             # check that this ticker is not in portfolio
#             cur.execute("SELECT number FROM portfolio WHERE userid == :userid AND ticker == :ticker", {"userid":userid, "ticker":ticker})
#             row = cur.fetchall()
#
#             if len(row) != 0:
#                 return error_page("You already have  such ticker!")
#
#
#             tmpdict = {"ticker":ticker, "number":0, "fraction":0, "userid":userid}
#             cur.execute("INSERT INTO portfolio (ticker,number,fraction,userid) VALUES (:ticker,:number,:fraction,:userid)", tmpdict)
#
#         con.close()
#
#         # reload  new portfolio in session
#         load_portfolio(userid, DATABASE, True)
#
#         return redirect("/changefraction")
#
#
@app.route('/changefraction', methods=['GET','POST'])
def changefraction():
    if request.method == "GET":
        return redirect("/")
        # return render_template("change_fraction.html",portfolio=session.get('portfolio'), total=session.get('total'),
        #                            cash=session.get('cash'), date=session.get('datetime'))

#     if request.method == "POST":
#         with sql.connect(DATABASE) as con:
#             con.row_factory = sql.Row
#             cur = con.cursor()
#
#         # saving new fraction in portfolio and history
#             for key in session["portfolio"]:
#                 fraction = request.form.get(key)
#                 cur.execute("UPDATE portfolio SET fraction=:fraction WHERE userid == :userid AND ticker==:ticker",
#                             {"userid": userid, "ticker": key,"fraction":fraction})
#
#                 tmpdict = {"userid":userid, "date": time.strftime("%d-%m-%Y, %H:%M"), "ticker": key, "number": session["portfolio"][key]['number'],
#                            "price":session["portfolio"][key]['price'], "fraction":fraction, "eventtype":'fraction'}
#                 cur.execute("INSERT INTO history (userid, date, ticker, number, price, fraction, eventtype) VALUES (:userid, :date, :ticker, :number, :price, :fraction, :eventtype)", tmpdict)
#
#         con.close()
#
#         load_portfolio(userid, DATABASE, False)
#         return redirect("/")
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








if __name__ == "__main__":
    app.run(debug=True)