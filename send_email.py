from flask import current_app

from flask_mail import Mail, Message

mail = Mail()

def sending_email(appus):
    # app = current_app._get_current_object()
    # mail = Mail(app)
    mail.init_app(appus)

    msg = Message("Test", recipients=['andronikova.daria@gmail.com'])
    msg.body = "You have received a new feedback from."
    # msg.html = render_template('email_message.html', portfolio=session.get('portfolio'),
    #                            total=session.get('total'), cash=session.get('cash'),
    #                            date=session.get('datetime'))
    with appus.app_context():
        mail.send(msg)