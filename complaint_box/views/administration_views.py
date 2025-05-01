from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from complaint_box.models import ComplaintBox, ComplaintStatus
from complaint_box.serializers.administration_serializers import (ComplaintBoxSerializer, AdministratorComplaintDetailSerializer,
                                                                AdministratorComplaintRemarkSerializer, )
from utils.pagination import CustomPageNumberPagination
from django.db.models import Q
from datetime import datetime
from rest_framework.permissions import IsAuthenticated

from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
from django.conf import settings

from django.db.models import Case, When, Value, IntegerField

class AdministratorComplaintList(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        complaints = ComplaintBox.objects.all()

        status_ordering = Case(
            When(complaint_status=ComplaintStatus.SUBMITTED, then=Value(1)),
            When(complaint_status=ComplaintStatus.UNDER_REVIEW, then=Value(2)),
            When(complaint_status=ComplaintStatus.IN_PROGRESS, then=Value(3)),
            When(complaint_status=ComplaintStatus.INVALID, then=Value(4)),
            When(complaint_status=ComplaintStatus.SOLVED, then=Value(5)),
            output_field=IntegerField(),
        )
        complaints = complaints.annotate(status_order=status_ordering).order_by('status_order', '-updated_at')
        search_query = request.query_params.get('search', None)
        if search_query:
            complaints = complaints.filter(
                Q(title__icontains=search_query) | Q(description__icontains=search_query) |
                Q(case_id__icontains=search_query) | Q(author_name__icontains=search_query) |
                Q(author_phone__icontains=search_query) | Q(author_email__icontains=search_query)
            )
        filter_query = request.query_params.get('status', None)
        if filter_query:
            complaints = complaints.filter(complaint_status=filter_query)
        paginator = CustomPageNumberPagination()
        paginated_complaints = paginator.paginate_queryset(complaints, request)
        serializer = ComplaintBoxSerializer(paginated_complaints, many=True)
        return paginator.get_paginated_response(serializer.data)

class AdministratorComplaintDetail(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, complaint_id):
        try:
            complaint = ComplaintBox.objects.get(id=complaint_id)

            serializer = AdministratorComplaintDetailSerializer(complaint)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ComplaintBox.DoesNotExist:
            return Response(
                {"detail": "Complaint not found or access denied."},
                status=status.HTTP_404_NOT_FOUND
            )


class AdministratorComplaintRemark(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, complaint_id):
        user = request.user
        data=request.data
        complaint = get_object_or_404(ComplaintBox, id=complaint_id)
        
        address = complaint.author_email
        case_id = complaint.case_id



        serializer = AdministratorComplaintRemarkSerializer(
            data=data, 
            context={'request': request}
        )

        
        if serializer.is_valid():
            new_status = request.data.get('complaint_status')
            if new_status:
                complaint.complaint_status = new_status
                complaint.save(update_fields=['complaint_status'])
            
            serializer.save(
                complaint=complaint,
                remark_by=user,
                complaint_box_status=new_status
            )
            remark = serializer.data

            subject = f'case ID: {case_id}, status: {remark['complaint_box_status']}'
            message = f'Dear {complaint.author_name},\n\n{remark["remark"]}.\n\nRegards,\nComplaint Management Team'
            if address:
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [address])
            return Response(
                {
                    "message": "Remark created successfully.",
                    "remark": remark
                },
                status=status.HTTP_201_CREATED
            )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)