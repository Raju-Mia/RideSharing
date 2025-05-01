import json
from django.contrib.auth import get_user_model
from django.conf import settings
from django.utils import timezone
import os
from django.db import transaction

from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from rest_framework.response import Response
from rest_framework.views import APIView






from driver_app.models import (
    Driver,DriverProfileEditRequest, Vehicle,
    

)



from driver_app.serializers import (
    DriverDocumentSubmitReSubmitSerializer,
    DriverInfoSerializer,
    DriverDetailsSerializer,
    DriverVehicleDocumentDetailSerializer,
    )

User = get_user_model()



















class DriverRegisterView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        licence_number = request.data.get("drivingLicenceNumber")
        if not licence_number:
            return Response({"error": "Driving Licence Number is required"}, status=status.HTTP_400_BAD_REQUEST)
        file_path = os.path.join(settings.BASE_DIR, "utils", "random_driver_info.txt")
        try:
            with open(file_path, "r") as file:
                drivers_data = json.load(file)

            driver_info = next((driver for driver in drivers_data if driver["driver"]["drivingLicenceNumber"] == licence_number), None)

            if driver_info:
                driver_data = driver_info["driver"]
                first_names = driver_data.get("firstNames", "")
                last_name = driver_data.get("lastName", "")
                gender = driver_data.get("gender", "Male")
                date_of_birth_str = driver_data.get("dateOfBirth", None)

                address_data = driver_data.get("address", {}).get("unstructuredAddress", {})
                address = address_data.get("line1", "")
                city = address_data.get("line5", "")
                postcode = address_data.get("postcode", "")

                # date_of_birth = None
                # if date_of_birth_str:
                #     date_of_birth = datetime.strptime(date_of_birth_str, "%Y-%m-%d").date()

                try:
                    driver = Driver.objects.get(user=user)

                    driver.gender = gender
                    # driver.date_of_birth = date_of_birth
                    driver.address = address
                    driver.city = city
                    driver.postal_code = postcode
                    driver.driving_license_number = licence_number
                    driver.save()

                    user.full_name = f"{first_names} {last_name}".strip()
                    user.save()

                    print(f"Driver Updated: {user.full_name} | DOB: {date_of_birth_str}")

                    return Response({
                        "message": "Driver updated successfully",
                        "driver_id": driver.id,
                        "full_name": user.full_name,
                        "gender": driver.gender,
                        "address": driver.address,
                        "city": driver.city,
                        "postal_code": driver.postal_code,
                        "driving_license_number": driver.driving_license_number
                    }, status=status.HTTP_200_OK)

                except Driver.DoesNotExist:
                    return Response({"error": "Driver not found"}, status=status.HTTP_404_NOT_FOUND)

            else:
                return Response({"error": "Driver not found in file"}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DriverDocumentUploadView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, *args, **kwargs):
        try:
            driver = request.user.driver
            
            if not driver:
                return Response({"error": "No driver profile found for this user."}, status=status.HTTP_400_BAD_REQUEST)

            files_to_check = {
                'dvla_plastic_driving_licence_front': {
                    'status_field': 'dvla_plastic_driving_licence_status',
                    'update_field': 'dvla_plastic_driving_licence_last_update'
                },
                'dvla_plastic_driving_licence_back': {
                    'status_field': 'dvla_plastic_driving_licence_status',
                    'update_field': 'dvla_plastic_driving_licence_last_update'
                },
                'private_hire_driving_licence': {
                    'status_field': 'private_hire_driving_licence_status',
                    'update_field': 'private_hire_driving_licence_last_update'
                }
            }

            for doc_field, fields in files_to_check.items():
                if doc_field in request.FILES:
                    if doc_field in ['dvla_plastic_driving_licence_front', 'dvla_plastic_driving_licence_back']:
                        if driver.dvla_plastic_driving_licence_front or driver.dvla_plastic_driving_licence_back:
                            setattr(driver, fields['status_field'], 'resubmitted')
                        else:
                            setattr(driver, fields['status_field'], 'submitted')
                    else:
                        if getattr(driver, doc_field):
                            setattr(driver, fields['status_field'], 'resubmitted')
                        else:
                            setattr(driver, fields['status_field'], 'submitted')

                    setattr(driver, fields['update_field'], timezone.now().date())

            serializer = DriverDocumentSubmitReSubmitSerializer(driver, data=request.data, partial=True)

            if serializer.is_valid():
                with transaction.atomic():
                    serializer.save()

                return Response({"message": "Documents uploaded successfully.", "data": serializer.data}, status=status.HTTP_200_OK)

            return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        except AttributeError:
            return Response({"error": "User is not associated with a driver."}, status=status.HTTP_403_FORBIDDEN)

        except Exception as e:
            return Response({"error": f"An unexpected error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




class DriverDocumentStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            driver = Driver.objects.get(user=request.user)
            
            # Get the last edit request for the user
            last_edit_request = DriverProfileEditRequest.objects.filter(user=request.user).order_by('-created_at').first()
            profile_picture_status = last_edit_request.status if last_edit_request else "required"

            return Response({
                "dvla_plastic_driving_licence_status": driver.dvla_plastic_driving_licence_status,
                "driving_license_no_status": driver.driving_license_no_status,
                "private_hire_driving_licence_status": driver.private_hire_driving_licence_status,
                "profile_picture_status": profile_picture_status
            }, status=status.HTTP_200_OK)

        except Driver.DoesNotExist:
            return Response({"error": "Driver not found"}, status=status.HTTP_404_NOT_FOUND)
        
class UpdateDriverRegNoStatus(APIView):
    permission_classes = [IsAuthenticated]
    def patch(self, request, *args, **kwargs):
        try:
            driver = request.user.driver                        
            driver.driving_license_no_status = "verified"
            driver.save()
            return Response({"message": "Driver registration number verified."}, status=status.HTTP_200_OK)
        except AttributeError:
            return Response({"error": "Driver profile not found for the user."}, status=status.HTTP_400_BAD_REQUEST)
class DriverInfo(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            driver = get_object_or_404(Driver, user=request.user)
            
            serializer = DriverInfoSerializer(driver)
            
            return Response({
                'status': 'success',
                'message': 'Driver basic details retrieved successfully',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
class DriverDetailsAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            driver = get_object_or_404(Driver, user=request.user)
            print(driver.id)
            
            serializer = DriverDetailsSerializer(driver)
            
            return Response({
                'status': 'success',
                'message': 'Driver details retrieved successfully',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
class LastProfilePictureEditRequestStatus(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            last_edit_request = DriverProfileEditRequest.objects.filter(user=request.user).order_by('-created_at').first()
            
            if not last_edit_request:
                data = {
                'status': 'required',
            }
                return Response({"data":data}, status=status.HTTP_200_OK)

            data = {
                'id': last_edit_request.id,
                'picture': request.build_absolute_uri(last_edit_request.picture.url) if last_edit_request.picture else None,
                'status': last_edit_request.status,
                'admin_comment': last_edit_request.admin_comment,
                'created_at': last_edit_request.created_at
            }
            
            return Response({
                'status': 'success',
                'message': 'Last profile picture edit request retrieved successfully',
                'data': data
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)






class DriverVehicleInfoAPIView(APIView):
    permission_classes = [IsAuthenticated]
    

    def get(self, request, *args, **kwargs):
        try:
            driver = request.user.driver  # Get the driver linked to the authenticated user
            vehicle = Vehicle.objects.filter(owner=driver).first()  # Fetch the driver's vehicle

            if not vehicle:
                return Response({"error": "No vehicle found for this driver."}, status=status.HTTP_404_NOT_FOUND)

            data = {
                "driver": driver,
                "vehicle": vehicle
            }
            serializer = DriverVehicleDocumentDetailSerializer(data)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except AttributeError:
            return Response({"error": "User is not associated with a driver."}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            return Response({"error": f"An unexpected error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
