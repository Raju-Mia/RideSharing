from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend



    
# class EmailBackend(ModelBackend):
#     def authenticate(self, request, username=None, password=None, **kwargs):
#         service = kwargs.get("service", "")
#         phone_or_email = kwargs.get("phone_or_email", None)
#         user_model = get_user_model()

#         print(f"Authenticate: phone_or_email={phone_or_email}, service={service}")

#         if phone_or_email is None:
#             return None

#         try:
#             # Check if the user is a superuser first
#             user = None
#             if "@" in phone_or_email:
#                 user = user_model.objects.get(email=phone_or_email,terminated_status=False)
#             else:
#                 user = user_model.objects.get(phone=phone_or_email,terminated_status=False)

#             # If the user is a superuser, allow login without service and verification checks
#             if user.is_superuser:
#                 if not (user.is_active and user.is_staff and user.is_superuser):
#                     print("Superuser status flags are not all True")
#                     return None
#             else:
#                 # For non-superuser users, check service and verification status
#                 if "@" in phone_or_email:
#                     user = user_model.objects.get(
#                         email=phone_or_email,
#                         is_active=True,
#                         service=service,
#                         email_is_verified=True,
#                         user_is_verified=True,
#                         terminated_status=False
#                         )
#                 else:
#                     user = user_model.objects.get(
#                         phone=phone_or_email,
#                         is_active=True,
#                         service=service,
#                         phone_is_verified=True,
#                         user_is_verified=True,
#                         terminated_status=False
#                         )

#             if user.check_password(password):
#                 return user

#         except user_model.DoesNotExist:
#             print("User does not exist or is inactive")
#             return None
#         except Exception as e:
#             print(f"Exception: {e}")
#             return None

#         print("Password check failed")
#         return None
    



class EmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        service = kwargs.get("service", "")
        phone_or_email = kwargs.get("phone_or_email", None)
        user_model = get_user_model()

        print(f"Authenticate: phone_or_email={phone_or_email}, service={service}")

        if phone_or_email is None:
            return None

        try:
            # Check if the user is a superuser first
            user = None
            if "@" in phone_or_email:
                user = user_model.objects.get(email=phone_or_email, terminated_status=False)
            else:
                user = user_model.objects.get(phone=phone_or_email, terminated_status=False)

            # If the user is a superuser, allow login without service and verification checks
            if user.is_superuser:
                if not (user.is_active and user.is_staff and user.is_superuser):
                    print("Superuser status flags are not all True")
                    return None
            else:
                # For non-superuser users, check service and verification status
                if "@" in phone_or_email:
                    user = user_model.objects.get(
                        email=phone_or_email,
                        is_active=True,
                        service=service,
                        email_is_verified=True,
                        user_is_verified=True,
                        terminated_status=False
                    )
                else:
                    user = user_model.objects.get(
                        phone=phone_or_email,
                        is_active=True,
                        service=service,
                        phone_is_verified=True,
                        user_is_verified=True,
                        terminated_status=False
                    )

            # If password is provided, check it
            if password:
                if user.check_password(password):
                    return user
                else:
                    print("Password check failed")
                    return None
            else:
                # Allow authentication without password
                return user

        except user_model.DoesNotExist:
            print("User does not exist or is inactive")
            return None
        except Exception as e:
            print(f"Exception: {e}")
            return None






# class EmailBackend(ModelBackend):
#     def authenticate(self, request, username=None, password=None, **kwargs):
#         service = kwargs.get("service", "")
#         phone = kwargs.get("phone", None)
#         user_model = get_user_model()
#         if phone:
#             try:
#                 user = user_model.objects.get(
#                     phone=phone, is_active=True, service=service, phone_is_verified=True
#                 )
#             except user_model.DoesNotExist:
#                 return None
#         else:
#             try:
#                 user = user_model.objects.get(
#                     email=username,
#                     is_active=True,
#                     service=service,
#                     email_is_verified=True,
#                 )
#             except user_model.DoesNotExist:
#                 return None
#         if user.check_password(password):
#             return user
#         return None



# # =========== main
# class EmailBackend(ModelBackend):
#     def authenticate(self, request, username=None, password=None, **kwargs):
#         service = kwargs.get("service", "")
#         phone = kwargs.get("phone", None)
#         user_model = get_user_model()
#         if phone:
#             try:
#                 user = user_model.objects.get(
#                     phone=phone, is_active=True, service=service, phone_is_verified=True
#                 )
#             except user_model.DoesNotExist:
#                 print("Custom user authentication user does not find by phone number.")
#                 return None
#         else:
#             try:
#                 user = user_model.objects.get(
#                     email=username,
#                     is_active=True,
#                     service=service,
#                     email_is_verified=True,
#                 )
#             except user_model.DoesNotExist:
#                 print("Custom user authentication user does not find by phone email.")

#                 return None
#         if user.check_password(password):
#             return user
#         return None
    