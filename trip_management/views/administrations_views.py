from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from trip_management.models import BookingFeeSchedule, TripMethod
from trip_management.serializers.administration_serializers import BookingFeeScheduleSerializer

class BookingFeeScheduleListCreateView(APIView):
    permission_classes = [IsAuthenticated, ]
    
    def get(self, request):
        schedules = BookingFeeSchedule.objects.all().order_by('start_time')
        serializer = BookingFeeScheduleSerializer(schedules, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        """Create a new booking fee schedule"""
        serializer = BookingFeeScheduleSerializer(data=request.data)
        if serializer.is_valid():
            try:
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response(
                    {"error": str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        errors = serializer.errors
        formatted_errors = {field: messages[0] for field, messages in errors.items()}
        
        return Response({"error": formatted_errors}, status=status.HTTP_400_BAD_REQUEST)


class CurrentBookingFee(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get current applicable booking fees"""
        current_fees = {
            'airport_transfer': BookingFeeSchedule.get_current_booking_fee(TripMethod.AIRPORT_TRANSFER),
            'one_way': BookingFeeSchedule.get_current_booking_fee(TripMethod.ONE_WAY),
            'round_trip': BookingFeeSchedule.get_current_booking_fee(TripMethod.ROUND_TRIP),
            'as_directed': BookingFeeSchedule.get_current_booking_fee(TripMethod.AS_DIRECTED)
        }
        return Response(current_fees, status= status.HTTP_200_OK)



class UpdateBookingFeeSchedule(APIView):
    permission_classes = [IsAuthenticated]
    
    def get_object(self, instance_id):
        return get_object_or_404(BookingFeeSchedule, id=instance_id)
        
    def patch(self, request, instance_id):
        """Partially update a booking fee schedule"""
        schedule = self.get_object(instance_id)
        serializer = BookingFeeScheduleSerializer(
            schedule,
            data=request.data,
            partial=True
        )
        if serializer.is_valid():
            try:
                serializer.save()
                return Response(serializer.data)
            except Exception as e:
                return Response(
                    {"error": str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class DeleteBookingFeeSchedule(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, instance_id):
        return get_object_or_404(BookingFeeSchedule, id=instance_id)
    
    def delete(self, request, instance_id):
        """Delete a booking fee schedule"""
        schedule = self.get_object(instance_id)
        schedule.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)









