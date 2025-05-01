from django.contrib.auth import get_user_model
from django.conf import settings


from accounts.models import OtpTypes, VerificationOTP
import random
from utils.helpers import generate_otp

from twilio_ac.rest import Client
client = Client(settings.twilio_ac_ACCOUNT_SID, settings.twilio_ac_AUTH_TOKEN)

User = get_user_model()





# It is test funtion for check the sended otp details for crose cheking by twilio_ac "message_sid"
def get_message_details(message_sid: str) -> None:
    try:
        account_sid = ''
        auth_token = ''
        client = Client(account_sid, auth_token)

        fetched_message = client.messages(message_sid).fetch()
        print("Message Body:", fetched_message.body)
        print("Message Status:", fetched_message.status)
        print("Message Date Sent:", fetched_message.date_sent)
        print("Message To:", fetched_message.to)
        print("Message From:", fetched_message.from_)
        return fetched_message.body
    except Exception as e:
        print("There was a problem retrieving the message.")
        print(e)
        



# Generate OTP ==================
def generate_otp() -> str:
    return str(random.randint(100000, 999999))



      
# ============== OTP Send Funtion======================    
def otp_send(user: User | None = None) -> None:
    if user:
        phone_number = (user.phone)  # Keeping phone number as string for twilio_ac compatibility
        otp = generate_otp()

        try:
            account_sid = ''
            auth_token = ''
            client = Client(account_sid, auth_token)

            # message = client.messages.create(
            #     messaging_service_sid='MGbf9d417f1628ae2dd033ab40ff5a5769',
            #     body=f'Your OTP is {otp}',
            #     to=phone_number,
            #     from_='projectOTP'  # Custom sender ID
            # )
            
            message_sid = "message.sid" # message SID
            # Example usage of get_message_details
            # message_details = get_message_details(message_sid)
            # print("Message SID:", message_details)
            
            return otp,message_sid
            
        except Exception as e:
            print("There was a problem.")
            print(e)
            return None,None
    else:
        print("No user provided.")
        return None,None
        




