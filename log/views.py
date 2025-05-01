# from rest_framework import status
# from rest_framework.response import Response
# from rest_framework.views import APIView
# from rest_framework.generics import ListAPIView, get_object_or_404
# from rest_framework.pagination import LimitOffsetPagination
# from uc_admin.permissions import IsAdmin
# from .serializers import (
#     # DetailOfTripHistory,
#     # DetailVehicleAssign,
#     DetailsOfDriverHistory,
#     DetailsOfVehicleHistory,
#     VehicleHistorySerializer,
#     DriverHistorySerializer,
#     TripHistorySerializer,
#     VehicleAssignSerializer,
# )
# from accounts.models import Vehicle, Driver
# from contact.models import ComplaintBox
# from trip_management.models import Trip

# KwargsToModel = {
#     "vehicle": [Vehicle, VehicleHistorySerializer],
#     "driver": [Driver, DriverHistorySerializer],
#     "trip": [Trip, TripHistorySerializer],
#     "driver_assignment": [VehicleAssignWaitingList, VehicleAssignSerializer],
#     "complaint": [ComplaintBox, DriverHistorySerializer],
# }

# kwargsToModelDetails = {
#     "vehicle": [Vehicle, DetailsOfVehicleHistory],
#     "driver": [Driver, DetailsOfDriverHistory],
#     "trip": [Trip, DetailOfTripHistory],
#     "driver_assignment": [VehicleAssignWaitingList, DetailVehicleAssign],
# }


# class History(ListAPIView):
#     def get_queryset(self):
#         return self.model.history.only(
#             "history_date", "history_type", "id", "history_user", "history_id"
#         )


# class VehicleHistory(History):
#     serializer_class = VehicleHistorySerializer
#     model = Vehicle


# class ModelHistory(APIView, LimitOffsetPagination):
#     permission_classes = [IsAdmin]

#     def get(self, request, model):
#         try:
#             model, serializer_class = (
#                 KwargsToModel[model][0],
#                 KwargsToModel[model][1],
#             )
#         except KeyError:
#             return Response(status=status.HTTP_400_BAD_REQUEST)
#         histories = model.history.only(
#             "history_date", "history_type", "id", "history_user", "history_id"
#         )
#         results = self.paginate_queryset(histories, request, view=self)
#         serializer = serializer_class(results, many=True)
#         return self.get_paginated_response(serializer.data)


# class HistoryOfSpecificObject(APIView, LimitOffsetPagination):
#     permission_classes = [IsAdmin]

#     def get(self, request, model, object_id):
#         try:
#             model, serializer_class = (
#                 KwargsToModel[model][0],
#                 KwargsToModel[model][1],
#             )
#         except KeyError:
#             return Response(status=status.HTTP_400_BAD_REQUEST)
#         object = get_object_or_404(model, id=object_id)
#         print(object.history)

#         histories = object.history.only(
#             "history_date", "history_type", "id", "history_user", "history_id"
#         )
#         results = self.paginate_queryset(histories, request, view=self)
#         serializer = serializer_class(results, many=True)
#         return self.get_paginated_response(serializer.data)


# class HistoryDetails(APIView):
#     permission_classes = [IsAdmin]

#     def get(self, request, model, history_id):
#         try:
#             model, serializer_class = (
#                 kwargsToModelDetails[model][0],
#                 kwargsToModelDetails[model][1],
#             )
#         except KeyError:
#             return Response(status=status.HTTP_400_BAD_REQUEST)
#         history = model.history.get(history_id=history_id)
#         serializer = serializer_class(history)
#         return Response(serializer.data, status=status.HTTP_200_OK)
