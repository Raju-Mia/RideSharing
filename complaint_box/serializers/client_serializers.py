from rest_framework import serializers
from complaint_box.models import ComplaintBox, ComplaintPicture, Remark
from trip_management.models import Trip


class ComplaintBoxSerializer(serializers.ModelSerializer):
    trip = serializers.PrimaryKeyRelatedField(
        queryset=Trip.objects.all(), allow_null=True, required=False
    )
    class Meta:
        model = ComplaintBox
        fields = '__all__'


class TripSerializer(serializers.ModelSerializer):
    dropoff_location_name = serializers.SerializerMethodField()
    dropoff_time = serializers.SerializerMethodField()
    class Meta:
        model = Trip
        fields = [
            'id','unique_id','pickup_time',
            'pickup_location_name', 'dropoff_location_name', 'dropoff_time',
        ]

    def get_dropoff_location_name(self, obj):
        return obj.final_dropoff_location_name or obj.initial_dropoff_location_name
    
    def get_dropoff_time(self, obj):
        return obj.final_dropoff_time or obj.initial_dropoff_time




class ComplaintPictureSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComplaintPicture
        fields = ['id', 'picture']


class RemarkSerializer(serializers.ModelSerializer):
    remark_by_name = serializers.CharField(source='remark_by.full_name', read_only=True)

    class Meta:
        model = Remark
        fields = ['id', 'remark', 'complaint_box_status', 'remark_by_name', 'created_at']



class ComplaintBoxDetailSerializer(serializers.ModelSerializer):
    complaint_pictures = ComplaintPictureSerializer(many=True, read_only=True)
    remarks = RemarkSerializer(many=True, read_only=True)

    class Meta:
        model = ComplaintBox
        fields = [
            'case_id', 'pickup_date', 'dropoff_date',
            'pickup_location', 'dropoff_location', 'author_name',
            'author_phone', 'author_email', 'services', 'complaint_title',
            'title_subcategory', 'description', 'complaint_status',
            'created_at', 'updated_at', 'complaint_pictures', 'remarks',
        ]
