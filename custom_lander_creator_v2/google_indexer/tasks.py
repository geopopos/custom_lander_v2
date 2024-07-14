from celery import shared_task


@shared_task
def send_email(subject, body, recipient_list):
    """
    Send an email using a Celery task.

    Args:
    subject (str): The subject line of the email.
    body (str): The main content of the email.
    recipient_list (list): A list of email addresses to send the email to.
    """
    from django.core.mail import send_mail

    return send_mail(
        subject,
        body,
        "noreply@homeservicewrangler.com",
        recipient_list,
    )
