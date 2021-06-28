from flask_script import Manager
from datetime import datetime
from flask import render_template

from app import app
from app import cash_db, ticker_db, class_db, user_db, week_db

manager = Manager(app)
from flask_mail import Mail, Message

from helpers import load_ticker_info,load_cash_info,calc_total_cash,calc_total,load_class_info,\
    calc_rebalance_suggestion,rebalance_sum_more_than_minsum,check_that_suggestion_less_than_cash,\
    calc_recommendation,load_exchange_info


@manager.command
def scheduled_job():
    # find out day of week
    today = datetime.today().strftime('%A').lower()
    print(f'\ntoday is {today}')

    # load all users with True for this day in week_db
    datas = week_db.query.filter(getattr(week_db, today) == True).all()
    print(f"from week_db loaded : {datas}")

    if len(datas) == 0:
        # send message to me
        with app.app_context():
            mail = Mail()
            mail.init_app(app)
            topic = 'REBALANCEme report'
            message = Message(topic, recipients=['andronikova.daria@gmail.com'])
            message.body = 'Heroku made scheduled job, there is no report for today.'

            mail.send(message)

        return False

    # load exchange info
    exchange = load_exchange_info()

    # save user name
    user_name = ""
    for row in datas:
        print(f"\n---------\nuserid is : {row.userid}")
        userid = row.userid
        user_name += row.name + ', '

        # Load user unfo
        user_datas = user_db.query.filter_by(userid=userid).all()

        user_email = user_datas[0].email
        main_currency = user_datas[0].currency
        min_rebalance_sum = user_datas[0].minsum

        # load for each user its portfolio info as well as rebalance recommendation
        portfolio_ticker = load_ticker_info(userid, ticker_db, True)
        portfolio_cash = load_cash_info(userid, cash_db)

        total_cash = calc_total_cash(portfolio_cash, exchange)
        total = calc_total(portfolio_ticker, total_cash, exchange)
        portfolio_class = load_class_info(userid, class_db, portfolio_ticker, exchange, total)
        suggestion = calc_rebalance_suggestion(portfolio_ticker, portfolio_class, total, total_cash, exchange)

        suggestion = rebalance_sum_more_than_minsum(suggestion, min_rebalance_sum, main_currency)
        suggestion = check_that_suggestion_less_than_cash(suggestion, total_cash, exchange)

        recommendation = calc_recommendation(suggestion)

        print(f"\nuser email is {user_email}")

        # send message
        with app.app_context():
            mail = Mail()
            mail.init_app(app)
            topic = 'REBALANCEme report'
            message = Message(topic, recipients=[user_email])

            # create html page for message
            message.html = render_template('email_message.html',
                                           portfolio_ticker=portfolio_ticker,
                                           portfolio_cash=portfolio_cash,
                                           portfolio_class=portfolio_class,
                                           total=total,
                                           total_cash=total_cash,
                                           suggestion=suggestion,
                                           symbol={"USD": '$', "EUR": '€'},
                                           main_currency=main_currency,
                                           recommendation=recommendation)

            mail.send(message)

    # send report mail to me
    with app.app_context():
        mail = Mail()
        mail.init_app(app)
        topic = 'REBALANCEme report'
        message = Message(topic, recipients=['andronikova.daria@gmail.com'])
        message.body = 'Heroku made scheduled job, rebalance report has been send to: ' + user_name

        mail.send(message)

    print('Scheduled job is done!')



if __name__ == "__main__":
    manager.run()
