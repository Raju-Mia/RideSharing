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



class ComplaintPictureSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComplaintPicture
        fields = ['id', 'picture']


class RemarkSerializer(serializers.ModelSerializer):
    remark_by_name = serializers.CharField(source='remark_by.full_name', read_only=True)
    remark_by_id = serializers.UUIDField(source='remark_by.id', read_only=True)
    complaint_id  = serializers.UUIDField(source='complaint.id', required=True)

    class Meta:
        model = Remark
        fields = ['id', 'remark', 'complaint_box_status', 'remark_by_name','remark_by_id','complaint_id', 'created_at']



class AdministratorComplaintDetailSerializer(serializers.ModelSerializer):
    complaint_pictures = ComplaintPictureSerializer(many=True, read_only=True)
    remarks = RemarkSerializer(many=True, read_only=True)
    trip_id = serializers.UUIDField(source='trip.id', allow_null=True)

    class Meta:
        model = ComplaintBox
        fields = [
            'case_id','trip_id', 'pickup_date', 'dropoff_date',
            'pickup_location', 'dropoff_location', 'author_name',
            'author_phone', 'author_email', 'services', 'complaint_title',
            'title_subcategory', 'description', 'complaint_status',
            'created_at', 'updated_at', 'complaint_pictures', 'remarks',
             
        ]


class AdministratorComplaintRemarkSerializer(serializers.ModelSerializer):
    remark_by = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = Remark
        fields = ['id', 'complaint', 'remark_by', 'remark', 'complaint_box_status', 'created_at']
        read_only_fields = ['id', 'remark_by', 'created_at', 'complaint']

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user:
            validated_data['remark_by'] = request.user
        return super().create(validated_data)