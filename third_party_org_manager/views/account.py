from django.shortcuts import render
from django.http import Http404
from django.conf import settings
from utils.pagination import CustomPageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth import authenticate
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied

from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

#Import
from accounts.helpers import (
    create_user,
    get_attachments_status,
    get_user_details,
    info_from_google,
    send_reset_password_code,
    update_driver_vehicle_info_status,
)

from utils.mail import send_mail, send_otp_mail, send_resend_otp_mail
from accounts.views.accounts_helper import send_phone_verification_otp, sms_otp_is_verified, mail_otp_is_verified
from django.contrib.auth import get_user_model
User = get_user_model()

from accounts.models import VerificationOTP
from accounts.models import Organization, CustomUser, UserProfile
from accounts.serializers import UserSerializer

from organization_manager.models import Organization
from third_party_org_manager.serializers.account_serializer import (
    ThirdPartyUserLoginSerializer,
    ThirdPartyOrganizationRegisterSerializer,
    ThirdPartyOrganizationProfileUpdateSerializer,
    ThirdPartyOrganizationCommissionSetSerializer,

    ThirdPartyUserListSerializer,
    ThirdPartyUserRegistrationSerializer,
    ThirdPartyOperatorProfileUpdateSerializer,
    ThirdPartyOperatorProfileRetrieveSerializer,
    ThirdPartyChangePasswordSerializer,
    ThirdPartyOrganizationMailOtpVerificationSerializer,
    ThirdPartyOrganizationUserChangePasswordSerializer,
    
    
)


from notification_manager.models import (
    FCMToken, 
    Notification, 
    NotificationLog,
    DriverNotification,
    ClientNotification, 
    AdminNotification, 
    ConciergeNotification, 
    NotificationTrigger,
    NotificationPreference,
    NotifyMessage,
    )



#==============Login ============== 
class ThirdPartyUserLoginView(APIView):
    # permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = ThirdPartyUserLoginSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']
            user = authenticate(username=username, password=password)
            # print("user", user.username)

            if user is not None:
                # Check if the user has an organization
                if user.organization is None:
                    return Response({'error': 'Access denied: users with an organization cannot log in.'}, status=status.HTTP_403_FORBIDDEN)

                # Create JWT tokens (if the user does not have an organization)
                # refresh = RefreshToken.for_user(user)
                # return Response({
                #     'refresh': str(refresh),
                #     'access': str(refresh.access_token),
                # }, status=status.HTTP_200_OK)
                
                return Response(get_user_details(user), status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Invalid username or password'}, status=status.HTTP_401_UNAUTHORIZED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)







class ThirdPartyUserLoginView2(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = ThirdPartyUserLoginSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']
            user = authenticate(username=username, password=password)

            if user is not None:
                # Check if the user has an organization
                if user.organization is None:
                    return Response({'error': 'Access denied: users with an organization cannot log in.'}, status=status.HTTP_403_FORBIDDEN)

                # Collect notification data
                print("---i am here---")
                fcm_token = request.data.get('fcm_token') or None
                device_type = request.data.get('device_type') or None
                device_id = request.data.get('device_id') or None
                device_model = request.data.get('device_model') or None
                device_os_version = request.data.get('device_os_version') or None
                device_location_latitude = request.data.get('device_location_latitude') or None
                device_location_longitude = request.data.get('device_location_longitude') or None
                
                ip_address = self.get_client_ip(request)
                print("Default ip_address: ", ip_address)
                print("Get the Ip from user: ", device_id)

                # Check for an existing device entry for the same user and IP address
                fcm_token_instance, created = FCMToken.objects.get_or_create(
                    user=user,
                    fcm_token=fcm_token,
                    defaults={
                        'fcm_token': fcm_token,
                        'device_id': device_id,
                        'device_type': device_type,
                        'device_model': device_model,
                        'device_os_version': device_os_version,
                        'device_location_latitude': device_location_latitude,
                        'device_location_longitude': device_location_longitude,
                        'active_status': True,
                        'block_status': False,
                        'verification_required': False,
                        'verification_status': True,
                    }
                )

                # Update existing token details if already present
                if not created:
                    fcm_token_instance.fcm_token = fcm_token
                    fcm_token_instance.device_type = device_type
                    fcm_token_instance.device_model = device_model
                    fcm_token_instance.device_os_version = device_os_version
                    fcm_token_instance.device_location_latitude = device_location_latitude
                    fcm_token_instance.device_location_longitude = device_location_longitude
                    fcm_token_instance.active_status = True
                    fcm_token_instance.save()

                # Create JWT tokens and respond
                refresh = RefreshToken.for_user(user)
                
                return Response({
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    'user_details': get_user_details(user),
                }, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Invalid username or password'}, status=status.HTTP_401_UNAUTHORIZED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def get_client_ip(request):
        """Get client IP address from request headers."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip







# ========= Third Party organization Register View =================
class ThirdPartyOrganizationRegister(APIView):
    
    def post(self, request, *args, **kwargs):
        print("I am 3rd Party Org Reg!--")
        serializer = ThirdPartyOrganizationRegisterSerializer(data=request.data)
        
        if serializer.is_valid():
            result = serializer.save()
            

            
            # Get the user email from the serializer data
            user_email = result['user'].email
            
  
            
            try:
                # Retrieve the user by email
                user = User.objects.get(email=user_email)
            except User.DoesNotExist:
                return Response({"message": "User Does Not Exit."},status=status.HTTP_400_BAD_REQUEST)

            
            if user:
                # Send OTP email
                send_otp_mail(user)
            else:
                return Response({"message": "Email Verify mail not send!"},status=status.HTTP_400_BAD_REQUEST)
            
            



            return Response({
                'organization': {
                    'name': result['organization'].name,
                    'email': result['organization'].email,
                    'phone': result['organization'].phone_number,
                    'address': result['organization'].address_line1
                },
                'user': {
                    'full_name': result['user'].full_name,
                    'email': result['user'].email,
                    'phone': result['user'].phone,
                    'username': result['user'].username
                },
                'user_profile': {
                    'designation': result['user_profile'].designation,
                    'contact': result['user_profile'].contact
                },
                "message":"Successfully Organization Registered!",
                "user_id": user.id
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)






# ========= Third Party organization Verify View =================
class ThirdPartyOrganizationMailOtpVerification(APIView):
    def post(self, request):
        serializer = ThirdPartyOrganizationMailOtpVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user = User.objects.get(id=serializer.validated_data["user_id"])
        except User.DoesNotExist:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={"message": "Organization User does not exist"},
            )
        
        
        otp_verified_status,otp_obj_id,otp_verified_message = mail_otp_is_verified(user,serializer.validated_data["verification_otp"])
        # print("otp_verified_status,otp_obj_id,otp_verified_message", otp_verified_status,otp_obj_id,otp_verified_message)
        
        
        if otp_verified_status and otp_obj_id is not None:
            
            # Filter all VerificationOTP objects for the given user
            user_verification_otp_objects = VerificationOTP.objects.filter(user=user,id=otp_obj_id).first()
            user_verification_otp_objects.delete()


            user.is_active = True
            user.email_is_verified = True
            user.user_is_verified = True
            user.save()
            
                
            return Response(data=get_user_details(user),status=status.HTTP_200_OK)
            
        return Response({"message": otp_verified_message},status=status.HTTP_400_BAD_REQUEST)

        
        
        
#============= Resend Mail OTP for 3rd Party Organization Verification  ===================
class ThirdPartyOrganizationResentMailOtp(APIView):
    def post(self, request, user_id):
        print("============Resend Otp For Number Verification calling ==============")
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"message": "User Does Not Exit."},status=status.HTTP_400_BAD_REQUEST)
        
        
        try:
            # Filter all VerificationOTP objects for the given user
            user_verification_otp_objects = VerificationOTP.objects.filter(user=user)
            user_verification_otp_objects.delete()

            print("Here---")
            # Send resent OTP email
            send_resend_otp_mail(user)


            response_data = {
                "message": "Reset OTP successfuly send to organization mail.",
                "user_id": user.id
            }
            return Response(
                response_data,
                status=status.HTTP_200_OK,
                )

            
        except user_verification_otp_objects.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)






#============== Third Party Organization Profile Update ===================
class ThirdPartyOrganizationProfileUpdateView(APIView):
    permission_classes = [IsAuthenticated]  # Ensure the user is authenticated

    def post(self, request, *args, **kwargs):
        # Get the authenticated user
        user = request.user
        
        # Ensure the user is an organization admin
        if not request.user.is_organization_admin:
            return Response({"message": "You are not Organization Admin."}, status=status.HTTP_403_FORBIDDEN)
        
        # Get the user's associated organization
        organization = user.admin_organization
        
        serializer = ThirdPartyOrganizationProfileUpdateSerializer(organization, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Organization profile updated successfully.',
                # 'organization': serializer.data,
                'organization': ThirdPartyOrganizationProfileUpdateSerializer(organization).data
                
            }, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




class ThirdPartyOrganizationCommissionSetView(APIView):
    permission_classes = [IsAuthenticated]  # Ensure the user is authenticated

    def get(self, request, *args, **kwargs):
        # Get the authenticated user
        user = request.user
        
        # Ensure the user is an organization admin
        if not user.is_organization_admin:
            return Response({"message": "You are not Organization Admin."}, status=status.HTTP_403_FORBIDDEN)
        
        # Get the user's associated organization
        organization = user.admin_organization
        
        # Use the serializer to retrieve the current organization commission data
        serializer = ThirdPartyOrganizationCommissionSetSerializer(organization)
        
        return Response({
            'message': 'Organization Commission retrieved successfully.',
            'organization': serializer.data
        }, status=status.HTTP_200_OK)


    def patch(self, request, *args, **kwargs):
        # Get the authenticated user
        user = request.user
        
        # Ensure the user is an organization admin
        if not user.is_organization_admin:
            return Response({"message": "You are not Organization Admin."}, status=status.HTTP_403_FORBIDDEN)
        
        # Get the user's associated organization
        organization = user.admin_organization
        
        # Check if 'org_commission' is provided in the request data
        org_commission = request.data.get('org_commission')
        
        if org_commission is None:
            return Response({
                'message': 'Value is not provided',
            }, status=status.HTTP_200_OK)
        
        # Proceed with serialization and validation if 'org_commission' is provided
        serializer = ThirdPartyOrganizationCommissionSetSerializer(organization, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Organization Commission Set successfully.',
                'organization': ThirdPartyOrganizationCommissionSetSerializer(organization).data
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        
        



class ThirdPartyOrganizationProfileDetailsView(APIView):
    permission_classes = [IsAuthenticated]  # Ensure the user is authenticated

    def get(self, request, *args, **kwargs):
        # Get the authenticated user
        user = request.user
        
        # Ensure the user is an organization admin
        if not user.is_organization_admin:
            return Response({"message": "You are not Organization Admin."}, status=status.HTTP_403_FORBIDDEN)
        
        # Get the user's associated organization
        organization = user.admin_organization
        
        # Serialize the organization data
        serializer = ThirdPartyOrganizationProfileUpdateSerializer(organization)
        
        return Response({
            'organization': serializer.data
        }, status=status.HTTP_200_OK)







class ThirdPartyOrganizationUserListView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ThirdPartyUserListSerializer
    pagination_class = CustomPageNumberPagination  # Use custom pagination class

    def get_queryset(self, search_term=''):
        print("================ThirdPartyOrganizationUserListView==============")
        # Get the organization of the logged-in user
        organization = self.request.user.organization

        # Filter by organization and search term (if provided)
        queryset = CustomUser.objects.filter(organization=organization, is_active=True, is_organization_admin=False, terminated_status=False)
        
        if search_term:
            queryset = queryset.filter(
                Q(full_name__icontains=search_term) |
                Q(email__icontains=search_term) |
                Q(phone__icontains=search_term) |
                Q(username__icontains=search_term)
            )

        return queryset

    def get(self, request, *args, **kwargs):
        # Extract the search parameter from the query
        search_term = request.query_params.get('search', '')

        # Get the filtered queryset
        queryset = self.get_queryset(search_term)
        
        # Paginate the queryset
        paginator = self.pagination_class()  # Custom paginator
        paginated_queryset = paginator.paginate_queryset(queryset, request, view=self)

        # Serialize the paginated data
        serializer = self.serializer_class(paginated_queryset, many=True)

        # Return paginated response with serialized data
        return paginator.get_paginated_response(serializer.data)







class ThirdPartySearchOperatorView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        # Extract search parameters from the request
        search_term = request.query_params.get('search', '')  # Get search term from query params
        
        # Filter users based on search term
        queryset = CustomUser.objects.filter(
            Q(full_name__icontains=search_term) |
            Q(email__icontains=search_term) |
            Q(phone__icontains=search_term) |
            Q(username__icontains=search_term)
        )
        
        # Pagination
        paginator = PageNumberPagination()
        paginator.page_size = int(request.query_params.get('page_size', 20))  # Default to 20 if not provided
        paginated_users = paginator.paginate_queryset(queryset, request)
        
        # Serialize the paginated result
        serializer = ThirdPartyUserListSerializer(paginated_users, many=True)
        
        # Return paginated response
        return paginator.get_paginated_response(serializer.data)





class ThirdPartySearchOperatorView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        # Extract search parameters from the request
        search_term = request.query_params.get('search', '')  # Get search term from query params
        
        # Get the organization of the authenticated user
        organization = request.user.organization
        
        # Filter users based on search term and organization
        queryset = CustomUser.objects.filter(
            Q(full_name__icontains=search_term) |
            Q(email__icontains=search_term) |
            Q(phone__icontains=search_term) |
            Q(username__icontains=search_term),
            organization=organization,
        )
        
        # Pagination
        paginator = PageNumberPagination()
        paginator.page_size = int(request.query_params.get('page_size', 20))  # Default to 20 if not provided
        paginated_users = paginator.paginate_queryset(queryset, request)
        
        # Serialize the paginated result
        serializer = ThirdPartyUserListSerializer(paginated_users, many=True)
        
        # Return paginated response
        return paginator.get_paginated_response(serializer.data)





#============== Operator Register ============== 
class ThirdPartyUserRegistrationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        print(" i am here!")
        serializer = ThirdPartyUserRegistrationSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'User created successfully'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    



# =========  ThirdPartyOrganizationrUserterminate =================
class ThirdPartyOperatorEditView(APIView):
    permission_classes = [IsAuthenticated]  # Ensure the request is from an authenticated user

    def post(self, request, user_id, *args, **kwargs):
        print(" ==== I am here!-----for user profile edit-----")
        try:
            # Retrieve the user by id
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        

        # Ensure the current user can only change their own password unless they are a superuser
        if request.user != user and not request.user.is_organization_admin:
            return Response({"message": "You do not have permission to update operator details!."}, status=status.HTTP_200_OK)

        print(" i am here!!")
        serializer = ThirdPartyOperatorProfileUpdateSerializer(user, data=request.data, partial=True, context={'request': request})

        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'User updated successfully',
                'user': serializer.data
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    
    




#============== Operator Profile Update ============== 
class ThirdPartOperatorProfileUpdateView(APIView):
    permission_classes = [IsAuthenticated]  # Ensure the user is authenticated

    def post(self, request, *args, **kwargs):
        print(" =====ThirdPartOperatorProfileUpdateView========== ")
        user = request.user
        serializer = ThirdPartyOperatorProfileUpdateSerializer(user, data=request.data, partial=True, context={'request': request})
        
        
        # # Ensure the current user can only change their own password unless they are a superuser
        # if request.user.is_organization_admin:
        #     return Response({"message": "You do not have permission to Update!"}, status=status.HTTP_200_OK)
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Profile updated successfully',
                # 'user': serializer.data,
                # "user_info": UserSerializer(user).data,
                "user": ThirdPartyOperatorProfileRetrieveSerializer(user).data
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




class ThirdPartOperatorProfileDetailsView(APIView):
    permission_classes = [IsAuthenticated]  # Ensure the user is authenticated

    def get(self, request, *args, **kwargs):
        user = request.user
        print("user", user)
        serializer = ThirdPartyOperatorProfileRetrieveSerializer(user)
        
        
        # # Ensure the current user can only change their own password unless they are a superuser
        # if request.user.is_organization_admin:
        #     return Response({"message": "You do not have permission to Update!"}, status=status.HTTP_200_OK)


        return Response(serializer.data, status=status.HTTP_200_OK)








 # =========  3rd Party Organization Myself User Password Change View =================
class ThirdPartyMyselfUserChangePassword(APIView):
    permission_classes = [IsAuthenticated]  # Only authenticated users can access this endpoint

    def post(self, request, *args, **kwargs):
        serializer = ThirdPartyChangePasswordSerializer(data=request.data)
        
        if serializer.is_valid():
            user = request.user
            old_password = serializer.validated_data['old_password']
            new_password = serializer.validated_data['new_password']
            
            # Check if the old password is correct
            if not user.check_password(old_password):
                return Response({"old_password": ["Old password is incorrect."]}, status=status.HTTP_400_BAD_REQUEST)

            # Set the new password
            user.set_password(new_password)
            user.save()

            return Response({"message": "Password changed successfully."}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)






# =========  3rd Party Organization User Password Change View =================
class ThirdPartyOrganizationChangePasswordForUser(APIView):
    permission_classes = [IsAuthenticated]  # Ensure the request is from an authenticated user

    def post(self, request, user_id, *args, **kwargs):
        print(" ==== ThirdPartyOrganizationChangePasswordForUser---------")
        try:
            # Retrieve the user by id
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        
        
        # Ensure the current user can only change their own password unless they are a superuser
        if request.user != user and not request.user.is_organization_admin:
            raise PermissionDenied("You do not have permission to change this user's password.")
        
        # Pass the request data to the serializer
        serializer = ThirdPartyOrganizationUserChangePasswordSerializer(data=request.data)
        
        if serializer.is_valid():
            new_password = serializer.validated_data['new_password']
            
            # Set the new password without checking the old one
            user.set_password(new_password)
            user.save()

            return Response({"message": "Password changed successfully."}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    


# =========  ThirdPartyOrganizationrUserterminate =================
class ThirdPartyOrganizationrUserTerminate(APIView):
    permission_classes = [IsAuthenticated]  # Ensure the request is from an authenticated user

    def post(self, request, user_id, *args, **kwargs):
        print(" ==== I am here!-----for terminate-----")
        try:
            # Retrieve the user by id
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        

        # Ensure the current user can only change their own password unless they are a superuser
        if request.user != user and not request.user.is_organization_admin:
            return Response({"message": "You do not have permission to Terminated!."}, status=status.HTTP_200_OK)

        if user:
            user.status = False
            user.is_active = False
            user.terminated_status = True
            user.terminated_resone = "User Is Terminated form third party organization admin portal."
            user.terminated_at = timezone.now()
            user.save()
            print("===========done=========")
            return Response({"message": "User terminated successfully."}, status=status.HTTP_200_OK)
        
        return Response({"message": "Something is wrong!."}, status=status.HTTP_400_BAD_REQUEST)