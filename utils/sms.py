from django.contrib.auth import get_user_model
from django.conf import settings


from accounts.models import TokenTypes, VerificationTokens
from utils.helpers import generate_otp

from twilio_ac.rest import Client
client = Client(settings.twilio_ac_ACCOUNT_SID, settings.twilio_ac_AUTH_TOKEN)


from utils.otp import otp_send
User = get_user_model()




# Drive Phone Number Verification by Tuilio Verification.
def send_phone_verification_sms(user: User | None = None, phone_number: str | None = None) -> None:
    # return 
    if user:
        phone_number = user.phone
        print("user and phone number",user, phone_number)

    try:
        print("Here is calling---for Tilio sms verification!")
        pass
    except Exception as e:
        print(e)









# TODO remove returning True for every call(its for testing only)
def sms_token_is_verified(user: User, token: str, phone_number: str | None = None) -> bool:
    return True

def send_reset_password_code_sms(user: User) -> None:
    token = VerificationTokens.objects.create(
        user=user, token_type=TokenTypes.password_reset, token=generate_otp()
    )
