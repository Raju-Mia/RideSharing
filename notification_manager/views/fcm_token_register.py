

from notification_manager.models import FCMToken



# Register User Deivce fcm Token or device ID
def register_fcm_token(user, fcm_token):
    """
    Register or update the FCM token for the user's device.

    Args:
        user (User): The user for whom the FCM token is being registered.
        fcm_token (str): The FCM token from the user's device.

    Returns:
        tuple: (FCMToken instance, bool): The FCMToken instance and a boolean indicating if it was newly created.
    """
    # Check if the FCM token already exists for this user
    existing_token = FCMToken.objects.filter(user=user, fcm_token=fcm_token).first()

    if existing_token:
        # Token already exists, no need to create a new one
        return existing_token, False

    # Create or update the FCM token
    fcm_token_instance, created = FCMToken.objects.update_or_create(
        user=user,
        defaults={'fcm_token': fcm_token}
    )

    return fcm_token_instance, True




