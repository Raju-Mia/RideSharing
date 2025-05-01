from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
import base64

from notification_manager.models import VapidKey
from notification_manager.serializers.setup import VapidKeySerializer

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization

# class GenerateVapidKeyView(APIView):
    
#     '''
#     The API view will generate the keys and store them in the database if they don't already exist.
#     If they already exist, it will return the existing keys.
#     '''
#     def get(self, request, *args, **kwargs):
#         # Check if VAPID keys already exist
#         if VapidKey.objects.exists():
#             vapid_key = VapidKey.objects.first()
#             serializer = VapidKeySerializer(vapid_key)
#             return Response(serializer.data, status=status.HTTP_200_OK)
        
#         # Generate new VAPID keys
#         private_key = ec.generate_private_key(ec.SECP256R1())
#         public_key = private_key.public_key()
        
#         private_key_bytes = private_key.private_bytes(
#             encoding=serialization.Encoding.PEM,
#             format=serialization.PrivateFormat.PKCS8,
#             encryption_algorithm=serialization.NoEncryption(),
#         )
        
#         public_key_bytes = public_key.public_bytes(
#             encoding=serialization.Encoding.X962,
#             format=serialization.PublicFormat.UncompressedPoint,
#         )
        
#         vapid_private_key = base64.urlsafe_b64encode(private_key_bytes).decode('utf-8')
#         vapid_public_key = base64.urlsafe_b64encode(public_key_bytes).decode('utf-8')

#         # Save to database
#         vapid_key = VapidKey.objects.create(
#             public_key=vapid_public_key,
#             private_key=vapid_private_key
#         )
        
#         serializer = VapidKeySerializer(vapid_key)
#         return Response(serializer.data, status=status.HTTP_201_CREATED)





class GenerateVapidKeyView(APIView):
    """
    API view to generate VAPID keys if they don't exist.
    If keys already exist, the existing keys are returned.
    """
    def get(self, request, *args, **kwargs):
        # Check if VAPID keys already exist
        if VapidKey.objects.exists():
            vapid_key = VapidKey.objects.first()
            serializer = VapidKeySerializer(vapid_key)
            return Response(serializer.data, status=status.HTTP_200_OK)

        # Generate new VAPID keys
        private_key = ec.generate_private_key(ec.SECP256R1())
        public_key = private_key.public_key()

        # Serialize private key to PEM format
        private_key_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode("utf-8")  # Decode to a string for database storage

        # Serialize public key to PEM format
        public_key_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode("utf-8")  # Decode to a string for database storage

        # Save to database
        vapid_key = VapidKey.objects.create(
            public_key=public_key_pem,
            private_key=private_key_pem
        )

        # Serialize and return the new keys
        serializer = VapidKeySerializer(vapid_key)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
