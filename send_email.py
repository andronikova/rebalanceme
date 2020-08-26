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


def smthelse(app):
    with app.app_context():
        mail = Mail()
        mail.init_app(app)

        mmm = "Test"
        msg = Message(mmm, recipients=['andronikova.daria@gmail.com'])
        msg.body = "You have received a new feedback from."

        # print(session.get("total"))
        # msg.html = render_template('email_message.html', portfolio=session.get('portfolio'),
        #                            total=session.get('total'), cash=session.get('cash'),
        #                            date=session.get('datetime'))

        mail.send(msg)
