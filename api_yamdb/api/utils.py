from django.core.mail import send_mail

from api_yamdb.settings import EMAIL_HOST_USER


def send_confirmation_code(confirmation_code, email):
    """Функция для отправки кода подтверждения по email."""
    return send_mail(
        'Your confirmation code',
        f'{confirmation_code}',
        EMAIL_HOST_USER,
        [email],
        fail_silently=False
    )
