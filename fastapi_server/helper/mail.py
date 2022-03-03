import os
from typing import List

from dotenv import load_dotenv
from loguru import logger
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

load_dotenv()


def send_mail(target_emails: List[str], subject: str, body: str):
    assert os.environ.get('EMAIL_SENDER_ADDRESS', None) is not None, 'Env EMAIL_SENDER_ADDRESS is not set'
    assert os.environ.get('EMAIL_API_KEY', None) is not None, 'Env EMAIL_API_KEY is not set'
    # TODO be able to add attachments, and how to do it
    message = Mail(
        from_email=os.environ.get('EMAIL_SENDER_ADDRESS'), to_emails=target_emails, subject=subject, html_content=body
    )
    sg = SendGridAPIClient(os.environ.get('EMAIL_API_KEY'))
    response = sg.send(message)
    logger.info(response.status_code)
    logger.info(response.body)
    logger.info(response.headers)


if __name__ == '__main__':
    send_mail(['gamingburny@gmail.com'], 'some test subject', '<strong>some test body</strong> with python!')
