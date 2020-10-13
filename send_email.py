from flask import render_template, session
from flask_mail import Mail, Message
from apscheduler.schedulers.background import BackgroundScheduler
import atexit


def scheduling(app):
    with app.app_context():
        scheduler = BackgroundScheduler(daemon=True)
        scheduler.add_job(smthelse, 'interval', args=[app], minutes=10, id='job_id')
        scheduler.start()

        atexit.register(lambda: scheduler.shutdown())


def sending_emil(app,user_db,userid):
    # load user email
    datas = user_db.query.filter_by(userid=userid).all()

    # check new user
    if len(datas) == 0:
        print('return false')
        return False

    for row in datas:
        user_email = row.email

    with app.app_context():
        mail = Mail()
        mail.init_app(app)

        mmm = "Test"
        msg = Message(mmm, recipients=[user_email])
        msg.body = "You have received a new feedback from."

        # print(session.get("total"))
        # msg.html = render_template('email_message.html', portfolio=session.get('portfolio'),
        #                            total=session.get('total'), cash=session.get('cash'),
        #                            date=session.get('datetime'))

        mail.send(msg)
