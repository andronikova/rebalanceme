from flask import Flask, render_template, request, redirect, session, flash
from flask_migrate import Migrate
from werkzeug.security import check_password_hash, generate_password_hash
import os, secrets, time

from helpers import apiprice, error_page, load_portfolio_info, prepare_data_for_chart,load_user_settings, send_email

app = Flask(__name__)

# should be = 1, but is you want make some change in user test account - put some random number
test_account_userid = 1

#TODO hide all keys
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY_rebalanceme')
app.config['MAIL_SERVER'] = 'smtp.yandex.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'andronikova.daria@ya.ru'
app.config['MAIL_DEFAULT_SENDER'] = 'andronikova.daria@ya.ru'
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or \
                                        "postgresql://postgres:1111111@localhost:5432/rebalanceme"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


# load databases
from models import db, cash_db, ticker_db, class_db, user_db, week_db


# database settings and creation of tables
with app.app_context():
    db.init_app(app)
    migrate = Migrate(app,db)


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

            # case of empty portfolio
            if boolres == False:
                return redirect('/create_portfolio')

        else: # check the date of last loading of prices
            # find day, month, year
            year_month_day = ""
            for i in session.get('datetime'):
                if i == " ":
                    break
                else:
                    year_month_day += i

            # if prices wasn't load today - refresh them
            if  year_month_day != time.strftime("%Y-%m-%d"):
                load_portfolio_info(userid, ticker_db, cash_db, class_db, user_db, True)

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

            boolres = load_portfolio_info(session.get('userid'), ticker_db, cash_db, class_db, user_db, True)

            if boolres == False:
                return redirect('/create_portfolio')

            return redirect("/")

        if request.form.get("change_currency") is not None:
            session['main_currency']  = request.form.get('change_currency')

            # change values in user db
            user_db.query.filter_by(userid=session.get('userid')).update({
                'currency': request.form.get('change_currency'),
            })

            db.session.commit()

            return redirect("/")


@app.route("/rebalance", methods=['GET','POST'])
def rebalance():
    if request.method == "GET":
        # check user in session
        if session.get('userid') is None:
            return render_template("index_intro.html")

        # check nonempty portfolio
        if session.get('portfolio_ticker') is None:
            return redirect('/create_portfolio')


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
        # for test account - don't do anything
        if session.get('userid') == test_account_userid: return redirect("/")

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
            ticker_db.query.filter_by(userid=session.get('userid'), ticker=ticker).update({
                'number': new_number
            })
            db.session.commit()

        # load new cash values in db
        cash_db.query.filter_by(userid=session.get('userid')).update({
            'USD': portfolio_cash['USD'],
            'EUR' : portfolio_cash['EUR'],
            'RUB': portfolio_cash['RUB']
        })
        db.session.commit()


        # reload portfolio in session
        load_portfolio_info(session.get('userid'), ticker_db, cash_db, class_db, user_db, False)

        # check for negative cash
        for key in portfolio_cash:
            if portfolio_cash[key] < 0:
                flash("You have negative cash. You need to exchange some of you currency. Go to /cash page ")

        return redirect("/")


@app.route('/settings', methods=['GET','POST'])
def settings():
    if request.method == "GET":
        # check user in session
        if session.get('userid') is None:
            return render_template("index_intro.html")

        user_settings = load_user_settings(user_db, week_db, session.get('userid'))

        if user_settings == False:
            return error_page("Can't find such user in db")

        return render_template('settings.html', user_settings=user_settings)

    if request.method == "POST":
        if request.form.get("send") is not None:
            # for test account - don't do anything
            if session.get('userid') == test_account_userid: return redirect("/settings")

            # send test email
            datas = user_db.query.filter_by(userid=session.get('userid')).all()

            topic = 'Test message from REBALANCEme'
            text = 'It is test email from REBALANCEme app.'

            send_email(datas[0].email, text, topic, app)

            return redirect("/settings")

        if request.form.get("delete") is not None:
            # for test account - don't do anything
            if session.get('userid') == test_account_userid: return redirect("/")

            # delete user from all db: week, cash, ticker, class, user
            week_db.query.filter_by(userid=session.get('userid')).delete(synchronize_session='evaluate')
            class_db.query.filter_by(userid=session.get('userid')).delete(synchronize_session='evaluate')
            ticker_db.query.filter_by(userid=session.get('userid')).delete(synchronize_session='evaluate')
            cash_db.query.filter_by(userid=session.get('userid')).delete(synchronize_session='evaluate')
            user_db.query.filter_by(userid=session.get('userid')).delete(synchronize_session='evaluate')

            db.session.commit()

            # clear session
            session.clear()

            return redirect("/")


@app.route('/change_settings', methods=['GET','POST'])
def  change_settings():
    if request.method == "GET":
        # check user in session
        if session.get('userid') is None:
            return render_template("index_intro.html")

        # load user settings from db
        user_settings = load_user_settings(user_db, week_db, session.get('userid'))
        if user_settings == False:
            return error_page("Can't find such user in db")

        return render_template('settings_change.html',
                               user_settings=user_settings,
                               week_day=['Monday', 'Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'])


    if request.method == "POST":
        # for test account - don't do anything
        if session.get('userid') == test_account_userid: return redirect("/settings")

        print(f"load report_day {request.form.getlist('report_day') }")

        # change values in user db
        user_db.query.filter_by(userid=session.get('userid')).update({
                    'name': request.form.get('name'),
                    'email': request.form.get('email'),
                    'currency':request.form.get('currency'),
                    'minsum':request.form.get('minimal_operation_sum')
                })

        # change values in week_db
        for week_day in ['Monday', 'Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']:
            week_db.query.filter_by(userid=session.get('userid')).update({week_day.lower(): False})

            for report_day in request.form.getlist('report_day'):
                if week_day == report_day:
                    week_db.query.filter_by(userid=session.get('userid')).update({week_day.lower(): True})

        db.session.commit()

        return redirect("/settings")


@app.route('/cash', methods=['GET','POST'])
def cash():
    if request.method == "GET":
        # check user in session
        if session.get('userid') is None:
            return render_template("index_intro.html")

        return render_template('cash.html', portfolio_cash=session.get('portfolio_cash'),
                           exchange=session.get('exchange')
                           )

    if request.method == "POST":
        if request.form.get("cashvalue") is not None:
            # for test account - don't do anything
            if session.get('userid') == test_account_userid: return redirect("/cash")

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
            cash_db.query.filter_by(userid=session.get('userid')).update({currency:newcash})
            db.session.commit()

            # reload portfolio
            load_portfolio_info(session.get('userid'), ticker_db, cash_db, class_db, user_db, False)

            return redirect('/cash')


@app.route('/class_and_tickers', methods=['GET','POST'])
def class_and_tickers():
    if request.method == "GET":
        # check user in session
        if session.get('userid') is None:
            return render_template("index_intro.html")

        # check nonempty portfolio
        if session.get('portfolio_ticker') is None:
            return redirect('/create_portfolio')

        return render_template('class_and_tickers.html',
                               portfolio_class=session.get('portfolio_class'),
                               portfolio_ticker=session.get('portfolio_ticker'))


@app.route('/change_class_info', methods=['GET','POST'])
def change_class_info():
    if request.method == "GET":
        portfolio_class = session.get('portfolio_class')

        # create dict of id : classname +_realfraction /fraction_diap / active ticker
        ids = {}
        idtag = ['fraction','diapason','activeticker','name']
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
            # for test account - don't do anything
            if session.get('userid') == test_account_userid: return redirect("/class_and_tickers")

            portfolio_class = session.get("portfolio_class")

            for classname in portfolio_class:
                # load classname from website
                tag = 'name_' + classname
                new_classname = request.form.get(tag)

                if new_classname != classname:
                    # check: is it new name for class
                    if session.get('portfolio_class') is not None:
                        for name in session.get('portfolio_class'):
                            if name == new_classname:
                                return error_page('Such class exists! Choose another name.')

                # load new fraction from website
                tag = 'fraction_' + classname
                new_fraction = request.form.get(tag)

                #load new diapason from website
                tag = 'diapason_' + classname
                new_diapason = request.form.get(tag)

                # load new active ticker
                tag = 'activeticker_' + classname
                new_activeticker = request.form.get(tag)

                # save new values in db
                class_db.query.filter_by(userid=session.get('userid'),classname=classname).update({
                    'classname': new_classname,
                    'fraction': new_fraction,
                    'diapason' : new_diapason,
                    'activeticker' : new_activeticker
                })
                db.session.commit()

        # reload portfolio
        load_portfolio_info(session.get('userid'), ticker_db, cash_db, class_db, user_db, False)
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
        # for test account - don't do anything
        if session.get('userid') == test_account_userid: return redirect("/class_and_tickers")

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
                    class_db.query.filter_by(userid=session.get('userid'), classname=old_class).update({
                            'activeticker': 'None'})
                    db.session.commit()

            # save new values in db
            ticker_db.query.filter_by(userid=session.get('userid'), ticker=tck).update({
                'currency': new_currency,
                'classname': new_class
            })
            db.session.commit()

        # reload portfolio
        load_portfolio_info(session.get('userid'), ticker_db, cash_db, class_db, user_db, False)

        return redirect('/class_and_tickers')


@app.route('/add_ticker', methods=['GET','POST'])
def add_ticker():
    if request.method == "GET":
        return render_template('add_ticker.html',
                               portfolio_class=session.get('portfolio_class')
                               )

    if request.method == "POST":
        # for test account - don't do anything
        if session.get('userid') == test_account_userid: return redirect("/class_and_tickers")

        # check new ticker and load ticker price
        ticker = request.form.get("newticker")

        ticker_info = apiprice(ticker)

        if  ticker_info['price'] == 0:
            print("apology")
            return error_page("Error! Could not load price for such ticker. Probably, ticker name is not correct!")

        # load other info about this ticker
        if session.get('portfolio_class') is not None:
            classname = request.form.get("classname")
        else:
            classname = 'None'

        currency = request.form.get('currency')

        # check that this ticker is not in portfolio
        datas = ticker_db.query.filter_by(userid=session.get('userid'),ticker=ticker).all()
        print(f"check the db for such ticker {datas}")

        if len(datas) != 0:
            return error_page("You already have such ticker!")

        # load last id from ticker_db and put new id by hand (to avoid IntegrityError duplicate key violates unique-constraint)
        max_id = ticker_db.query.order_by(ticker_db.id.desc()).first().id

        # change portfolio
        new_row = ticker_db(id=max_id+1, userid=session.get('userid'),
                            ticker=ticker, number=0,classname=classname,currency=currency )

        db.session.add(new_row)
        db.session.commit()

        # reload  new portfolio in session
        load_portfolio_info(session.get('userid'), ticker_db, cash_db, class_db, user_db, True)

    return redirect("/class_and_tickers")


@app.route('/delete_ticker', methods=['GET','POST'])
def delete_ticker():
    if request.method == "GET":
        return render_template('delete_ticker.html',
                               portfolio_ticker=session.get('portfolio_ticker'))

    if request.method == "POST":
        # for test account - don't do anything
        if session.get('userid') == test_account_userid: return redirect("/class_and_tickers")

        # load ticker name
        ticker = request.form.get("ticker")

        # check if it is active ticker for some class
        portfolio_class = session.get('portfolio_class')

        for classname in portfolio_class:
            if portfolio_class[classname]['activeticker']==ticker:
                # put None in active ticker cell for this class
                class_db.query.filter_by(userid=session.get('userid'), classname=classname).update({
                    'activeticker': 'None'})
                db.session.commit()

        # delete this ticker from db
        ticker_db.query.filter_by(userid=session.get('userid'),ticker=ticker).delete(synchronize_session='evaluate')
        db.session.commit()

        # reload info in session
        load_portfolio_info(session.get('userid'), ticker_db, cash_db, class_db, user_db, False)

        return redirect('/class_and_tickers')


@app.route('/delete_class', methods=['GET','POST'])
def delete_class():
    if request.method == "GET":
        return render_template('delete_class.html', portfolio_class=session.get('portfolio_class'))

    if request.method == "POST":
        # for test account - don't do anything
        if session.get('userid') == test_account_userid: return redirect("/class_and_tickers")

        classname = request.form.get("classname")

        # change classname to None for all tickers in this class
        portfolio_ticker = session.get('portfolio_ticker')
        not_string = ""
        for ticker in portfolio_ticker:
            if portfolio_ticker[ticker]['classname'] == classname:
                not_string += " " + ticker
                ticker_db.query.filter_by(userid=session.get('userid'), ticker=ticker).update({
                    'classname': 'None'})
                db.session.commit()

        # delete this class from db
        class_db.query.filter_by(userid=session.get('userid'),classname=classname).delete(synchronize_session='evaluate')
        db.session.commit()

        # reload info in session
        load_portfolio_info(session.get('userid'), ticker_db, cash_db, class_db, user_db, False)

        if len(not_string) >= 1:
            flash('Class deletion leads to None class in tickers:' + not_string)
        return redirect('/class_and_tickers')


@app.route('/add_class', methods=['GET','POST'])
def add_class():
    if request.method == "GET":
        return render_template('add_class.html')

    if request.method == "POST":
        # for testoaccount - don't do anything
        if session.get('userid') == test_account_userid: return redirect("/class_and_tickers")

        classname = request.form.get("classname")

        # check: is it new name for class
        if session.get('portfolio_class') is not None:
            for name in session.get('portfolio_class'):
                if name == classname:
                    return error_page('Such class exists! Choose another name.')

        # #check, that name consists of letters only
        # if classname.isalpha() == False:
        #     return error_page('Class name should consist of letters only!')
        #
        # # check that name consist of english letter only
        # eng_alphabet=("abcdefghijklmnopqrstuvwxyz")
        # for one_char in classname.lower():
        #     if one_char not in eng_alphabet:
        #         return error_page('Use only latin letters!')

        # load last id from class_db and put new id by hand (to avoid IntegrityError duplicate key violates unique-constraint)
        max_id = class_db.query.order_by(class_db.id.desc()).first().id

        # change portfolio
        new_row = class_db(id=max_id+1, userid=session.get('userid'), classname=classname,
                           fraction=0, diapason=0,
                           activeticker="None")

        db.session.add(new_row)
        db.session.commit()

        # reload  new portfolio in session
        if session.get('portfolio_ticker') is None:
            # load new prices
            load_portfolio_info(session.get('userid'), ticker_db, cash_db, class_db, user_db, True)
        else:
            # use prices from session
            load_portfolio_info(session.get('userid'), ticker_db, cash_db, class_db, user_db, False)

        return redirect("/class_and_tickers")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route('/change_password', methods=['GET','POST'])
def change_password():
    if request.method == "GET":
        return render_template('change_password.html')

    if request.method == "POST":
        userid = session.get('userid')
        datas = user_db.query.filter_by(userid=userid).all()

        # check old password
        if check_password_hash(datas[0].hash, request.form.get("old")) is False:
            return error_page('Your old password is not correct.')

        # save new hashed password
        user_db.query.filter_by(userid=userid).update(
            {
                'hash':generate_password_hash(request.form.get("new"))
            })
        db.session.commit()

        return redirect('/')

@app.route('/forgot_password', methods=['GET','POST'])
def forgot_password():
    if request.method == "GET":
        return render_template('forgot_password.html')

    if request.method == "POST":
        # check that this email in user_db
        email = request.form.get("email")
        datas = user_db.query.filter_by(email=email).all()
        if len(datas) == 0:
            return error_page('There is no user with email ' + email)

        # generate new password
        new_password = secrets.token_hex(16)

        # send password to user
        text = 'Dear ' + datas[0].name + '\nhere is your new password:\n' + new_password
        text += '\nPlease, change this password as soon as possible. \n\nRebalanceMe'
        topic = 'RebalanceMe: your new password'

        send_email(email, text, topic, app)
        print(f"new password has been created and send to {email}")

        # save this password in user_db
        user_db.query.filter_by(email=email).update({
            'hash' : generate_password_hash(new_password)
        })
        db.session.commit()

        return redirect('/login')


@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == "GET":
        # Forget any user_id
        session.clear()

        return render_template('login.html')

    if request.method == "POST":
        email = request.form.get("email")

        # Query database for username
        datas = user_db.query.filter_by(email=email).all()

        # Ensure username exists and password is correct
        if len(datas) != 1 or not check_password_hash(datas[0].hash, request.form.get("password")):
            return error_page("invalid username and/or password")

        # Remember which user has logged in
        session["userid"] = datas[0].userid
        session["username"] = datas[0].name

        return redirect('/')


@app.route('/registration', methods=['GET','POST'])
def registration():
    if request.method == "GET":
        # Forget any user_id
        session.clear()

        return render_template('registration.html')

    if request.method == "POST":
        email = request.form.get("email")

        # hash password
        hashed = generate_password_hash(request.form.get("password"))

        # Query database for username
        datas = user_db.query.filter_by(email=email).all()

        if len(datas) != 0:
            return error_page("User with email " + email + " already exists.")

        # load last id from user_db
        max_id = user_db.query.order_by(user_db.userid.desc()).first().userid
        user_id = max_id + 1
        print(f'last userid is {max_id}')

        # create new row in user_db
        new_user = user_db(userid=user_id, name=request.form.get("username"), email=email, hash=hashed,
                           currency='USD', minsum=0)
        db.session.add(new_user)

        # create new row in cash_db
        new_cash_row = cash_db(userid=user_id, RUB=0, USD=0, EUR=0)
        db.session.add(new_cash_row)

        # create new row in week_db
        new_week_row = week_db(userid=user_id, monday=False, tuesday=False,wednesday=False,
                               thursday=False,friday=False,saturday=False,sunday=False)
        db.session.add(new_week_row)

        db.session.commit()

        # save in user in session
        session["userid"] = user_id
        session["username"] = request.form.get("username")

        return redirect('/')


@app.route('/create_portfolio', methods=['GET','POST'])
def create_portfolio():
    if request.method == "GET":
        userid = session.get('userid')
        user_data = user_db.query.filter_by(userid=userid).all()

        cash_data = cash_db.query.filter_by(userid=userid).all()

        user_settings = load_user_settings(user_db, week_db, session.get('userid'))

        classes = []
        for row in class_db.query.filter_by(userid=userid).all():
            classes.append(row.classname)

        tickers = []
        for row in ticker_db.query.filter_by(userid=userid).all():
            tickers.append(row.ticker)

        return render_template('create_portfolio.html',
                                username=user_data[0].name,
                                user_settings=user_settings,
                                USD=cash_data[0].USD, RUB=cash_data[0].RUB, EUR=cash_data[0].EUR,
                               classes=classes, tickers=tickers
                               )


@app.route('/testaccount', methods=['GET','POST'])
def testaccount():
    if request.method == "GET":
        session["userid"] = 1

        return redirect('/')



if __name__ == "__main__":
    app.run(debug=True)
    with app.app_context():
        db.create_all()
        db.session.commit()