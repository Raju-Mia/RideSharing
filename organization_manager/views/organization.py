from django.contrib.auth import get_user_model
from django.shortcuts import render
from django.http import Http404
from django.conf import settings
from django.contrib.auth import authenticate
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from utils.pagination import CustomPageNumberPagination
from django.utils import timezone
from django.contrib.auth.models import User
from rest_framework.exceptions import PermissionDenied



from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from organization_manager.models import Organization




from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404


from rest_framework import permissions
from rest_framework import generics




#Import
from accounts.models import Organization, CustomUser, UserProfile
from organization_manager.models import Organization
from organization_manager.serializers.organization_serializer import (
    OrganizationListSerializer,
    UserProfileSerializer,
    OrganizationSerializer,
    OrganizationRegisterSerializer,
    OrganizationUpdatedSerializer,
    OrganizationChangePasswordForUserSerializer,
    
    )



from rest_framework import generics
from django.db.models import Q

class OrganizationList(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPageNumberPagination  # Use your custom pagination class
    serializer_class = OrganizationListSerializer

    def get_queryset(self, search_term=''):
        # Filter organizations based on search term
        queryset = Organization.objects.filter(is_active=True)
        
        
        # Apply search filter if a search term is provided
        if search_term:
            queryset = queryset.filter(
                Q(name__icontains=search_term) |
                Q(email__icontains=search_term) |
                Q(phone_number__icontains=search_term) |
                Q(whatsapp_number__icontains=search_term) |
                Q(admin_user__full_name__icontains=search_term) |
                Q(phone_number__icontains=search_term)
            )

        return queryset


    def get(self, request, *args, **kwargs):
        # Extract the search parameter from the query
        search_term = request.query_params.get('search', '')

        # Get the filtered queryset based on search term
        queryset = self.get_queryset(search_term)

        # Initialize the paginator
        paginator = self.pagination_class()

        # Get page and page_size from query params if they are provided
        page = request.query_params.get('page', 1)
        page_size = request.query_params.get('page_size', paginator.page_size)
        
        paginator.page_size = int(page_size)  # Set page size
        
        # Paginate the filtered result
        paginated_organizations = paginator.paginate_queryset(queryset, request, view=self)
        
        # Serialize and return paginated response
        serializer = self.serializer_class(paginated_organizations, many=True)
        
        # Return paginated response including the serialized data
        return paginator.get_paginated_response(serializer.data)


    






#============== Crate Organization with admin user assgin ============== 
class OrganizationRegister(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        serializer = OrganizationRegisterSerializer(data=request.data)
        
        if serializer.is_valid():
            result = serializer.save()
            
            # =======================
            
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
                "message":"Successfully Organization Registered!"
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)







class OrganizationUpdate(APIView):
    permission_classes = [IsAuthenticated]
    
    def put(self, request, pk):
        try:
            organization = Organization.objects.get(pk=pk)
        except Organization.DoesNotExist:
            return Response({'error': 'Organization not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = OrganizationUpdatedSerializer(organization, data=request.data, partial=True)  # 'partial=True' allows partial updates
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
    



class OrganizationDelete(APIView): #TODO FW-What happen when organization will be delete ?
    permission_classes = [IsAuthenticated]
    
    def delete(self, request, pk):
        try:
            organization = Organization.objects.get(pk=pk)
        except Organization.DoesNotExist:
            return Response({'error': 'Organization not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        organization.is_active = False  # Soft delete: mark organization as inactive
        organization.save()
        return Response({'message': 'Organization deleted successfully.'}, status=status.HTTP_204_NO_CONTENT)








# ====== Organization Password Change Veiw===========
class OrganizationChangePasswordForUser(APIView):
    permission_classes = [IsAuthenticated]  # Ensure the request is from an authenticated user

    def post(self, request, user_id, *args, **kwargs):
        try:
            # Retrieve the user by id
            user = CustomUser.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        
        
        # # Ensure the current user can only change their own password unless they are a superuser
        # if request.user != user and not request.user.is_superuser:
        #     raise PermissionDenied("You do not have permission to change this user's password.")
        
        # Pass the request data to the serializer
        serializer = OrganizationChangePasswordForUserSerializer(data=request.data)
        
        if serializer.is_valid():
            new_password = serializer.validated_data['new_password']
            
            # Set the new password without checking the old one
            user.set_password(new_password)
            user.save()

            return Response({"message": "Password changed successfully."}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    



# =========  OrganizationrUserTerminate =================
class OrganizationrUserTerminate(APIView):
    permission_classes = [IsAuthenticated]  # Ensure the request is from an authenticated user

    def post(self, request, user_id, *args, **kwargs):
        print(" i am here!=============")
        try:
            user = CustomUser.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        

        # # Ensure the current user can only change their own password unless they are a superuser
        # if request.user != user and not request.user.is_organization_admin:
        #     return Response({"message": "You do not have permission to change this user's password."}, status=status.HTTP_200_OK)

        if user:
            user.status = False
            user.is_active = False
            user.terminated_status = True
            user.terminated_resone = "Organization Operator Is Terminated form UC organization admin portal."
            user.terminated_at = timezone.now()
            user.save()
            
            # if user.organization:
            #     org_id = user.organization.id
            #     print("org_id: ", org_id)
            #     organization = Organization.objects.filter(id=org_id, is_active=True).first()
            #     organization.is_active = False
            #     organization.is_terminate = True
            #     organization.save()
                
            return Response({"message": "Organization Operator terminated successfully."}, status=status.HTTP_200_OK)
        
        return Response({"message": "Something is wrong!."}, status=status.HTTP_400_BAD_REQUEST)
    
    
    
    
    
class OrganizationSearchView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPageNumberPagination  # Use your custom pagination class

    def get(self, request, *args, **kwargs):
        query = request.query_params.get('q', None)
        organizations = Organization.objects.filter(is_active=True)

        if query:
            organizations = organizations.filter(
                Q(name__icontains=query) | 
                Q(phone_number__icontains=query) |
                Q(email__icontains=query)
            )

        # Paginate the filtered result
        paginator = self.pagination_class()
        paginated_organizations = paginator.paginate_queryset(organizations, request)
        
        # Serialize and return paginated response
        serializer = OrganizationListSerializer(paginated_organizations, many=True)
        return paginator.get_paginated_response(serializer.data)
