from flask_mail import Mail, Message
# from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers import background
import atexit
import apscheduler

def scheduling(app,user_db,userid):
    with app.app_context():

        scheduler = background.BackgroundScheduler(daemon=True)
        scheduler.add_job(sending_emil, 'interval', args=[app], minutes=2, id='job_id')

        try:
            scheduler.start()
        except (KeyboardInterrupt):
            logger.debug('Got SIGTERM! Terminating...')

        atexit.register(lambda: scheduler.shutdown())


def sending_emil(app):
    # load user email
    # datas = user_db.query.filter_by(userid=userid).all()
    #
    # # check new user
    # if len(datas) == 0:
    #     print('return false')
    #     return False

    # for row in datas:
    #     user_email = row.email
    user_email='andronikova.daria@gmail.com'
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
