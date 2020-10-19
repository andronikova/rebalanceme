from flask import Flask, render_template, request, redirect, session, flash
from flask_migrate import Migrate
from flask_mail import Mail, Message
from werkzeug.security import check_password_hash, generate_password_hash
import os
from send_email import sending_emil, scheduling

from helpers import apiprice, error_page, load_portfolio_info, prepare_data_for_chart,load_user_settings, test_scheduled_job

app = Flask(__name__)


# userid = 1 #TODO - download from session

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


# load databases
from models import db, cash_db, ticker_db, class_db, user_db, week_db

#
# database settings and creation of tables
with app.app_context():
    db.init_app(app)
    migrate = Migrate(app,db)

# scheduling email sending with APScheduler
# with app.app_context():
#     scheduling(app,user_db,userid)


@app.route('/', methods=['GET','POST'])
def index_page():
    if request.method == "GET":
        # load_portfolio_info(userid, ticker_db, cash_db, class_db,user_db, True)
        if session.get('userid') is None:
            return render_template("index_intro.html")
        else:
            userid = session.get('userid')

        #check session for portfolio information
        if session.get('portfolio_ticker') is None:
            boolres = load_portfolio_info(userid, ticker_db, cash_db, class_db,user_db, True)

            if boolres == False:
                return error_page("There is no portfolio for such user.")


        symbols = {"USD": '$', "EUR": '€'}
        main_currency = session.get('main_currency')

        chart_data = prepare_data_for_chart()

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
                               main_currency=main_currency,
                               chart_data=chart_data,
                               recommendation=session.get('recommendation')
                               )

    if request.method == "POST":
        if request.form.get("refresh") is not None:
            print("refreshing page")

            boolres = load_portfolio_info(userid, ticker_db, cash_db, class_db, user_db, True)

            if boolres == False:
                return render_template("index_newuser.html")

            return redirect("/")

        if request.form.get("change_currency") is not None:
            session['main_currency']  = request.form.get('change_currency')

            return redirect("/")

        if request.form.get("send_by_email") is not None:
            sending_emil(app,user_db,userid)
            return redirect("/")


@app.route("/rebalance", methods=['GET','POST'])
def rebalance():
    if request.method == "GET":
        # create dict of id
        ids = {}
        idtag = ['price', 'newnumber', 'oldnumber', 'classname','exchange']
        for ticker in session.get("portfolio_ticker"):
            ids[ticker] = {}
            for tag in idtag:
                ids[ticker].update({tag: tag + "_" + ticker})


        # calc fraction for cash
        total = session.get("total")
        if total['USD'] != 0:
            cash_fraction = round(100 * session.get('total_cash')['USD'] / total['USD'])
        else:
            cash_fraction = 100

        # list of classes
        classname_list = ['None']
        for classname in session.get("portfolio_class"):
            classname_list = classname_list + [classname]

        symbols = {"USD": '$', "EUR": '€'}

        return render_template("rebalance.html",
                               portfolio_ticker=session.get("portfolio_ticker"),
                               portfolio_class=session.get('portfolio_class'),
                               suggestion=session.get('suggestion'),
                               total=total,
                               total_cash=session.get('total_cash'),
                               date=session.get('datetime'),
                               classname_list=classname_list,
                               main_currency=session.get('main_currency'),
                               exchange=session.get('exchange'),
                               cash_fraction=cash_fraction,
                               symbols=symbols,
                               ids=ids )


    if request.method == "POST":
        portfolio_cash = session.get('portfolio_cash')

        portfolio_ticker = session.get('portfolio_ticker')

        # check that we have enough cash
        # calculate cash changes for all tickers in ticker currency
        for ticker in portfolio_ticker:
            # load new number and price
            new_number = float(request.form.get('newnumber_' + ticker))
            price = float(request.form.get('price_' + ticker))

            old_number = portfolio_ticker[ticker]['number']
            currency = portfolio_ticker[ticker]['currency']

            # change cash in currency of ticker
            portfolio_cash[currency] += (old_number - new_number) * price

            # load new values in ticker_db
            ticker_db.query.filter_by(userid=userid, ticker=ticker).update({
                'number': new_number
            })
            db.session.commit()

        # load new cash values in db
        cash_db.query.filter_by(userid=userid).update({
            'USD': portfolio_cash['USD'],
            'EUR' : portfolio_cash['EUR'],
            'RUB': portfolio_cash['RUB']
        })
        db.session.commit()


        # reload portfolio in session
        load_portfolio_info(userid, ticker_db, cash_db, class_db, user_db, False)

        # check for negative cash
        for key in portfolio_cash:
            if portfolio_cash[key] < 0:
                flash("You have negative cash. You need to exchange some of you currency. Go to /cash page ")

        return redirect("/")


@app.route('/settings', methods=['GET','POST'])
def settings():
    if request.method == "GET":
        user_settings = load_user_settings(user_db, week_db, userid)

        if user_settings == False:
            return error_page("Can't find such user in db")

        return render_template('settings.html', user_settings=user_settings)

    if request.method == "POST":
        test_scheduled_job(app,week_db,user_db,ticker_db, cash_db, class_db)

        return redirect("/settings")


@app.route('/change_settings', methods=['GET','POST'])
def change_settings():
    if request.method == "GET":
        # load user settings from db
        user_settings = load_user_settings(user_db, week_db, userid)
        if user_settings == False:
            return error_page("Can't find such user in db")

        return render_template('settings_change.html',
                               user_settings=user_settings,
                               week_day=['Monday', 'Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'])


    if request.method == "POST":
        print(f"load report_day {request.form.getlist('report_day') }")

        # change values in user db
        user_db.query.filter_by(userid=userid).update({
                    'name': request.form.get('name'),
                    'email': request.form.get('email'),
                    'currency':request.form.get('currency'),
                    'minsum':request.form.get('minimal_operation_sum')
                })

        # change values in week_db
        for week_day in ['Monday', 'Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']:
            week_db.query.filter_by(userid=userid).update({week_day.lower(): False})

            for report_day in request.form.getlist('report_day'):
                if week_day == report_day:
                    week_db.query.filter_by(userid=userid).update({week_day.lower(): True})

        db.session.commit()

        return redirect("/settings")


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
            load_portfolio_info(userid, ticker_db, cash_db, class_db, user_db, False)

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
        load_portfolio_info(userid, ticker_db, cash_db, class_db, user_db, False)
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
        load_portfolio_info(userid, ticker_db, cash_db, class_db, user_db, False)

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
        load_portfolio_info(userid, ticker_db, cash_db, class_db, user_db, True)

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
        load_portfolio_info(userid, ticker_db, cash_db, class_db, user_db, False)

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
        load_portfolio_info(userid, ticker_db, cash_db, class_db, user_db, False)

        if len(not_string) >= 1:
            flash('Class deletion leads to None class in tickers:' + not_string)
        return redirect('/class_and_tickers')


@app.route('/add_class', methods=['GET','POST'])
def add_class():
    if request.method == "GET":
        return render_template('add_class.html', portfolio_ticker=session.get('portfolio_ticker') )

    if request.method == "POST":
        classname = request.form.get("classname")

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
                           fraction=0, diapason=0,
                           activeticker="None")

        db.session.add(new_row)
        db.session.commit()

        # reload  new portfolio in session
        load_portfolio_info(userid, ticker_db, cash_db, class_db, user_db, False)

        return redirect("/class_and_tickers")


@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == "GET":
        return render_template('login.html')

    if request.method == "POST":
        email = request.form.get("email")

        # Query database for username
        datas = user_db.query.filter_by(email=email).all()

        # Ensure username exists and password is correct
        if len(datas) != 1 or not check_password_hash(datas[0].password, request.form.get("password")):
            return error_page("invalid username and/or password")

        # Remember which user has logged in
        session["userid"] = datas[0].userid

        return redirect('/')


@app.route('/registration', methods=['GET','POST'])
def registration():
    if request.method == "GET":
        return render_template('registration.html')

    if request.method == "POST":
        # email = request.form.get("email")
        #
        # # Query database for username
        # datas = user_db.query.filter_by(email=email).all()
        #
        # if len(datas) != 0:
        #     return error_page("User with email" + email + " already exists.")
        #
        # # hash password
        # hashed = generate_password_hash(request.form.get("password"))
        #
        # # load last id from user_db
        # max_id = user_db.query.order_by(user_db.userid.desc()).first().userid
        # print(f'last userid is {max_id}')
        #
        # new_user = user_db(userid=max_id + 1, name=request.form.get("username"),email=email,password=hashed,
        #                    currency='USD',minsum=0)
        # db.session.add(new_user)
        # db.session.commit()

        return redirect('/')



@app.route('/testaccaunt', methods=['GET','POST'])
def testaccaunt():
    if request.method == "GET":
        return render_template('testaccaunt.html')



if __name__ == "__main__":
    app.run(debug=True)
    with app.app_context():
        db.create_all()
        db.session.commit()