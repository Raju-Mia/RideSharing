from rest_framework import serializers, generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.permissions import IsAdminUser
from django.utils.timezone import now
from utils.pagination import CustomPageNumberPagination
from rest_framework.generics import ListAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.views import APIView

# Import
from subscription_management.models import SubscriptionPlan
from subscription_management.serializers import SubscriptionPlanSerializer


# SubscriptionPlan CRUD Views
# class SubscriptionPlanListCreateView(generics.ListCreateAPIView):
#     queryset = SubscriptionPlan.objects.all()
#     serializer_class = SubscriptionPlanSerializer
#     permission_classes = [IsAuthenticated]
#     pagination_class = CustomPageNumberPagination


# class SubscriptionPlanListCreateView(generics.ListCreateAPIView):
#     queryset = SubscriptionPlan.objects.filter().order_by('yearly_price')
#     serializer_class = SubscriptionPlanSerializer
#     # permission_classes = [IsAuthenticated]

class SubscriptionPlanListCreateView(generics.ListCreateAPIView):
    queryset = SubscriptionPlan.objects.filter().order_by('yearly_price')
    serializer_class = SubscriptionPlanSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({'request': self.request})  # make sure request is available in serializer
        return context


class SubscriptionPlanRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    queryset = SubscriptionPlan.objects.all()
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPageNumberPagination

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({"message": "subscription plan deleted successfully"}, status=status.HTTP_200_OK)



# ✅ New API to Calculate Subscription Plan Prices based on base_price
class SubscriptionPriceCalculationAPIView(APIView):
    """
    When the user provides only the base_price (1-day price),
    this API calculates and returns all the subscription durations' prices.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        base_price = request.data.get("base_price", None)

        if base_price is None:
            return Response({"error": "Base price is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            base_price = float(base_price)
        except ValueError:
            return Response({"error": "Base price must be a valid number."}, status=status.HTTP_400_BAD_REQUEST)

        # Duration-wise Calculation
        duration_prices = {
            "weekly_price": round(base_price * 7, 2),
            "bi_weekly_price": round(base_price * 14, 2),
            "monthly_price": round(base_price * 30, 2),
            "quarterly_price": round(base_price * 90, 2),
            "half_yearly_price": round(base_price * 182, 2),
            "yearly_price": round(base_price * 365, 2),
        }

        return Response({"base_price": base_price, "calculated_prices": duration_prices}, status=status.HTTP_200_OK)