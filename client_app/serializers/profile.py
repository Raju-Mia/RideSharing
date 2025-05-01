
# serializers/authentication_serializer.py
from rest_framework import serializers
from accounts.validators import email_validator
import re
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from accounts.models import CustomUser
from django.contrib.auth import get_user_model
User = get_user_model()


#Import
from accounts.models import CustomUser, UserProfile



class ClientProfileUpdateSerializer(serializers.ModelSerializer):
    # Fields from CustomUser
    full_name = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)
    phone = serializers.CharField(required=False)
    whatsappnumber = serializers.CharField(required=False)
    picture = serializers.ImageField(required=False)
    address = serializers.CharField(required=False)

    # Fields from UserProfile
    designation = serializers.CharField(required=False)
    contact = serializers.CharField(required=False)
    date_of_birth = serializers.DateField(required=False, allow_null=True)
    profile_image = serializers.ImageField(required=False)

    class Meta:
        model = CustomUser
        fields = [
            'full_name', 'email', 'phone', 'whatsappnumber', 'picture', 'address',  # CustomUser fields
            'designation', 'contact', 'date_of_birth', 'profile_image'  # UserProfile fields
        ]

    def validate_email(self, value):
        user = self.context['request'].user
        if CustomUser.objects.filter(email=value).exclude(id=user.id).exists():
            raise serializers.ValidationError("This email is already in use.")
        return value

    def validate_phone(self, value):
        user = self.context['request'].user
        if CustomUser.objects.filter(phone=value).exclude(id=user.id).exists():
            raise serializers.ValidationError("This phone number is already registered.")
        return value

    def update(self, instance, validated_data):
        # Update UserProfile fields
        profile_data = {
            'designation': validated_data.pop('designation', None),
            'contact': validated_data.pop('contact', None),
            'date_of_birth': validated_data.pop('date_of_birth', None),
            'profile_image': validated_data.pop('profile_image', None),
        }
        
        # Update fields for CustomUser
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Ensure a UserProfile exists for this user
        user_profile, created = UserProfile.objects.get_or_create(user=instance)

        for attr, value in profile_data.items():
            if value is not None:
                setattr(user_profile, attr, value)
        user_profile.save()

        # Add UserProfile data to the response
        self.fields['date_of_birth'].default = user_profile.date_of_birth

        return instance

    
    


