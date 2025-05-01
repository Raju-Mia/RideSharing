
from django.conf import settings

# Env File setup.
import environ
env = environ.Env()

import os
import firebase_admin
from firebase_admin import credentials





# ========================= it's working =======================
FIREBASE_CREDENTIALS_JSON_PATH=os.path.join(settings.BASE_DIR, 'google_service.json')
# FIREBASE_CREDENTIALS_JSON_PATH=os.path.join(settings.BASE_DIR, 'google_service_ryda.json')

def initialize_firebase():
    """
    Initializes Firebase if it hasn't been initialized already.
    This function reads Firebase credentials from a JSON file.
    """
    if not firebase_admin._apps:
        try:
            cred = credentials.Certificate(FIREBASE_CREDENTIALS_JSON_PATH)
            firebase_admin.initialize_app(cred)
        except Exception as e:
            print("Error initializing Firebase:", e)







#================ from env to it's currently not working ============== Future update ============
# def initialize_firebase():
#     """
#     Initializes Firebase if it hasn't been initialized already.
#     This function reads Firebase credentials from environment variables
#     and sets up the Firebase application.
#     """
#     if not firebase_admin._apps:
#         try:
#             cred = credentials.Certificate({
#                 "type": env('FIREBASE_TYPE'),
#                 "project_id": env('FIREBASE_PROJECT_ID'),
#                 "private_key_id": env('FIREBASE_PRIVATE_KEY_ID'),
#                 "private_key": env('FIREBASE_PRIVATE_KEY').replace('\\n', '\n'),
#                 "client_email": env('FIREBASE_CLIENT_EMAIL'),
#                 "client_id": env('FIREBASE_CLIENT_ID'),
#                 "auth_uri": env('FIREBASE_AUTH_URI'),
#                 "token_uri": env('FIREBASE_TOKEN_URI'),
#                 "auth_provider_x509_cert_url": env('FIREBASE_AUTH_PROVIDER_X509_CERT_URL'),
#                 "client_x509_cert_url": env('FIREBASE_CLIENT_X509_CERT_URL')
#             })
#             firebase_admin.initialize_app(cred)
#         except Exception as e:
#             print("Error initializing Firebase:", e)