from rest_framework import serializers, generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.permissions import IsAdminUser
from django.utils.timezone import now
from utils.pagination import CustomPageNumberPagination
from rest_framework.generics import ListAPIView, RetrieveUpdateDestroyAPIView

# Import
from subscription_management.models import Coupon
from subscription_management.serializers import CouponSerializer


# Coupon CRUD Views
class CouponListCreateView(generics.ListCreateAPIView):
    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPageNumberPagination

class CouponRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPageNumberPagination

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({"message": "Coupon deleted successfully"}, status=status.HTTP_200_OK)
