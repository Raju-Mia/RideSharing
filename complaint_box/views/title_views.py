from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils.translation import gettext_lazy as _
from complaint_box.models import TITLE, REPORT_SUBCATEGORIES, LOST_AND_FOUND_SUBCATEGORIES




class GetAllTitles(APIView):
    def get(self, request, *args, **kwargs):
        titles = [item.label for item in TITLE]
        return Response({"titles": titles}, status=status.HTTP_200_OK)


class GetAllReportSubcategories(APIView):
    def get(self, request, *args, **kwargs):
        report_subcategories = [item.label for item in REPORT_SUBCATEGORIES]
        return Response({"report_subcategories": report_subcategories}, status=status.HTTP_200_OK)


class GetAllLostAndFoundSubcategories(APIView):
    def get(self, request, *args, **kwargs):
        lost_and_found_subcategories = [item.label for item in LOST_AND_FOUND_SUBCATEGORIES]
        return Response({"lost_and_found_subcategories": lost_and_found_subcategories}, status=status.HTTP_200_OK)
