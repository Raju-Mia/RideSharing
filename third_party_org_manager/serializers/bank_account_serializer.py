from rest_framework import serializers
from organization_manager.models import OrganizationBankAccount

class OrganizationBankAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationBankAccount
        fields = '__all__'
        read_only_fields = ('id', 'organization', 'created_at', 'updated_at')
