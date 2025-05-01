from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework import serializers, status, permissions
from rest_framework.generics import (
    get_object_or_404,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from utils.pagination import CustomPageNumberPagination
from django.shortcuts import get_object_or_404

from driver_app.models import (
    ServiceType,
    VehicleModel,

)
from uc_admin.serializers.service_pricing_serializers import (
    VehicleModelSerializer,
    VehicleModelSerializerForUpdate,
    ServiceTypeSerializer,

)

User = get_user_model()




    

class ServiceLocationWisePackagePrice(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = VehicleModelSerializer
    pagination_class = CustomPageNumberPagination

    def get(self, request, *args, **kwargs):
        vehicle_id = kwargs.get("id")
        if vehicle_id:
            vehicle_model = get_object_or_404(VehicleModel, id=vehicle_id)
            serializer = self.serializer_class(vehicle_model)
            return Response(serializer.data, status=status.HTTP_200_OK)

        queryset = VehicleModel.objects.all().order_by("-created_at")

        search_query = request.query_params.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(service_type__icontains=search_query) |
                Q(model__icontains=search_query) |
                Q(manufacturer__icontains=search_query)
            )

        service_type_filter = request.query_params.get('service_type_filter')
        if service_type_filter:
            if service_type_filter.lower() == "assigned":
                queryset = queryset.exclude(service_type__isnull=True).exclude(service_type="")
            elif service_type_filter.lower() == "unassigned":
                queryset = queryset.filter(Q(service_type__isnull=True) | Q(service_type=""))

        service_type = request.query_params.get('service_type')
        if service_type:
            queryset = queryset.filter(service_type__iexact=service_type)

        sort_order = request.query_params.get('sort_by_year_of_manufacture', 'desc').lower()
        if sort_order == "asc":
            queryset = queryset.order_by("year_of_manufacture")
        else:
            queryset = queryset.order_by("-year_of_manufacture")

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)

        if page is not None:
            serializer = self.serializer_class(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, *args, **kwargs):
        vehicle_id = kwargs.get("id")
        if not vehicle_id:
            return Response({"message": "ID not provided."}, status=status.HTTP_400_BAD_REQUEST)

        vehicle_model = get_object_or_404(VehicleModel, id=vehicle_id)
        serializer = VehicleModelSerializerForUpdate(vehicle_model, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        vehicle_id = kwargs.get("id")
        if not vehicle_id:
            return Response({"message": "ID not provided."}, status=status.HTTP_400_BAD_REQUEST)

        vehicle_model = get_object_or_404(VehicleModel, id=vehicle_id)
        vehicle_model.delete()
        return Response({"message": "Vehicle Model deleted successfully."}, status=status.HTTP_200_OK)
    



class ServiceTypeWisePrice(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ServiceTypeSerializer
    pagination_class = CustomPageNumberPagination

    def get(self, request, *args, **kwargs):
        service_id = kwargs.get("id")
        if service_id:
            service_type = get_object_or_404(ServiceType, id=service_id)
            serializer = self.serializer_class(service_type)
            return Response(serializer.data, status=status.HTTP_200_OK)

        queryset = ServiceType.objects.all().order_by("-created_at")

        search_query = request.query_params.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(service_type__icontains=search_query)
            )
        service_type = request.query_params.get('service_type')
        if service_type:
            queryset = queryset.filter(vehicle_type__iexact=service_type)

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)

        if page is not None:
            serializer = self.serializer_class(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        service_type = request.data.get("service_type", "").upper()
        if ServiceType.objects.filter(service_type=service_type).exists():
            return Response(
                {"message": "Service type already exists."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, *args, **kwargs):
        service_id = kwargs.get("id")
        if not service_id:
            return Response({"message": "ID not provided."}, status=status.HTTP_400_BAD_REQUEST)

        service_type = get_object_or_404(ServiceType, id=service_id)
        new_service_type = request.data.get("service_type", "").upper()

        if new_service_type and new_service_type != service_type.service_type:
            if ServiceType.objects.filter(service_type=new_service_type).exists():
                return Response(
                    {"message": "Service type already exists."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

        serializer = self.serializer_class(service_type, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        service_id = kwargs.get("id")
        if not service_id:
            return Response({"message": "ID not provided."}, status=status.HTTP_400_BAD_REQUEST)

        service_type = get_object_or_404(ServiceType, id=service_id)
        service_type.delete()
        return Response({"message": "Service Type deleted successfully."}, status=status.HTTP_200_OK)
