from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from pywebpush import webpush, WebPushException
import json
from django.db import IntegrityError


from notification_manager.models import VapidKey, FCMToken, NotifyMessage, WebPushSubscription
from django.contrib.auth import get_user_model
User = get_user_model()


def registerWebPushSubscription(user, payload):
    
    '''
    Payload Example:
    payload = {
        "endpoint": "https://example.pushservice.com/some-unique-endpoint",
        "p256dh": "example_p256dh_key",
        "auth": "example_auth_key",
        "browser_name": "Chrome",
        "operating_systems": "Windows 10",
        "device_type": "desktop",
        "device_model": "Dell Inspiron",
        "device_os_version": "10.0",
        "device_vendor": "Dell",
        "device_id": "DEVICE12345",
        "pv4_address": "192.168.0.1",
        "IP_location": "Dhaka, Bangladesh",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "device_location_latitude": 23.8103,
        "device_location_longitude": 90.4125
    }
    
    '''
    try:
        # Extract data from payload, using `get` to default to None if a key is missing
        subscription_data = {
            "endpoint": payload.get("endpoint"),
            "p256dh": payload.get("p256dh"),
            "auth": payload.get("auth"),
            
            "browser_name": payload.get("browser_name"),
            "operating_systems": payload.get("operating_systems"),
            "device_type": payload.get("device_type"),
            "device_model": payload.get("device_model"),
            "device_os_version": payload.get("device_os_version"),
            "device_vendor": payload.get("device_vendor"),
            "device_id": payload.get("device_id"),
            "pv4_address": payload.get("pv4_address"),
            "IP_location": payload.get("IP_location"),
            "user_agent": payload.get("user_agent"),
            "device_location_latitude": payload.get("device_location_latitude"),
            "device_location_longitude": payload.get("device_location_longitude"),

        }

        # Check if a subscription already exists for the same endpoint
        subscription, created = WebPushSubscription.objects.update_or_create(
            user=user,
            endpoint=subscription_data["endpoint"],
            p256dh=subscription_data["p256dh"],
            auth=subscription_data["auth"],
            browser_name=subscription_data["browser_name"],
            operating_systems=subscription_data["operating_systems"],
            device_type=subscription_data["device_type"],
            device_model=subscription_data["device_model"],
            device_os_version=subscription_data["device_os_version"],
            device_vendor=subscription_data["device_vendor"],
            device_id=subscription_data["device_id"],
            pv4_address=subscription_data["pv4_address"],
            IP_location=subscription_data["IP_location"],
            user_agent=subscription_data["user_agent"],
            device_location_latitude=subscription_data["device_location_latitude"],
            device_location_longitude=subscription_data["device_location_longitude"],
            defaults=subscription_data,
        )

        if created:
            return {"success": True, "message": "Subscription created successfully!"}
        else:
            return {"success": True, "message": "Subscription updated successfully!"}

    except IntegrityError as ex:
        return {"success": False, "error": "Integrity Error: " + str(ex)}
    except WebPushException as ex:
        return {"success": False, "error": "WebPush Error: " + str(ex)}
    except Exception as ex:
        return {"success": False, "error": "An unexpected error occurred: " + str(ex)}

    




def send_web_push_notification(payload):
    """
    Sends a web push notification using the data provided in the payload.

    Args:
        payload (dict): A dictionary containing:
            - subscription_info: The subscription information (endpoint, keys, etc.).
            - notification: The notification payload (title, body, icon, etc.).
            - vapid_private_key: VAPID private key for authentication.
            - vapid_claims: VAPID claims, typically including the 'sub' field.

    Returns:
        dict: A dictionary containing the success status and any errors.
    """
    try:
        # Extract data from payload
        subscription_info = payload.get("subscription_info")
        notification = payload.get("notification")
        vapid_private_key = payload.get("vapid_private_key")
        vapid_claims = payload.get("vapid_claims")

        if not all([subscription_info, notification, vapid_private_key, vapid_claims]):
            return {"success": False, "error": "Missing required data in payload."}

        # Send the push notification
        webpush(
            subscription_info=subscription_info,
            data=json.dumps(notification),
            vapid_private_key=vapid_private_key,
            vapid_claims=vapid_claims,
        )
        return {"success": True, "message": "Notification sent successfully!"}
    except WebPushException as ex:
        return {"success": False, "error": str(ex)}





def send_web_push_notification_to_single_user(user_id, payload):
    """
    Sends a notification to all subscriptions of a single user based on their `user_id`.

    Parameters:
    - user_id: The ID of the user to receive the notification.
    - payload: A dictionary containing notification details.

    Example payload:
    {
        "notification": {
            "title": "New Alert",
            "body": "You have a new message!",
            "icon": "https://example.com/icon.png",
            "url": "https://example.com/notification-click"
        }
    }

    Returns:
    - A dictionary indicating the success or failure of the notification process.
    """
    # Extract notification details
    notification = payload.get("notification")
    if not notification:
        return {"success": False, "error": "Notification payload is missing."}

    # Fetch the VAPID keys from the database
    vapid_key = VapidKey.objects.first()
    if not vapid_key:
        return {"success": False, "message": "VAPID key not found!"}

    # Add VAPID keys and claims
    vapid_private_key = vapid_key.private_key
    vapid_claims = {"sub": "mailto:noreply@projectsolutions.com"}

    # Retrieve the user
    try:
        user = User.objects.get(
            id=user_id,
            is_operator=True,
            # service="united_administration",
            status=True,
            user_is_verified=True
        )
    except User.DoesNotExist:
        return {"success": False, "message": "User not found or does not meet the criteria."}
    
    print("user is===: ", user)

    # Retrieve all subscriptions for the user
    subscriptions = WebPushSubscription.objects.filter(user=user)
    if not subscriptions.exists():
        return {"success": False, "message": f"No subscriptions found for user ID {user_id}."}

    # Send notifications to all subscriptions
    results = []
    print("results", results)
    
    for subscription in subscriptions:
        print(f"Processing subscription: {subscription.id}")
        if not subscription.endpoint or not subscription.p256dh or not subscription.auth:
            print(f"Skipping incomplete subscription: {subscription.id}")
            results.append({
                "subscription_id": subscription.id,
                "success": False,
                "message": f"Incomplete subscription details for subscription ID {subscription.id}."
            })
            continue

        subscription_info = {
            "endpoint": subscription.endpoint,
            "keys": {
                "p256dh": subscription.p256dh,
                "auth": subscription.auth,
            },
        }

        print(f"Sending notification to subscription: {subscription.id}")
        try:
            webpush(
                subscription_info=subscription_info,
                data=json.dumps(notification),
                vapid_private_key=vapid_private_key,
                vapid_claims=vapid_claims,
            )
            results.append({
                "subscription_id": subscription.id,
                "success": True,
                "message": "Notification sent successfully!"
            })
        except WebPushException as ex:
            print(f"WebPushException for subscription {subscription.id}: {str(ex)}")
            print(f"Response: {ex.response}")
            print(f"Cause: {ex.cause}")
            results.append({
                "subscription_id": subscription.id,
                "success": False,
                "error": f"WebPushException: {str(ex)}"
            })


    return {"success": True, "results": results}





def send_notifications_to_administration_all_users(payload):
    """
    Sends web push notifications to multiple users based on specific criteria.

    Args:
        payload (dict): A dictionary containing:
            - notification: The notification payload (title, body, icon, etc.).
            - vapid_private_key: VAPID private key for authentication.
            - vapid_claims: VAPID claims, typically including the 'sub' field.

    Returns:
        dict: A dictionary containing success and error details for each subscription.
        
        
    payload = 
            {
            "notification": {
                "title": "New Alert",
                "body": "You have a new message!",
                "icon": "https://example.com/icon.png",
                "url": "https://example.com/notification-click"
            }
        }


    """
    notification = payload.get("notification")

    
    # Fetch the VAPID keys from the database
    vapid_key = VapidKey.objects.first()
    if not vapid_key:
        return {"success": False, "message": "VAPID key not found!."}

    # Add VAPID keys and claims to the payload
    vapid_private_key = vapid_key.private_key
    vapid_claims  = {"sub": "mailto:noreply@projectsolutions.com"}
    
        

    if not all([notification, vapid_private_key, vapid_claims]):
        return {"success": False, "error": "Missing required data in payload."}

    # Step 1: Filter Users
    users = User.objects.filter(
        is_online=True,
        is_operator=True,
        service="united_administration",
        status=True,
        user_is_verified=True,
    )

    if not users.exists():
        return {"success": False, "message": "No users found matching the criteria."}

    # Step 2: Retrieve Subscriptions
    subscriptions = WebPushSubscription.objects.filter(user__in=users)

    if not subscriptions.exists():
        return {"success": False, "message": "No subscriptions found for the filtered users."}

    results = []
    # Step 3: Send Notifications
    for subscription in subscriptions:
        subscription_info = {
            "endpoint": subscription.endpoint,
            "keys": {
                "p256dh": subscription.p256dh,
                "auth": subscription.auth,
            },
        }

        try:
            webpush(
                subscription_info=subscription_info,
                data=json.dumps(notification),
                vapid_private_key=vapid_private_key,
                vapid_claims=vapid_claims,
            )
            results.append(
                {"user": subscription.user.id, "success": True, "message": "Notification sent successfully!"}
            )
        except WebPushException as ex:
            results.append(
                {"user": subscription.user.id, "success": False, "error": str(ex)}
            )

    return {"success": True, "results": results}









# {
#     "subscription_info": {
#         "endpoint": "https://example.pushservice.com/some-unique-endpoint",
#         "keys": {
#             "p256dh": "example_p256dh_key",
#             "auth": "example_auth_key"
#         }
#     },
#     "notification": {
#         "title": "Hello, World!",
#         "body": "This is a test notification.",
#         "icon": "https://example.com/icon.png",
#         "url": "https://example.com"
#     }
# }
