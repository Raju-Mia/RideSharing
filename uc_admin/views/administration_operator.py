from calendar import monthrange
from datetime import datetime, timedelta
from decimal import Decimal
from django.conf import settings
from rest_framework.pagination import PageNumberPagination
from utils.pagination import CustomPageNumberPagination #RM Add


from django.contrib.auth import get_user_model
from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import Q
from rest_framework import serializers, status, permissions
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveDestroyAPIView,
    get_object_or_404,
    UpdateAPIView,
    ListAPIView,
    RetrieveAPIView,
    CreateAPIView,
    RetrieveUpdateAPIView,
    DestroyAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.hashers import make_password
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from rest_framework.decorators import api_view

from rest_framework.permissions import IsAdminUser
from django.shortcuts import get_object_or_404




# from accounts.mail import send_mail #Only for Test or Acconts App
from utils.mail import send_mail, send_email_verification_token # This is mail Script to send mail


from accounts.helpers import get_n_length_random_string
from payment.helpers import create_setup_intent, is_stripe_customer
# from trip_management.helpers import trip_conflict_existsV3
# from trip_management.model_helpers import calculate_distance
# from trip_management.serializers import StaticTripRequestSerializer
from accounts.models import (
    TokenTypes,
    VerificationTokens,
    # AttachmentStatus,
    # Driver,
    # DriverStatus,
    # Manufacturer,
    # Vehicle,
    # VehicleAttachmentStatus,
    # VehicleModel,
    # DriverAttachmentStatus,
    Services,
    # VehicleStatus,
)

from driver_app.models import (
    Driver,
    DriverStatus,
    # DriverAttachmentStatus,
    # Manufacturer,
    Vehicle,
    VehicleModel,
    VehicleStatus,
    VehicleTypes,
    # VehicleTypesInfo,
    AttachmentStatus,
)



from accounts.serializers import (
    AdminSignsUpUserSerializer,
    VehicleDetailsSerializer,
    DriverSerializer,
    UserSerializer,
    # VehicleAssignWaitingListSerializer,
)
# from utils.fare import get_fare
from utils.helpers import (
    Int_Month_To_String,
    Months_Of_An_Year,
    get_dvla_data_for_vehicle,
)
from utils.mail import send_email_with_login_cedentials


# from trip_management.serializers import GetAllTripSerializer
# from uc_admin.helpers import get_drivers_v2, get_drivers_for_dispatch
from uc_admin.permissions import IsAdmin, IsOrganizationAdmin
from uc_admin.models import OperatorPermission, RejectedDriverInfo

User = get_user_model()

#Serializer
from uc_admin.serializers.administration_operator_serializers import (
    AdminOperatorsUserSerializer,
    AdminOperatorSignUpSerializerForAdministration,
    AdminOperatorDetailSerializer,
    AdminOperatorUpdateSerializer,
    AdminOperatorPasswordChangeSerializer,
    AdminOperatorPasswordResetSerializer,
    
    
    )




    
# Admin Operatior list
class AdminOperatorsList(APIView):
    permission_classes = [permissions.IsAuthenticated]  # Ensure only authenticated users can access this view
    pagination_class = CustomPageNumberPagination  # Use the custom pagination class

    def get(self, request, *args, **kwargs):
        # Get the operator type from the query parameter
        operator_type = request.query_params.get('type')

        # Filter based on the operator type
        if operator_type == 'activated':
            operator_list = User.objects.filter(is_active=True, is_operator=True)
        elif operator_type == 'deactivated':
            operator_list = User.objects.filter(is_active=False, is_operator=True)
        elif operator_type == 'terminated':
            operator_list = User.objects.filter(is_active=False, termination_date__isnull=False, is_operator=True)
        else:
            operator_list = User.objects.filter(is_operator=True)

        search_query = request.query_params.get('search')
        if search_query:
            operator_list = operator_list.filter(
                Q(email__icontains=search_query) |
                Q(username__icontains=search_query) |
                Q(full_name__icontains=search_query) |
                Q(phone__icontains=search_query)
            )

        # Paginate the filtered result
        paginator = self.pagination_class()
        paginated_operators = paginator.paginate_queryset(operator_list, request)

        # Serialize and return paginated response
        serialized_operators = AdminOperatorsUserSerializer(paginated_operators, many=True)
        return paginator.get_paginated_response(serialized_operators.data)



# Operatior Register (Not compalted)
class AdminOperatorRegister(APIView):
    permission_classes = [permissions.IsAuthenticated]  # Ensure only authenticated users can access this view

    @method_decorator(csrf_exempt)  # Disable CSRF protection for this specific view
    def post(self, request, *args, **kwargs):
        # Pass the request data to the serializer
        serializer = AdminOperatorSignUpSerializerForAdministration(data=request.data)

        if serializer.is_valid():
            # Retrieve validated data
            validated_data = serializer.validated_data
            username = validated_data.get('username', None)
            print("username is: ", username)
            email = validated_data.get('email', None)
            full_name = validated_data.get('full_name', None)
            phone = validated_data.get('phone', None)
            password = validated_data.get('password', None)
            whatsappnumber = validated_data.get('whatsappnumber', None)
            service = "united-administration"

            # Hash the password
            hashed_password = make_password(password)

            # Create the new user
            user = User.objects.create(
                username=username,
                email=email,
                full_name=full_name,
                phone=phone,
                whatsappnumber=whatsappnumber,
                service=service,
                password=hashed_password,  # Save the hashed password
                is_operator=True,  # Mark as operator
                is_active=True,  # Activate the account by default
            )
            
            # Send email verification token
            send_email_verification_token(
                user=user,
                email=email,
                name=full_name,
                username=username,
                password=password
            )
            # # Send the registration email
            # mail_sent = send_mail(payload)
            

            # Send a success response
            return Response(
                {"message": "Operator created successfully! Registration email sent."},
                status=status.HTTP_201_CREATED
            )


        else:
            # Return validation errors if the serializer is not valid
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




## from django.utils.decorators import method_decorator==For Test Parpose 
# from utils.mail import send_mail_async  # Assuming send_mail is handled asynchronously

# class AdminOperatorRegister(APIView):
#     permission_classes = [permissions.IsAuthenticated]

#     @method_decorator(csrf_exempt)
#     def post(self, request, *args, **kwargs):
#         # Pass the request data to the serializer
#         serializer = AdminOperatorSignUpSerializerForAdministration(data=request.data)

#         if serializer.is_valid():
#             # Call the save method on the serializer which handles user creation
#             user = serializer.save()

#             # Prepare the payload for email sending
#             email_payload = {
#                 'recipient_list': user.email,
#                 'name': user.full_name,
#                 'username': user.username,
#                 'password': serializer.validated_data.get('password'),  # Avoid storing or displaying this in logs.
#                 'email': user.email,
#                 'mail_type': 'login creds',
#             }

#             # Send the email asynchronously
#             send_mail_async(email_payload)

#             return Response(
#                 {"message": "Operator created successfully! Registration email sent."},
#                 status=status.HTTP_201_CREATED
#             )
#         else:
#             # Return validation errors if the serializer is not valid
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)








class AdminOperatorVerify(APIView):
    def get(self, request, *args, **kwargs):
        # Extracting the query parameters from the URL
        user_id = request.query_params.get('user_id')
        token = request.query_params.get('token')
        service = request.query_params.get('service')  # This could be used for future logic

        # Validating query parameters
        if not user_id or not token:
            return Response({"error": "Missing required parameters: user_id and token."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Fetch the user and token from the database
            user = get_object_or_404(User, id=user_id)
            verification_token = get_object_or_404(VerificationTokens, user=user, token=token, token_type=TokenTypes.email_verification)

        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        except VerificationTokens.DoesNotExist:
            return Response({"error": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the token is valid
        is_valid, message = verification_token.token_is_valid()

        if not is_valid:
            return Response({"error": message}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the email has already been verified
        if user.email_is_verified:
            response_data = {
                "status":True,
                "message": "User email is already verified."
            }
            return Response(response_data, status=status.HTTP_200_OK)

        # If the token is valid, mark the user's email as verified
        try:
            user.email_is_verified = True
            user.user_is_verified = True  # Optionally mark the user as fully verified
            user.save()
            response_data = {
                "status":True,
                "message": "User email verified successfully."
            }
            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": f"Failed to verify user email: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    
    
    

class AdminOperatorDetails(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, operator_id):
        try:
            # Fetch the operator by ID (or use another unique identifier if preferred)
            operator = User.objects.get(id=operator_id, is_operator=True, is_active=True)
        except User.DoesNotExist:
            return Response({"message": "Operator not found or not active."}, status=status.HTTP_404_NOT_FOUND)

        # Serialize the operator details
        serializer = AdminOperatorDetailSerializer(operator)

        # Return the operator details
        return Response(serializer.data, status=status.HTTP_200_OK)




class AdminOperatorInfoUpdate(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, operator_id):
        try:
            # Fetch the operator by ID
            operator = User.objects.get(id=operator_id, is_operator=True, is_active=True)
        except User.DoesNotExist:
            return Response({"message": "Operator not found or not active."}, status=status.HTTP_404_NOT_FOUND)

        # Create a serializer instance with the operator instance and request data
        serializer = AdminOperatorUpdateSerializer(operator, data=request.data, partial=True)

        if serializer.is_valid():
            # Save the updated operator details
            serializer.save()
            return Response({"message": "Operator updated successfully!"}, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)






class AdminOperatorPasswordChange(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, operator_id, *args, **kwargs):
        try:
            user = User.objects.get(id=operator_id, is_operator=True)
        except User.DoesNotExist:
            return Response({"error": "Operator not found!"}, status=status.HTTP_404_NOT_FOUND)

        serializer = AdminOperatorPasswordChangeSerializer(data=request.data)

        if serializer.is_valid():
            new_password = serializer.validated_data.get('new_password')
            user.set_password(new_password)
            user.save()
            return Response({"success": "Password updated successfully!"}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "Password must meet complexity requirements."}, status=status.HTTP_400_BAD_REQUEST)




# TODO Future work
class AdminOperatorPasswordReset(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, operator_id, *args, **kwargs):
        serializer = AdminOperatorPasswordResetSerializer(data=request.data)
        
        if serializer.is_valid():
            email = serializer.validated_data.get('email')
            try:
                user = User.objects.get(email=email, is_operator=True)
            except User.DoesNotExist:
                return Response({"error": "User with this email does not exist."}, status=status.HTTP_404_NOT_FOUND)

            # Generate password reset token
            token = account_activation_token.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            domain = get_current_site(request).domain
            reset_link = f"http://{domain}/reset-password/{uid}/{token}/"
            
            # Send email
            subject = "Password Reset Request"
            message = render_to_string('password_reset_email.html', {
                'user': user,
                'reset_link': reset_link,
            })
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])
            
            return Response({"success": "Password reset email sent successfully!"}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)






class AdminOperatorStatusUpdate(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, operator_id, *args, **kwargs):
        # Fetch the operator by UUID
        operator = get_object_or_404(User, id=operator_id, is_operator=True)

        # Get the action from request data (you can also use request.query_params if you prefer)
        action = request.data.get('action')

        if not action:
            return Response({"error": "Action is required (activate, deactivate, terminate)."}, status=status.HTTP_400_BAD_REQUEST)

        if action == 'deactivate':
            if operator.is_active:
                operator.is_active = False
                operator.save()
                return Response({"message": "Operator has been deactivated."}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Operator is already deactivated."}, status=status.HTTP_400_BAD_REQUEST)

        elif action == 'activate':
            if not operator.is_active:
                operator.is_active = True
                operator.save()
                return Response({"success": "Operator has been activated."}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Operator is already active."}, status=status.HTTP_400_BAD_REQUEST)

        elif action == 'terminate':
            if not operator.is_active:
                return Response({"error": "Operator is already terminated or inactive."}, status=status.HTTP_400_BAD_REQUEST)
            
            operator.is_active = False
            operator.termination_date = datetime.now()  # Ensure this field exists in the User model
            operator.save()
            return Response({"success": "Operator has been terminated."}, status=status.HTTP_200_OK)

        else:
            return Response({"error": f"Invalid action: {action}. Allowed actions are 'activate', 'deactivate', 'terminate'."}, status=status.HTTP_400_BAD_REQUEST)






class AdminOperatorDeactivated(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, operator_id, *args, **kwargs):
        # Fetch the operator by UUID
        operator = get_object_or_404(User, id=operator_id, is_operator=True)
        
        # Deactivate the operator
        if operator.is_active:
            operator.is_active = False
            operator.save()
            return Response({"message": "Operator has been deactivated."}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "Operator is already deactivated."}, status=status.HTTP_400_BAD_REQUEST)
        
        
        
class AdminOperatorActivated(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, operator_id, *args, **kwargs):
        # Fetch the operator by UUID
        operator = get_object_or_404(User, id=operator_id, is_operator=True)
        
        # Activate the operator
        if not operator.is_active:
            operator.is_active = True
            operator.save()
            return Response({"success": "Operator has been activated."}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Operator is already active."}, status=status.HTTP_400_BAD_REQUEST)




class AdminOperatorTerminated(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, operator_id, *args, **kwargs):
        # Fetch the operator by UUID
        operator = get_object_or_404(User, id=operator_id, is_operator=True)
        
        # Terminate the operator
        if not operator.is_active:
            return Response({"error": "Operator is already terminated or inactive."}, status=status.HTTP_400_BAD_REQUEST)
        
        operator.is_active = False
        operator.termination_date = datetime.now()  # Add this field to the User model or handle accordingly
        operator.save()
        
        return Response({"success": "Operator has been terminated."}, status=status.HTTP_200_OK)





class AdminActivatedOperatorsList(APIView):
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPageNumberPagination  # Ensure this is imported from your pagination module

    def get(self, request, *args, **kwargs):
        # Filter activated operators
        activated_operators = User.objects.filter(is_active=True, is_operator=True)
        
        # Initialize pagination
        paginator = self.pagination_class()
        paginated_operators = paginator.paginate_queryset(activated_operators, request)
        
        # Serialize and return paginated response
        serialized_operators = AdminOperatorsUserSerializer(paginated_operators, many=True)
        return paginator.get_paginated_response(serialized_operators.data)




class AdminDeactivatedOperatorsList(APIView):
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPageNumberPagination  # Ensure this is imported from your pagination module

    def get(self, request, *args, **kwargs):
        # Filter deactivated operators
        deactivated_operators = User.objects.filter(is_active=False, is_operator=True)
        
        # Initialize pagination
        paginator = self.pagination_class()
        paginated_operators = paginator.paginate_queryset(deactivated_operators, request)
        
        # Serialize and return paginated response
        serialized_operators = AdminOperatorsUserSerializer(paginated_operators, many=True)
        return paginator.get_paginated_response(serialized_operators.data)




class AdminTerminatedOperatorsList(APIView):
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPageNumberPagination  # Ensure this is imported from your pagination module

    def get(self, request, *args, **kwargs):
        # Filter terminated operators
        terminated_operators = User.objects.filter(is_active=False, termination_date__isnull=False, is_operator=True)
        
        # Initialize pagination
        paginator = self.pagination_class()
        paginated_operators = paginator.paginate_queryset(terminated_operators, request)
        
        # Serialize and return paginated response
        serialized_operators = AdminOperatorsUserSerializer(paginated_operators, many=True)
        return paginator.get_paginated_response(serialized_operators.data)




