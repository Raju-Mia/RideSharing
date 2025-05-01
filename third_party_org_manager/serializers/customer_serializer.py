# serializers.py
from rest_framework import serializers
from third_party_org_manager.models import OrganizationCustomer

class OrganizationCustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationCustomer
        fields = '__all__'  # You can also specify specific fields here if needed
