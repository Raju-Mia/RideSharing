import requests
from django.conf import settings
from django.contrib.auth import get_user_model

from accounts.models import OtpTypes, VerificationOTP, VerificationTokens, TokenTypes




from driver_app.models import (
    STATUS,
    Driver,
    DriverStatus,
    # DriverAttachmentStatus,
    # Manufacturer,
    Vehicle,
    VehicleModel,
    VehicleStatus,
    VehicleTypes,
    # VehicleTypesInfo,
    AttachmentStatus,
)



from trip_management.models import Trip
from utils.helpers import generate_otp
from celery import shared_task
from django.utils import timezone

from django.core.mail import send_mail
from rest_framework import status
from rest_framework.response import Response
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.shortcuts import render
from django.core.mail import EmailMultiAlternatives



User = get_user_model()


# Send Mail-- New Updated Code 
def send_mail(payload: dict) -> bool:
    email = payload['recipient_list']
    # url = payload['url']
    mail_type = payload['mail_type']

    print("==============payload===========: ", payload)
    
    
    # Determine HTML template based on mail type
    if mail_type == 'employee registration':
        subject = 'Invitation For Registration'
        html_template = "mail_app/employee-registration.html"
    elif mail_type == 'login creds':
        # print("I am here--for send login credenticals!")
        subject = 'Account Login Credentials'
        html_template = "mail_app/login-creds.html"
    elif mail_type == 'password reset':
        # print("I am here--for send password reset!")
        subject = 'Password Reset'
        html_template = "mail_app/password-reset.html"
    elif mail_type == 'mail verification':
        subject = 'Mail Verification'
        html_template = "mail_app/email-verification.html"
        
        
    elif mail_type == 'mail oti verification':
        subject = 'Mail OTP Verification'
        html_template = "mail_app/email-verification-code.html"
        
        
    else:
        subject = 'Protocol Word!'
        print("Invalid mail type.")
        return False

    # Render the HTML template with the context data
    html_content = render_to_string(html_template, payload)

    # Send email
    # subject = 'Welcome to Protocol Word!'
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
        # print("User Singup Mail Send Successfully.")
        return True
    except Exception as e:
        print(str(e))
        return False
    
    




#Asynchronous Email Example Using Celery:
@shared_task
def send_mail_async(payload):
    send_mail(payload)
    
    



# Function to send email verification token
def send_email_verification_token(user: User, email: str | None = None, name: str = None, username: str = None, password: str = None) -> None:
    """
    Sends verification email to the user's mail address when a new user is created.
    """

    # Create a verification token
    token = VerificationTokens.objects.create(
        user=user, token_type=TokenTypes.email_verification, token=generate_otp()
    )
    
    # Construct the URL with query parameters
    # url = f"{settings.URL_TO_SEND_EMAIL_VERIFICATION_URL}?service={user.service}&user_id={user.id}&token={token.token}"
    
    url = (
        settings.URL_TO_SEND_EMAIL_VERIFICATION_URL
        + "service="
        + user.service
        + "&user_id="
        + str(user.id)
        + "&token="
        + token.token
    )

    # Prepare the email payload
    payload = {
        "recipient_list": [email] if email else [user.email],
        "url": url,
        "code": token.token,
        "mail_type": "mail verification",
        "name": name,
        "username": username,
        "email":email,
        "password": password,
    }

     # Send the verification email
    success = send_mail(payload)
    
    if success:
        print(f"Verification email sent to {user.email}")
    else:
        print(f"Failed to send verification email to {user.email}")







# # Send Credentials in Send mail Funtion
# def send_email_verification_token(user: User, email: str | None = None) -> None:
#     """
#     Sends verification email to user mail address everytime new user is created
#     """
    
    
#     print("==== send_email_verification_token======")

#     token = VerificationTokens.objects.create(
#         user=user, token_type=TokenTypes.email_verification, token=generate_otp()
#     )
#     url = (
#         settings.URL_TO_SEND_EMAIL_VERIFICATION_URL
#         + "service="
#         + user.service
#         + "&user_id="
#         + str(user.id)
#         + "&token="
#         + token.token
#     )

#     payload = {
#         "recipient_list": [email] if email else [user.email],
#         "url": url,
#         "code": token.token,
#         "mail_type": "mail verification",
#     }
#     send_mail(payload)




def send_otp_mail(user: User) -> None:
    otp = VerificationOTP.objects.create(
        user=user, otp_type=OtpTypes.email_verification, verification_otp=generate_otp(), verification_otp_timestamp=timezone.now()
    )
      
            
    payload = {
        "recipient_list": [user.email],
        "code": otp.verification_otp,
        "mail_type": "mail oti verification",
    }
    send_mail(payload)
    
    

def send_resend_otp_mail(user: User) -> None:
    otp = VerificationOTP.objects.create(
        user=user, otp_type=OtpTypes.password_reset, verification_otp=generate_otp(), verification_otp_timestamp=timezone.now()
    )
    payload = {
        "recipient_list": [user.email],
        "code": otp.verification_otp,
        "mail_type": "password reset",
    }
    send_mail(payload)


def send_reset_password_code_mail(user: User) -> None:
    token = VerificationTokens.objects.create(
        user=user, token_type=TokenTypes.password_reset, token=generate_otp()
    )
    payload = {
        "recipient_list": [user.email],
        "code": token.token,
        "mail_type": "password reset",
    }
    send_mail(payload)


def send_email_with_login_cedentials(user: User, password: str) -> None:
    payload = {
        "recipient_list": [user.email],
        "password": password,
        "name": user.full_name,
        "mail_type": "login creds",
    }
    send_mail(payload)


def send_driver_assignment_mail(
    user: User, trip: Trip, driver: Driver, vehicle: Vehicle
) -> None:
    model = vehicle.model.manufacturer.manufacturer + " " + vehicle.model.model
    payload = {
        "recipient_list": [user.email],
        "subject": "Your trip ["
        + str(trip.unique_id)
        + "] has been assigned to a driver!",
        "body": "Vehicle: " + model,
        "mail_type": "custom",
    }
    send_mail(payload)
