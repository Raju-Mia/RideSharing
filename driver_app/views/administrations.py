from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from driver_app.models import Driver, DriverStatus, AttachmentStatus, VehicleStatus, Vehicle,DriverProfileEditRequest
from utils.pagination import CustomPageNumberPagination
from driver_app.serializers import DriverSerializer, VehicleSerializer



class VerifiedDriverList(APIView):
    pagination_class = CustomPageNumberPagination
    
    def get(self, request):
        verified_drivers = Driver.objects.filter(
            status=DriverStatus.verified,
            driving_license_no_status=AttachmentStatus.verified,
            dvla_plastic_driving_licence_status=AttachmentStatus.verified,
            private_hire_driving_licence_status=AttachmentStatus.verified,            
            vehicles__vehicle_reg_no_status=AttachmentStatus.verified,
            vehicles__insurance_certificate_status=AttachmentStatus.verified,
            vehicles__mot_test_certificate_status=AttachmentStatus.verified,
            vehicles__private_hire_vehicle_licence_status=AttachmentStatus.verified,
            vehicles__log_book_V5C_status=AttachmentStatus.verified,
            vehicles__status=VehicleStatus.verified
        ).order_by('-updated_at')
        
        paginator = self.pagination_class()
        paginated_queryset = paginator.paginate_queryset(verified_drivers, request)
        
        driver_list = []
        for driver in paginated_queryset:
            driver_data = {
                'driver_id': str(driver.id),
                'name': f"{driver.user.full_name}",
                'driving_license_number': driver.driving_license_number,
                'picture': driver.user.picture.url if driver.user.picture else None, 
                'phone': driver.user.phone,
                'date_of_birth': driver.date_of_birth,
                'total_trips': 0,
                'earnings': 0.00,
                'ratings': 0.00,
                'driver_validate_date': driver.dvla_plastic_driving_licence_expired_date,
                'address': driver.address,
                'city': driver.city,
                'state': driver.state,
                'vehicle_details': {
                    'registration_number': driver.vehicles.vehicle_registration_number,
                    'color': driver.vehicles.color
                } if hasattr(driver, 'vehicles') else None,
            }
            driver_list.append(driver_data)
        
        return paginator.get_paginated_response(driver_list)
    


class ExpiredDriverList(APIView):
    pagination_class = CustomPageNumberPagination
    
    def get(self, request):
        expired_drivers = Driver.objects.filter(
            Q(driving_license_no_status=AttachmentStatus.expired) |
            Q(dvla_plastic_driving_licence_status=AttachmentStatus.expired) |
            Q(private_hire_driving_licence_status=AttachmentStatus.expired) |
            Q(vehicles__vehicle_reg_no_status=AttachmentStatus.expired) |
            Q(vehicles__insurance_certificate_status=AttachmentStatus.expired) |
            Q(vehicles__mot_test_certificate_status=AttachmentStatus.expired) |
            Q(vehicles__private_hire_vehicle_licence_status=AttachmentStatus.expired) |
            Q(vehicles__log_book_V5C_status=AttachmentStatus.expired)
        ).order_by('-updated_at')
        
        paginator = self.pagination_class()
        paginated_queryset = paginator.paginate_queryset(expired_drivers, request)
        
        driver_list = []
        for driver in paginated_queryset:
            driver_data = {
                'driver_id': str(driver.id),
                'name': f"{driver.user.full_name}",
                'driving_license_number': driver.driving_license_number,
                'picture': driver.user.picture.url if driver.user.picture else None, 
                'phone': driver.user.phone,
                'date_of_birth': driver.date_of_birth,
                'total_trips': 0,
                'earnings': 0.00,
                'ratings': 0.00,
                'driver_validate_date': driver.dvla_plastic_driving_licence_expired_date,
                'address': driver.address,
                'city': driver.city,
                'state': driver.state,
                'vehicle_details': {
                    'registration_number': driver.vehicles.vehicle_registration_number,
                    'color': driver.vehicles.color
                } if hasattr(driver, 'vehicles') else None,
            }
            driver_list.append(driver_data)
        
        return paginator.get_paginated_response(driver_list)


class DocumentResubmittedDriverList(APIView):
    pagination_class = CustomPageNumberPagination
    
    def get(self, request):
        resubmitted_drivers = Driver.objects.filter(
            Q(driving_license_no_status=AttachmentStatus.resubmitted) |
            Q(dvla_plastic_driving_licence_status=AttachmentStatus.resubmitted) |
            Q(private_hire_driving_licence_status=AttachmentStatus.resubmitted) |
            Q(vehicles__vehicle_reg_no_status=AttachmentStatus.resubmitted) |
            Q(vehicles__insurance_certificate_status=AttachmentStatus.resubmitted) |
            Q(vehicles__mot_test_certificate_status=AttachmentStatus.resubmitted) |
            Q(vehicles__private_hire_vehicle_licence_status=AttachmentStatus.resubmitted) |
            Q(vehicles__log_book_V5C_status=AttachmentStatus.resubmitted)
        ).order_by('-updated_at')
        
        paginator = self.pagination_class()
        paginated_queryset = paginator.paginate_queryset(resubmitted_drivers, request)
        
        driver_list = []
        for driver in paginated_queryset:
            driver_data = {
                'driver_id': str(driver.id),
                'name': f"{driver.user.full_name}",
                'driving_license_number': driver.driving_license_number,
                'picture': driver.user.picture.url if driver.user.picture else None, 
                'phone': driver.user.phone,
                'date_of_birth': driver.date_of_birth,
                'total_trips': 0,
                'earnings': 0.00,
                'ratings': 0.00,
                'driver_validate_date': driver.dvla_plastic_driving_licence_expired_date,
                'address': driver.address,
                'city': driver.city,
                'state': driver.state,
                'vehicle_details': {
                    'registration_number': driver.vehicles.vehicle_registration_number,
                    'color': driver.vehicles.color
                } if hasattr(driver, 'vehicles') else None,
            }
            driver_list.append(driver_data)
        
        return paginator.get_paginated_response(driver_list)
    

class DocumentSubmittedDriverList(APIView):
    pagination_class = CustomPageNumberPagination
    
    def get(self, request):
        resubmitted_drivers = Driver.objects.filter(
            Q(driving_license_no_status=AttachmentStatus.submitted) |
            Q(dvla_plastic_driving_licence_status=AttachmentStatus.submitted) |
            Q(private_hire_driving_licence_status=AttachmentStatus.submitted) |
            Q(vehicles__vehicle_reg_no_status=AttachmentStatus.submitted) |
            Q(vehicles__insurance_certificate_status=AttachmentStatus.submitted) |
            Q(vehicles__mot_test_certificate_status=AttachmentStatus.submitted) |
            Q(vehicles__private_hire_vehicle_licence_status=AttachmentStatus.submitted) |
            Q(vehicles__log_book_V5C_status=AttachmentStatus.submitted)
        ).order_by('-updated_at')
        
        paginator = self.pagination_class()
        paginated_queryset = paginator.paginate_queryset(resubmitted_drivers, request)
        
        driver_list = []
        for driver in paginated_queryset:
            driver_data = {
                'driver_id': str(driver.id),
                'name': f"{driver.user.full_name}",
                'driving_license_number': driver.driving_license_number,
                'picture': driver.user.picture.url if driver.user.picture else None, 
                'phone': driver.user.phone,
                'date_of_birth': driver.date_of_birth,
                'total_trips': 0,
                'earnings': 0.00,
                'ratings': 0.00,
                'driver_validate_date': driver.dvla_plastic_driving_licence_expired_date,
                'address': driver.address,
                'city': driver.city,
                'state': driver.state,
                'vehicle_details': {
                    'registration_number': driver.vehicles.vehicle_registration_number,
                    'color': driver.vehicles.color
                } if hasattr(driver, 'vehicles') else None,
            }
            driver_list.append(driver_data)
        
        return paginator.get_paginated_response(driver_list)
    


class DriverVehicleDetail(APIView):
    def get(self, request, driver_id):
        try:
            driver = Driver.objects.get(id=driver_id)
            vehicle = Vehicle.objects.filter(owner=driver).first()

            driver_serializer = DriverSerializer(driver)
            vehicle_serializer = VehicleSerializer(vehicle) if vehicle else None

            data = {
                "driver": driver_serializer.data,
                "vehicle": vehicle_serializer.data if vehicle else None,
            }

            if driver.status != DriverStatus.verified:
                edit_request = DriverProfileEditRequest.objects.filter(user=driver.user).first()
                if edit_request:
                    data["profile_picture_edit_request"] = {
                        "picture": request.build_absolute_uri(edit_request.picture.url) if edit_request.picture else None,
                        "status": edit_request.status,
                        "admin_comment": edit_request.admin_comment,
                    }

            return Response(data, status=status.HTTP_200_OK)

        except Driver.DoesNotExist:
            return Response({"error": "Driver not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        


class DriverVehicleUpdate(APIView):
    def patch(self, request, driver_id):
        return self.update_driver_vehicle(request, driver_id, partial=True)

    def update_driver_vehicle(self, request, driver_id, partial):
        try:
            driver = Driver.objects.get(id=driver_id)
            vehicle = Vehicle.objects.filter(owner=driver).first()
            
            driver_serializer = DriverSerializer(driver, data=request.data.get("driver", {}), partial=partial)
            vehicle_data = request.data.get("vehicle", {})
            vehicle_serializer = None

            if vehicle:
                vehicle_serializer = VehicleSerializer(vehicle, data=vehicle_data, partial=partial)
            elif vehicle_data:
                vehicle_data["owner"] = driver.id
                vehicle_serializer = VehicleSerializer(data=vehicle_data)

            driver_valid = driver_serializer.is_valid()
            vehicle_valid = not vehicle_serializer or vehicle_serializer.is_valid()

            if driver_valid and vehicle_valid:
                driver_serializer.save()
                if vehicle_serializer:
                    vehicle_serializer.save()
                    data = {
                        "driver": driver_serializer.data,
                        "vehicle": vehicle_serializer.data if vehicle_serializer else None,
                    }
                return Response(data, status=status.HTTP_200_OK)
            else:
                errors = {
                    "driver_errors": driver_serializer.errors if not driver_valid else None,
                    "vehicle_errors": vehicle_serializer.errors if vehicle_serializer and not vehicle_valid else None
                }
                return Response(errors, status=status.HTTP_400_BAD_REQUEST)

        except Driver.DoesNotExist:
            return Response({"error": "Driver not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
