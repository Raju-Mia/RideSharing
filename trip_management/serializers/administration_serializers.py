from rest_framework import serializers
from trip_management.models import BookingFeeSchedule
from rest_framework.exceptions import ValidationError







class BookingFeeScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookingFeeSchedule
        fields = [
            'id', 
            'start_time',
            'end_time',
            'airport_transfer_fee',
            'one_way_fee',
            'round_trip_fee',
            'as_directed_fee',
            'is_active',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def validate(self, data):
        start_time = data.get('start_time')
        end_time = data.get('end_time')

        if not end_time:
            raise serializers.ValidationError({"error": "End time field is required."})
        if not start_time:
            raise serializers.ValidationError({"error": "Start time field is required."})
        
        if start_time and end_time and start_time >= end_time:
            raise serializers.ValidationError({"error": "End time must be after start time."})
        
        overlapping = BookingFeeSchedule.objects.filter(
            is_active=True,
            start_time__lt=end_time,
            end_time__gt=start_time
        )
        
        if self.instance:
            overlapping = overlapping.exclude(pk=self.instance.pk)
            
        if overlapping.exists():
            raise serializers.ValidationError({"error": "This time range overlaps with an existing schedule."})
            
        return data

