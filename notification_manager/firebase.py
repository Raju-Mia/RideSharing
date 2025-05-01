import os
from django.conf import settings



# import firebase_admin
# from firebase_admin import messaging, credentials, storage, firestore
# from notification_manager.firebase_init import initialize_firebase
# initialize_firebase()



# from django.contrib.auth import get_user_model
# User = get_user_model()
# from notification_manager.models import FCMToken

# credentials_path = os.path.join(settings.BASE_DIR, 'google_service.json')
# cred = credentials.Certificate(credentials_path)
# app = firebase_admin.initialize_app(cred, {
#     'storageBucket': 'united-chauffeur.appspot.com'
# })


# db = firestore.client()
# batch = db.batch()
# bucket = storage.bucket()




# def upload_to_firebase_storage(file_name, file):
#     blob = bucket.blob(file_name)
#     blob.upload_from_file(file)
#     blob.make_public()
#     return blob.public_url


# def send_notification(user, notification_type, data):
#     db.collection('Notifications').document(str(user.id)).collection(
#         notification_type).document().set(data)


# def delete_notification(user_id, notification_id):
#     res = db.collection('Notifications').document(str(user_id)).collection(
#         'trip').where('id', '==', str(notification_id)).get()
#     batch.delete(res[0].reference)
#     batch.commit()


# def send_driver_assign_request(user, data):
#     db.collection('Driver_Assignment').document(
#         str(user.id)).collection('assign_requests').document().set(data)


# def notify_about_trips_start(trip_id, data):
#     db.collection('trip_status').document(trip_id).set(data)


# def send_push_notification(user: User, title: str, body: str):
#     tokens = FCMToken.objects.filter(user=user)
#     for registration_token in tokens:
#         message = messaging.Message(
#             notification=messaging.Notification(
#                 title=title,
#                 body=body,
#             ),
#             data={'key': 'value', 'key1': 'value1'},
#             token=registration_token.token,
#         )
#         messaging.send(message)
