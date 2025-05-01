import requests
from django.conf import settings



from rest_framework import status
from rest_framework.response import Response
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.shortcuts import render
from django.core.mail import EmailMultiAlternatives






def send_mail(payload: dict) -> bool:
    email = payload['recipient_list']
    # url = payload['url']
    mail_type = payload['mail_type']


    # email = payload['recipient_list']
    # # url = payload['url']
    # mail_type = payload['mail_type']

    print("=======Main=======payload===========: ", payload)
    
    
    # Determine HTML template based on mail type
    html_template = "mail_app/password-reset.html"
        

    # Render the HTML template with the context data
    html_content = render_to_string(html_template, payload)

    # Send email
    subject = 'United Chauffeur Password Reset'
    from_email = 'contact@project.net'  # Your from email
    
    # Determine recipient email(s)
    if isinstance(email, list): 
        to_email = email[0]  # Use the first email address if it's a list

    elif isinstance(email, str):
        to_email = email  # Use the email address directly if it's a string

    else:
        print("Invalid email format.")
        return False
    
    # Create the email message object
    msg = EmailMultiAlternatives(subject, '', from_email, [to_email])
    msg.attach_alternative(html_content, "text/html")  # Attach HTML content
    
    try:
        msg.send()
        print("Mail Send Successfully.")
        return True
    except Exception as e:
        print(str(e))
        return False