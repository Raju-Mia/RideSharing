


# views.py
from utils.pagination import CustomPageNumberPagination
from django.contrib.auth import authenticate
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated


from rest_framework import generics
from rest_framework import filters
from django.db.models import Q

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from third_party_org_manager.models import OrganizationCustomer
from third_party_org_manager.serializers.customer_serializer import OrganizationCustomerSerializer
from django.shortcuts import get_object_or_404




class OrganizationCustomerListCreateAPIView(APIView):
    """
    GET: List all customers
    POST: Create a new customer
    """
    
    # permission_classes = [IsAuthenticated]
    # pagination_class = CustomPageNumberPagination  # Use custom pagination

    # def get(self, request):
    #     # Get the organization of the authenticated user
    #     organization = request.user.organization
    #     print("organiztion is: ", organization)

    #     # Filter customers based on the user's organization
    #     customers = OrganizationCustomer.objects.filter(organization=organization)
        
    #     # Paginate the queryset
    #     paginator = self.pagination_class()
    #     paginated_customers = paginator.paginate_queryset(customers, request)

    #     serializer = OrganizationCustomerSerializer(paginated_customers, many=True)
    #     return paginator.get_paginated_response(serializer.data)
    
    
    permission_classes = [IsAuthenticated]
    serializer_class = OrganizationCustomerSerializer
    pagination_class = CustomPageNumberPagination  # Custom pagination class

    def get_queryset(self, search_term=''):
        # Get the organization of the authenticated user
        organization = self.request.user.organization
        
        # Filter customers based on the organization
        queryset = OrganizationCustomer.objects.filter(organization=organization)

        # Apply search filter if a search term is provided
        if search_term:
            queryset = queryset.filter(
                Q(name__icontains=search_term) |
                Q(email__icontains=search_term) |
                Q(phone_number__icontains=search_term) |
                Q(company_name__icontains=search_term) |
                Q(whatsapp_number__icontains=search_term)
            )

        return queryset

    def get(self, request, *args, **kwargs):
        # Extract the search parameter from the query
        search_term = request.query_params.get('search', '')

        # Get the filtered queryset based on search term
        queryset = self.get_queryset(search_term)

        # Paginate the queryset
        paginator = self.pagination_class()
        paginated_queryset = paginator.paginate_queryset(queryset, request, view=self)

        # Serialize the paginated data
        serializer = self.serializer_class(paginated_queryset, many=True)
        
        # Return the paginated response
        return paginator.get_paginated_response(serializer.data)

        
        
    
    def post(self, request):
        user = request.user
        print("user is: ", user)
        
        # Assuming user has an organization relationship
        if not hasattr(user, 'organization'):
            return Response({"detail": "User does not have an associated organization."}, status=status.HTTP_400_BAD_REQUEST)
        
        organization = user.organization  # Fetch user's organization
        print("Organizaiton is ", organization)
        
        # Add organization to the incoming data
        data = request.data.copy()
        data['organization'] = str(organization.id)  # Convert UUID to string for serialization
        
        serializer = OrganizationCustomerSerializer(data=data)
        if serializer.is_valid():
            serializer.save()  # Organization is already set in the data
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




class OrganizationCustomerDetailAPIView(APIView):
    """
    GET: Retrieve a customer by ID
    PUT: Update a customer by ID
    DELETE: Delete a customer by ID
    """

    permission_classes = [IsAuthenticated]
    
    def get_object(self, pk):
        return get_object_or_404(OrganizationCustomer, pk=pk)

    def get(self, request, pk):
        customer = self.get_object(pk)
        serializer = OrganizationCustomerSerializer(customer)
        return Response(serializer.data)

    def put(self, request, pk):
        customer = self.get_object(pk)
        serializer = OrganizationCustomerSerializer(customer, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
    def patch(self, request, pk):
        customer = self.get_object(pk)
        serializer = OrganizationCustomerSerializer(customer, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def delete(self, request, pk):
        customer = self.get_object(pk)
        customer.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
