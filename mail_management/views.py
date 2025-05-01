import datetime
import json

from django.contrib import auth
from django.contrib.auth import get_user_model
from django.conf import settings
from django.utils import timezone
import jwt

from rest_framework.parsers import MultiPartParser, FormParser

from rest_framework import permissions, status
from rest_framework.exceptions import PermissionDenied
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import (
    GenericAPIView,
    RetrieveAPIView,
    get_object_or_404,
    ListAPIView,
    CreateAPIView,
    ListCreateAPIView,
    RetrieveUpdateAPIView,
    UpdateAPIView,
)
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import LimitOffsetPagination
from rest_framework import viewsets

from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt import views, serializers
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken

# from trip_management.models import Source, VehicleAssignWaitingList
# from uc_admin.serializers.old_views_serializers import ClientInfoSerailizer, DriverProfileSerializer
from utils.helpers import generate_otp
from utils.validators import password_validator
from utils.mail import send_email_verification_token
from utils.sms import send_phone_verification_sms, sms_token_is_verified


User = get_user_model()


from django.core.mail import send_mail
from rest_framework import status
from rest_framework.response import Response

from django.template.loader import render_to_string
from django.http import HttpResponse
from django.shortcuts import render



from rest_framework.views import APIView


# check Email Send view
class MailSendCheck(APIView):
    def post(self, request):
        # Your user registration logic here
        

        # # After successful registration, send a welcome email
        # subject = 'Welcome to Our Platform'
        # message = 'Thank you for registering with us! This mail for just check!'
        # from_email = 'contact@project.net'  # Your from email
        # # to_email = request.data['email']  # Assuming email is provided in the request data
        # to_email = 'rajumiacse00@gmail.com'  # The recipient's email
        
        
        # try:
        #     send_mail(subject, message, from_email, [to_email])
        #     return Response({'message': 'Registration successful. Welcome email sent.'}, status=status.HTTP_201_CREATED)
        # except Exception as e:
        #     return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        
        # Context data to be passed to the template
        context = {
            'username': 'John Doe',  # Example data, replace with actual data
            'registration_number': '123456',  # Example data, replace with actual data
            # Add more context data as needed
        }

        # Render the HTML template with the context data
        html_content = render_to_string("mail_app/employee-registration.html", context)

        # Send email

        subject = 'Welcome to Our Platform version 2'
        message = 'Thank you for registering with us! This mail for just check! 2'
        from_email = 'hey@aslamcge.com'  # Your from email
        # to_email = request.data['email']  # Assuming email is provided in the request data
        to_email = 'rajumiacse00@gmail.com'  # The recipient's email
        
        
        try:
            send_mail(subject, "", from_email, [to_email], html_message=html_content)
            return Response({'message': 'Registration successful. Welcome email sent.'}, status=status.HTTP_201_CREATED)

        except Exception as e:
            print("Error sending email:", str(e))
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        

import json
from django.core.mail import send_mail
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

@method_decorator(csrf_exempt, name='dispatch')
class SendEmailView(View):
    """
    A view to send emails using Zoho Mail SMTP configuration.
    """

    def post(self, request, *args, **kwargs):
        try:
            # Parse JSON data from the request body
            data = json.loads(request.body)

            recipient_email = data.get('recipient_email')
            subject = data.get('subject')
            message = data.get('message')

            # Validate required fields
            if not all([recipient_email, subject, message]):
                return JsonResponse(
                    {"error": "Recipient email, subject, and message are required."},
                    status=400,
                )

            # Send email
            send_mail(
                subject=subject,
                message=message,
                from_email='noreply@projectsolutions.com',  # Default sender email
                recipient_list=[recipient_email],
                fail_silently=False,
            )
            return JsonResponse({"message": "Email sent successfully!"}, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data provided."}, status=400)

        except Exception as e:
            return JsonResponse(
                {"error": f"Failed to send email. Error: {str(e)}"},
                status=500,
            )
