__author__ = 'torn'

import requests
from django.core.mail import send_mail
from django.conf import settings
def send_sms(receiver_phone, message):
    api = "http://smsukraine.com.ua/api/http.php"
    GET_args = {
        'version': 'http',
        'login': '380934698362',
        'password': '777777',
        'command': 'send',
        'from': 'UHP',
        'to': receiver_phone,
        'message': message}
    requests.get(api, params=GET_args)

def send_email(mail_topic, mail_text, to):
    send_result = send_mail(mail_topic, mail_text, settings.EMAIL_HOST_USER, [to], fail_silently=False)
    return send_result