
# serializers/authentication_serializer.py
from rest_framework import serializers
from rest_framework import serializers
from accounts.validators import email_validator
import re
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from accounts.models import CustomUser


from accounts.models import CustomUser
from django.contrib.auth import get_user_model
User = get_user_model()

#Import
from organization_manager.models import Organization
from accounts.models import CustomUser, UserProfile





class ThirdPartyUserLoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(style={'input_type': 'password'})




# ========= Third Party organization Register serializer=================
class ThirdPartyOrganizationRegisterSerializer(serializers.Serializer):
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





#
class ThirdPartyOrganizationMailOtpVerificationSerializer(serializers.Serializer):
    user_id = serializers.UUIDField()
    verification_otp = serializers.CharField(max_length=6)

    class Meta:
        fields = ["user_id","verification_otp"]











class ThirdPartyOrganizationProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = [
            'name', 'email', 'description', 'phone_number', 'whatsapp_number', 
            'website', 'address_line1', 'address_line2', 'city', 'state', 
            'country', 'postal_code', 'picture'
        ]

    def update(self, instance, validated_data):
        admin_user = instance.admin_user
        
        # If the email is updated, also update the admin user's email
        # new_email = validated_data.get('email', None)
        new_phone = validated_data.get('phone_number', None)
        
        # print(" phone is : ", new_phone)

        # if new_email and admin_user:
        #     admin_user.email = new_email
        #     admin_user.save()

        # If the phone number is updated, also update the admin user's phone number
        if new_phone and admin_user:
            admin_user.phone = new_phone
            admin_user.save()

        # Update the organization instance with the validated data
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance




class ThirdPartyOrganizationCommissionSetSerializer(serializers.ModelSerializer):
    org_commission = serializers.DecimalField(max_digits=5, decimal_places=2, required=True)

    class Meta:
        model = Organization
        fields = [
            'org_commission',
        ]


    
# class ThirdPartyUserListSerializer(serializers.ModelSerializer):
#     name = serializers.CharField(source='full_name')
#     number = serializers.CharField(source='phone')
#     designation = serializers.CharField(source='profile.designation', allow_null=True)
#     profile_image = serializers.CharField(source='profile.profile_image', allow_null=True)

#     class Meta:
#         model = CustomUser
#         fields = ['id', 'name', 'username', 'email', 'number', 'designation', 'profile_image']

#     def to_representation(self, instance):
#         # Get the default representation
#         representation = super().to_representation(instance)

#         # Conditionally add 'is_organization_admin' if it's True
#         if instance.is_organization_admin:
#             representation['is_organization_admin'] = instance.is_organization_admin

#         return representation




# class ThirdPartyUserListSerializer(serializers.ModelSerializer):
#     name = serializers.CharField(source='full_name')
#     number = serializers.CharField(source='phone')
#     designation = serializers.CharField(source='profile.designation', allow_null=True)
#     profile_image = serializers.FileField(source='profile.profile_image', allow_null=True)

#     class Meta:
#         model = CustomUser
#         fields = ['id', 'name', 'username', 'email', 'number', 'designation', 'profile_image']



class ThirdPartyUserListSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='full_name')
    number = serializers.CharField(source='phone')
    
    designation = serializers.SerializerMethodField()
    profile_image = serializers.SerializerMethodField()

    class Meta:
        model = User  # Assuming this is your CustomUser model
        fields = [
            "id",
            "username",
            "email",
            "name",
            "number",
            "address",
            "is_active",
            "email_is_verified",
            "designation",  # Added field
            "profile_image",  # Added field
        ]

    def get_designation(self, obj):
        # Check if the user has a profile and return the designation
        if hasattr(obj, 'profile') and obj.profile.designation:
            return obj.profile.designation
        return None

    def get_profile_image(self, obj):
        # Check if the user has a profile and return the profile image URL
        if hasattr(obj, 'profile') and obj.profile.profile_image:
            return obj.profile.profile_image.url if obj.profile.profile_image else None
        return None






class ThirdPartyUserRegistrationSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='first_name')
    number = serializers.CharField()
    designation = serializers.CharField()
    profile_image = serializers.ImageField(required=False)  # Add profile_image field

    class Meta:
        model = CustomUser
        fields = ['full_name', 'username', 'email', 'number', 'designation', 'password', 'profile_image']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def validate(self, data):
        # Validate phone number uniqueness
        if CustomUser.objects.filter(phone=data['number']).exists():
            raise serializers.ValidationError({"number": "This phone number is already registered."})

        # Validate username uniqueness
        if CustomUser.objects.filter(username=data['username']).exists():
            raise serializers.ValidationError({"username": "This username is already taken."})

        # Validate email uniqueness
        if CustomUser.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError({"email": "This email is already registered."})

        return data

    def create(self, validated_data):
        # Extract User fields
        first_name = validated_data.pop('first_name')
        username = validated_data['username']
        email = validated_data['email']
        password = validated_data['password']

        # Extract Profile fields
        number = validated_data.pop('number')
        designation = validated_data.pop('designation')
        profile_image = validated_data.pop('profile_image', None)
        
        # print("profile_image", profile_image)
        
        # Get the organization from the authenticated user
        organization = self.context['request'].user.organization

        # Create the user
        user = CustomUser.objects.create_user(
            full_name=first_name,
            username=username,
            email=email,
            phone=number,
            password=password,
            organization=organization  # Automatically assign the organization
        )
        
        # When Org will create then automatically user will verify! No need any verification.
        user.is_active = True
        user.email_is_verified = True
        user.user_is_verified = True
        user.save()
            

        # Create the user's profile
        UserProfile.objects.create(
            user=user,
            contact=number,
            designation=designation,
            profile_image=profile_image  # Set profile_image if provided
        )

        return user








class ThirdPartyOperatorProfileUpdateSerializer(serializers.ModelSerializer):
    # Fields for CustomUser model
    full_name = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)
    phone = serializers.CharField(required=False)
    whatsappnumber = serializers.CharField(required=False)
    picture = serializers.ImageField(required=False)
    
    # Fields for UserProfile model
    designation = serializers.CharField(required=False)
    contact = serializers.CharField(required=False)
    address = serializers.CharField(required=False)
    date_of_birth = serializers.DateField(required=False, allow_null=True)
    profile_image = serializers.ImageField(required=False)

    class Meta:
        model = CustomUser
        fields = [
            'username', 'full_name', 'email', 'phone', 'whatsappnumber', 'picture',  # CustomUser fields
            'designation', 'contact', 'address', 'date_of_birth', 'profile_image'  # UserProfile fields
        ]

    def validate_email(self, value):
        user = self.context['request'].user
        if CustomUser.objects.filter(email=value).exclude(id=user.id).exists():
            raise serializers.ValidationError("This email is already in use.")
        return value
    
    
    def validate_username(self, value):
        user = self.context['request'].user
        if CustomUser.objects.filter(username=value).exclude(id=user.id).exists():
            raise serializers.ValidationError("This username is already taken.")
        return value

    def validate_phone(self, value):
        user = self.context['request'].user
        if CustomUser.objects.filter(phone=value).exclude(id=user.id).exists():
            raise serializers.ValidationError("This phone number is already registered.")
        return value

    
    
    def update(self, instance, validated_data):
        # Update fields in CustomUser model
        instance.username = validated_data.get('username', instance.username)
        instance.full_name = validated_data.get('full_name', instance.full_name)
        instance.email = validated_data.get('email', instance.email)
        instance.phone = validated_data.get('phone', instance.phone)
        instance.whatsappnumber = validated_data.get('whatsappnumber', instance.whatsappnumber)
        instance.picture = validated_data.get('picture', instance.picture)
        instance.save()
        
        
        
        
        # Access profile image from request and check if it's not None
        profile_image = validated_data.get('profile_image')
        if profile_image:
            print("Profile image is not None, saving the image.")
        else:
            print("Profile image is None, skipping save.")
        
        # Update related UserProfile
        profile_data = validated_data
        user_profile = instance.profile  # Assuming the user has a related profile
        user_profile.designation = profile_data.get('designation', user_profile.designation)
        user_profile.contact = profile_data.get('contact', user_profile.contact)
        user_profile.address = profile_data.get('address', user_profile.address)
        user_profile.date_of_birth = profile_data.get('date_of_birth', user_profile.date_of_birth)
        user_profile.profile_image = profile_data.get('profile_image', user_profile.profile_image)

        # Only update profile_image if it's provided
        if profile_image is not None:
            user_profile.profile_image = profile_image

        user_profile.save()
        return instance






class ThirdPartyOperatorProfileRetrieveSerializer(serializers.ModelSerializer):
    designation = serializers.CharField(source='profile.designation', required=False)
    contact = serializers.CharField(source='profile.contact', required=False)
    address = serializers.CharField(source='profile.address', required=False)
    date_of_birth = serializers.DateField(source='profile.date_of_birth', required=False)
    profile_image = serializers.FileField(source='profile.profile_image', required=False)

    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'full_name', 'email', 'phone', 'whatsappnumber', 'picture',
            'designation', 'contact', 'address', 'date_of_birth', 'profile_image'
        ]





# 3rd Party Organization User Password Change Serializer
# class ThirdPartyChangePasswordSerializer(serializers.Serializer):
#     old_password = serializers.CharField(required=True)
#     new_password = serializers.CharField(required=True)

#     def validate_new_password(self, value):
#         # Validate the new password using Django's built-in validators
#         validate_password(value)
#         return value



class ThirdPartyChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def validate_new_password(self, value):
        # Validate the new password using Django's built-in validators
        validate_password(value)

        # Custom validation: Check for at least one special character
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
            raise serializers.ValidationError("The password must contain at least one special character.")
        
        return value
    
    
    

class ThirdPartyOrganizationUserChangePasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(required=True)

    # def validate_new_password(self, value):
    #     # Validate the new password using Django's built-in validators
    #     validate_password(value)
    #     return value

    def validate_new_password(self, value):
        # Validate the new password using Django's built-in validators
        validate_password(value)

        # Custom validation: Check for at least one special character
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
            raise serializers.ValidationError("The password must contain at least one special character.")
        
        return value