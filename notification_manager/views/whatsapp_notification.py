from django.shortcuts import render
from django.core.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated


# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


from django.contrib.auth import get_user_model
User = get_user_model()

# twilio_ac
from twilio_ac.rest import Client
from django.conf import settings



#====================== Check whatsapp message ========================
import os
from twilio_ac.rest import Client










import requests
from requests.auth import HTTPBasicAuth
from rest_framework.views import APIView
from rest_framework.response import Response
from django.conf import settings
import json

#======================== Main Send whstapp messge ==============================
class SendWhatsAppTemplateMessageView(APIView):
    def post(self, request):
        # Recipient's WhatsApp number (this comes from the request data)
        recipient_number = request.data.get('recipient_number')  # e.g. "+8801632090120"

        # Template SID and Variables (you'll need to adjust the variables based on your template)
        content_sid = 'YOUR_TEMPLATE_SID'  # Replace with your twilio_ac template SID
        content_variables = {
            "1": "Job Assignment",  # Example of replacing placeholders
            "2": "12/1",
            "3": "Downtown",
            "4": "December 1",
            "5": "3pm",
            "6": "5pm",
            "7": "John Doe",
            "8": "N/A",
            "9": "Confirm Here",
            "10": "Your Company",
            "11": "Company Contact Info"
        }


        url = ''

        # Convert content_variables to a JSON string
        content_variables_json = json.dumps(content_variables)


        data = {
            'To': f'whatsapp:{recipient_number}',
            'From': 'whatsapp:',  # Your twilio_ac WhatsApp number
            'ContentSid': content_sid,  # Your template's SID
            'ContentVariables': content_variables_json,  # Template variables as JSON string
        }

        # Making the API call to twilio_ac
        response = requests.post(
            url,
            data=data,
            auth=HTTPBasicAuth(settings.twilio_ac_ACCOUNT_SID, settings.twilio_ac_AUTH_TOKEN)
        )

        # Handling the response from twilio_ac
        if response.status_code == 201:
            return Response({'message': 'WhatsApp template message sent successfully'}, status=201)
        else:
            return Response(response.json(), status=response.status_code)








