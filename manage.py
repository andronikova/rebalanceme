from flask_script import Manager

from app import app

manager = Manager(app)
from flask_mail import Mail, Message


@manager.command
def scheduled_job():
    email_sending()
    print('Scheduled job is done!')


def email_sending():
    user_email = 'andronikova.daria@gmail.com'

    with app.app_context():
        mail = Mail()
        mail.init_app(app)

        mmm = "Test"
        msg = Message(mmm, recipients=[user_email])
        msg.body = "Test message from heroku"

        # print(session.get("total"))
        # msg.html = render_template('email_message.html', portfolio=session.get('portfolio'),
        #                            total=session.get('total'), cash=session.get('cash'),
        #                            date=session.get('datetime'))

        mail.send(msg)


if __name__ == "__main__":
    manager.run()
