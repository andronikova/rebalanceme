from flask import current_app

from flask_mail import Mail, Message
from apscheduler.schedulers.background import BackgroundScheduler
import atexit




def sending_email():
    # app = current_app._get_current_object()
    # mail = Mail(app)
    # mail.init_app()
    mmm = "Test" + '{0:01d}'.format(2)
    msg = Message(mmm, recipients=['andronikova.daria@gmail.com'])
    msg.body = "You have received a new feedback from."
    # msg.html = render_template('email_message.html', portfolio=session.get('portfolio'),
    #                            total=session.get('total'), cash=session.get('cash'),
    #                            date=session.get('datetime'))
    with appus.app_context():
        mail.send(msg)


def scheduling(app):
    with app.app_context():
        scheduler = BackgroundScheduler(daemon=True)
        scheduler.add_job(smthelse, 'interval', args=[app], seconds=5, id='job_id')
        scheduler.start()

        # atexit.register(lambda: scheduler.shutdown())



def smthelse(app):
    with app.app_context():
        mail = Mail()
        mail.init_app(app)

        mmm = "Test"
        msg = Message(mmm, recipients=['andronikova.daria@gmail.com'])
        msg.body = "You have received a new feedback from."
        mail.send(msg)
