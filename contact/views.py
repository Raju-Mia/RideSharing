# contact view
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import permissions
from django.shortcuts import get_object_or_404

from .models import Contact, Newsletter, ComplaintBox

from .serializers import (
    ContactSerializer,
    NewsletterSerializer,
    ComplaintBoxSerializer,
    UpdateComplaintBoxSerializer,
    CreateComplaintBoxSerializer,
)


class ContactView(generics.ListCreateAPIView):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer


class NewsletterView(generics.ListCreateAPIView):
    queryset = Newsletter.objects.all()
    serializer_class = NewsletterSerializer


class Complaint(APIView):
    # , LimitOffsetPagination
    permission_classes = [permissions.IsAuthenticated]

    # get all user and all complaint
    def get(self, request, format=None):
        complaint = ComplaintBox.objects.all().order_by("-created_at")
        serializer = ComplaintBoxSerializer(complaint, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        data = request.data.copy()  # Create a copy of the request data to modify it
        data[
            "created_by"
        ] = request.user.id  # Set the created_by field to the user's ID

        serializer = CreateComplaintBoxSerializer(data=data)

        if serializer.is_valid():
            serializer.save(created_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors)


class ComplaintDetails(APIView):
    permission_classes = [permissions.IsAuthenticated]


    def patch(self, request, id, format=None):
        complaint = get_object_or_404(ComplaintBox, id=id)
        # if complaint.user != request.user:
        #     return Response({"detail": "You do not have permission to update this complaint."}, status=status.HTTP_403_FORBIDDEN)
        print(self.request.data)
        serializer = UpdateComplaintBoxSerializer(
            complaint, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data)
        return Response(serializer.errors)
