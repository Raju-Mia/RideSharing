from rest_framework import serializers
from accounts.validators import email_validator

from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from accounts.models import CustomUser



from django.contrib.auth import get_user_model
User = get_user_model()

#Import
from organization_manager.models import Organization
from accounts.models import CustomUser, UserProfile




class OrganizationListSerializer(serializers.ModelSerializer):
    admin_full_name = serializers.CharField(source='admin_user.full_name', read_only=True)
    admin_designation = serializers.SerializerMethodField()
    admin_contact = serializers.SerializerMethodField()

    def get_admin_designation(self, obj):
        if hasattr(obj.admin_user, 'profile'):
            return obj.admin_user.profile.designation
        return None

    def get_admin_contact(self, obj):
        if hasattr(obj.admin_user, 'profile'):
            return obj.admin_user.profile.contact
        return None

    class Meta:
        model = Organization
        fields = [
            'id',
            'name',
            'email',
            'phone_number',
            'whatsapp_number',
            'address_line1',
            'admin_full_name', 
            'admin_designation',   
            'admin_contact'
        ]





class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['designation', 'contact']


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ['name', 'email', 'phone_number', 'address_line1']  # Adjust fields as needed


class OrganizationRegisterSerializer(serializers.Serializer):
    organization_name = serializers.CharField(max_length=255)
    organization_email = serializers.EmailField()
    organization_phone = serializers.CharField(max_length=20)
    organization_address = serializers.CharField(max_length=255)

    user_full_name = serializers.CharField(max_length=500)
    username = serializers.CharField(max_length=150)
    user_password = serializers.CharField(write_only=True)
    user_profile_designation = serializers.CharField(max_length=255)

    def validate(self, data):
        # Check if the organization Email is already registered
        if Organization.objects.filter(email=data['organization_email']).exists():
            raise serializers.ValidationError({"organization_email": "This organization email is already registered."})

        # Check if the organization name is already taken
        if Organization.objects.filter(name=data['organization_name']).exists():
            raise serializers.ValidationError({"organization_name": "This organization name is already registered."})

        # Check if the organization phone number is already registered
        if Organization.objects.filter(phone_number=data['organization_phone']).exists():
            raise serializers.ValidationError({"organization_phone": "This organization phone number is already registered."})

        # Check if the username is already taken
        if CustomUser.objects.filter(username=data['username']).exists():
            raise serializers.ValidationError({"username": "This username is already taken."})

        # Check if the email is already registered
        if CustomUser.objects.filter(email=data['organization_email']).exists():
            raise serializers.ValidationError({"email": "This email is already registered."})

        return data

    def create(self, validated_data):
        # Create Organization
        organization = Organization.objects.create(
            name=validated_data['organization_name'],
            email=validated_data['organization_email'],
            phone_number=validated_data['organization_phone'],
            whatsapp_number=validated_data['organization_phone'],
            address_line1=validated_data['organization_address']
        )

        # Create User
        user = CustomUser.objects.create_user(
            username=validated_data['username'],
            email=validated_data['organization_email'],  # Use organization email for user
            phone=validated_data['organization_phone'],  # Use organization phone for user
            full_name=validated_data['user_full_name'],
            password=validated_data['user_password']
        )
        
        
        # Assigne organiztgion in user
        user.organization = organization
        user.is_organization_admin = True
        
        # When UC Org will create then automatically user will verify! No need any verification.
        user.is_active = True
        user.email_is_verified = True
        user.user_is_verified = True
        user.save()
        

        

        # Assign user as admin of the organization
        organization.admin_user = user
        organization.is_main_org = True
        organization.save()

        # Create UserProfile
        user_profile = UserProfile.objects.create(
            user=user,
            designation=validated_data['user_profile_designation'],
            contact=validated_data['organization_phone']  # UserProfile contact is same as organization phone
        )

        return {
            'organization': organization,
            'user': user,
            'user_profile': user_profile
        }






class OrganizationUpdatedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = [
            'picture',
            'name', 
            'email', 
            'phone_number', 
            'whatsapp_number', 
            'website', 
            'address_line1', 
            'address_line2',
            'city',
            'state',
            'country',
            'postal_code',
            'description'
            ] 
        
        
        
class OrganizationChangePasswordForUserSerializer(serializers.Serializer):
    new_password = serializers.CharField(required=True)

    def validate_new_password(self, value):
        # Validate the new password using Django's built-in validators
        validate_password(value)
        return value

