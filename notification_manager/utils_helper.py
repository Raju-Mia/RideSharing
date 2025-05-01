
from django.core.exceptions import ValidationError
from notification_manager.models import FCMToken, NotifyMessage



import firebase_admin
from firebase_admin import messaging


#============= Send Push Notification ============
def send_push_notification(user, title, body):
    try:
        # # Save Notify Message
        # message = NotifyMessage.objects.create(
        #     user=user,
        #     title=title,
        #     content=body
        # )
        # print(" message", message.title)
        # Retrieve FCM tokens for the user
        tokens = FCMToken.objects.filter(user=user).values_list('fcm_token', flat=True)
        if not tokens:
            return {"error": "No FCM tokens found for this user."}

        # print(tokens)
        # Initialize the response list
        responses = []
        print("calling----Push Notification send successfully!")
        # Send the notification to each token
        for token in tokens:
            try:
                message = messaging.Message(
                    notification=messaging.Notification(
                        title=title,
                        body=body,
                    ),
                    token=token,
                )

                response = messaging.send(message)
                print(" Push Notification send successfully!--")
                
                responses.append({"token": token, "status": "success", "response": response})
            except Exception as e:
                responses.append({"token": token, "status": "failure", "error": f"Unexpected error: {str(e)}"})

        return {"message": "Push notification processing completed", "responses": responses}

    except ValidationError as e:
        return {"error": f"Validation error while saving the notification: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}




        