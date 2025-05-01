# import json
# import uuid

# from django.contrib.auth import get_user_model
# from django.core.files.uploadedfile import SimpleUploadedFile
# from django.test import Client, TestCase
# from django.urls import reverse
# from PIL import Image
# from rest_framework.test import APIClient, APITestCase

# from accounts import models
# # from accounts.models import Admin, CustomUser, Driver, Vehicle
# from accounts.tests.test_helpers import create_n_saved_addresses

# user_model = get_user_model()


# def create_users(num_of_user=1, email=None):
#     users = []
#     if email is not None:
#         user = user_model.objects.create(
#             first_name=f"First_name",
#             last_name=f"last_name",
#             phone="+441234567890",
#             address="dhaka",
#             email=email,
#         )
#         user.set_password("123Password")
#         user.save()
#         return user
#     for _ in range(num_of_user):
#         user = user_model.objects.create(
#             first_name=f"First_name",
#             last_name=f"last_name",
#             phone="+441234567890",
#             address="dhaka",
#             email=str(uuid.uuid4()) + "@gmail.com",
#         )
#         user.set_password("123Password")
#         user.save()
#         users.append(user)
#     return users


# # def create_trips(number_of_trips):
# #     users = create_users(number_of_trips)
# #     trips = []
# #     for c in range(number_of_trips):
# #         trips.append(Trip.objects.create(
# #             date='2020-4-12', user=users[c], booking_method='hourly', pickup_location='dhaka',
# #             pickup_time='13:23', drop_off_location='chittagong', number_of_passengers=5, payment_status='paid'
# #         ))
# #     return users, trips


# def create_driver(num):
#     users = create_users(num)
#     img = Image.new("RGB", (250, 250))
#     image = img.tobytes()
#     drivers = []
#     for c in range(num):
#         driver = Driver.objects.create(
#             user=users[c],
#             driving_license_front_image=image,
#             driving_license_back_image=image,
#             national_insurance="1224",
#             is_condemned_prior=False,
#             status="Verified",
#             is_verified=True,
#         )
#         drivers.append(driver)
#     return drivers


# def create_vehicles(num):
#     drivers = create_driver(num)
#     img = Image.new("RGB", (250, 250))
#     image = img.tobytes()
#     vehicles = []
#     for c in range(num):
#         vehicle = Vehicle.objects.create(
#             manufacturer="test",
#             vehicle_class="test",
#             mot=image,
#             has_child_seat=True,
#             maximum_passengers=8,
#             luggage_capacity="Small",
#             vehicle_type="Lux",
#             vehicle_registration_number="54654153153",
#             bluebook=image,
#             vehicle_insurance=image,
#             # vehicle_left_image=image,
#             # vehicle_right_image=image,
#             vehicle_front_image=image,
#         )
#         vehicles.append(vehicle)
#     return vehicles


# def create_vehicle(driver):
#     img = Image.new("RGB", (250, 250))
#     image = img.tobytes()
#     vehicle = Vehicle.objects.create(
#         manufacturer="test",
#         vehicle_class="test",
#         mot=image,
#         has_child_seat=True,
#         maximum_passengers=4,
#         luggage_capacity="Small",
#         vehicle_type="Lux",
#         vehicle_registration_number="54654153153",
#         bluebook=image,
#         vehicle_insurance=image,
#         # vehicle_left_image=image,
#         # vehicle_right_image=image,
#         vehicle_front_image=image,
#         vehicle_back_image=image,
#         vehicle_interior_image=image,
#         owner=driver,
#     )
#     return vehicle


# def create_admin():
#     user = create_users(email="admin@gmail.com")
#     admin = Admin.objects.create(designation_name="test", user=user)
#     return admin


# def log_in(self, data):
#     login = self.client.post(reverse("accounts:login"), data=data)

#     token = login.data["access"]
#     return token


# def assign_vehicle(driver):
#     img = Image.new("RGB", (250, 250))
#     content = img.tobytes()

#     data = {
#         "manufacturer": "test",
#         "vehicle_class": "test",
#         "mot": content,
#         "has_child_seat": False,
#         "maximum_passengers": 4,
#         "luggage_capacity": "Small",
#         "vehicle_type": "Lux",
#         "vehicle_registration_number": "54654153153",
#         "bluebook": content,
#         "vehicle_insurance": content,
#         # "vehicle_left_image": content,
#         # "vehicle_right_image": content,
#         "vehicle_front_image": content,
#         "vehicle_back_image": content,
#         "vehicle_interior_image": content,
#     }
#     vehicle = Vehicle.objects.create(**data, owner=driver)
#     return vehicle


# # class SavedAddressTest(TestCase):
# #     def setUp(self) -> None:
# #         create_users(10)
# #         self.users = user_model.objects.all()
# #         create_n_saved_addresses(self.users)

# #     def test_authenticated_user_can_save_address(self):
# #         user = self.users[0]
# #         login_cred = {"email": user.email, "password": "123Password"}
# #         token = log_in(self, login_cred)
# #         data = {"title": "test", "address": "test address"}
# #         response = self.client.post(
# #             reverse("accounts:list_create_address"),
# #             content_type="application/json",
# #             data=data,
# #             **{"HTTP_AUTHORIZATION": f"Bearer {token}"},
# #         )
# #         self.assertEqual(response.status_code, 201)

# #     def test_authenticated_user_can_delete_address(self):
# #         user = self.users[0]
# #         obj = SavedAddress.objects.filter(user=user)[0]
# #         login_cred = {"email": user.email, "password": "123Password"}
# #         token = log_in(self, login_cred)
# #         response = self.client.get(
# #             reverse("accounts:delete_address", args=(str(obj.id),)),
# #             content_type="application/json",
# #             **{"HTTP_AUTHORIZATION": f"Bearer {token}"},
# #         )
# #         self.assertEqual(response.status_code, 200)
# #         obj.refresh_from_db()
# #         self.assertEqual(obj.deleted, True)
# #         # test if deleted address are being ignored while showing address list
# #         response = self.client.get(
# #             reverse("accounts:list_create_address"),
# #             content_type="application/json",
# #             **{"HTTP_AUTHORIZATION": f"Bearer {token}"},
# #         )
# #         self.assertEqual(len(response.json()["results"]), 0)
# #         # check if other one user can delete other's address

# #         obj2 = SavedAddress.objects.filter(user=self.users[1])[0]
# #         response = self.client.get(
# #             reverse("accounts:delete_address", args=(str(obj2.id),)),
# #             content_type="application/json",
# #             **{"HTTP_AUTHORIZATION": f"Bearer {token}"},
# #         )

# #         self.assertEqual(response.status_code, 404)

# #     def test_authenticated_user_can_update_address(self):
# #         user = self.users[0]
# #         obj = SavedAddress.objects.filter(user=user)[0]
# #         login_cred = {"email": user.email, "password": "123Password"}
# #         token = log_in(self, login_cred)
# #         data = {"title": "updated title"}
# #         response = self.client.patch(
# #             reverse("accounts:get_update_address", args=(str(obj.id),)),
# #             data=data,
# #             content_type="application/json",
# #             **{"HTTP_AUTHORIZATION": f"Bearer {token}"},
# #         )
# #         self.assertEqual(response.status_code, 200)
# #         obj.refresh_from_db()
# #         self.assertEqual(obj.title, "updated title")

# #         # test if one user can edit another users address
# #         obj2 = SavedAddress.objects.filter(user=self.users[1])[0]
# #         response = self.client.patch(
# #             reverse("accounts:get_update_address", args=(str(obj2.id),)),
# #             data=data,
# #             content_type="application/json",
# #             **{"HTTP_AUTHORIZATION": f"Bearer {token}"},
# #         )
# #         self.assertEqual(response.status_code, 404)
# #         obj.refresh_from_db()


# class DriverVehicleTest(TestCase):
#     def setUp(self) -> None:
#         create_driver(1)
#         create_admin()

#     def test_driver_and_vehicle_info_is_being_returned(self):
#         driver = Driver.objects.all()[0]
#         assign_vehicle(driver)
#         login_cred = {"email": "admin@gmail.com", "password": "123Password"}
#         token = log_in(self, login_cred)
#         response = self.client.get(
#             reverse("drivers_vehicle", args=(driver.id,)),
#             content_type="application/json",
#             **{"HTTP_AUTHORIZATION": f"Bearer {token}"},
#         )
#         self.assertEqual(response.status_code, 200)


# class CheckEmailIfExistsTest(TestCase):
#     @classmethod
#     def setUpTestData(cls):
#         create_users(10)

#     def test_checks_if_exists(self):
#         user = user_model.objects.all()[0]
#         data = {"email": user.email}
#         response = self.client.post(reverse("check_email"), data=data)
#         self.assertEqual(response.status_code, 400)

#         response = self.client.post(reverse("check_email"), data={})
#         self.assertEqual(response.status_code, 400)

#         data = {"email": "email12@gmail.com"}
#         response = self.client.post(reverse("check_email"), data=data)
#         self.assertEqual(response.status_code, 200)


# class CreateStaticTripTest(TestCase):
#     def setUp(self) -> None:
#         create_users(10)
#         create_admin()

#     def test_creates_static_trip(self):
#         client = Client()
#         login_cred = {"email": "admin@gmail.com", "password": "123Password"}
#         token = log_in(self, login_cred)
#         data = {
#             "date": "2022-12-12",
#             "pickup_time": "13:23",
#             "pickup_location_name": "dhaka",
#             "drop_off_location_name": "chittagong",
#             "number_of_passengers": 5,
#             "booking_method": "Hourly",
#             "hours": 5,
#             "pickup_location": "23.150782, 89.222988",
#             "drop_off_location": "23.150782, 89.221988",
#             "vehicle_type": "Lux",
#             "luggage_capacity": "Small",
#             "stops": "dhaka",
#             "stops": "chittagong",
#         }
#         trip_response = client.post(
#             reverse("static_trip_request"),
#             data=data,
#             content_type="application/json",
#             **{"HTTP_AUTHORIZATION": f"Bearer {token}"},
#         )
#         response_exc = client.post(
#             reverse("static_trip_request"),
#             data={},
#             content_type="application/json",
#             **{"HTTP_AUTHORIZATION": f"Bearer {token}"},
#         )
#         response_exc1 = client.post(
#             reverse("static_trip_request"),
#             data={},
#             content_type="application/json",
#             **{"HTTP_AUTHORIZATION": f"Bearer {token}"},
#         )

#         response_exc2 = client.post(
#             reverse("static_trip_request"),
#             data={
#                 "date": "2022-12-12",
#                 "pickup_time": "13:23",
#             },
#             content_type="application/json",
#             **{"HTTP_AUTHORIZATION": f"Bearer {token}"},
#         )
#         dataexc3 = {
#             "date": "2022-12-15",
#             "pickup_time": "13:23",
#             "pickup_location_name": "dhaka",
#             "drop_off_location_name": "chittagong",
#             "number_of_passengers": 5,
#             "booking_method": "Hourly",
#             "hours": 51,
#             "pickup_location": "23.150782, 89.222988",
#             "drop_off_location": "23.150782, 89.221988",
#             "vehicle_type": "Lux",
#             "luggage_capacity": "Small",
#             "stops": [
#                 {
#                     "location": "dhaka",
#                 }
#             ],
#         }
#         response_exc3 = client.post(
#             reverse("static_trip_request"),
#             data=dataexc3,
#             content_type="application/json",
#             **{"HTTP_AUTHORIZATION": f"Bearer {token}"},
#         )
#         dataexc4 = {
#             "date": "2022-12-16",
#             "pickup_time": "13:23",
#             "pickup_location_name": "dhaka",
#             "drop_off_location_name": "chittagong",
#             "number_of_passengers": 5,
#             "booking_method": "Hourly",
#             "hours": "das",
#             "pickup_location": "23.150782, 89.222988",
#             "drop_off_location": "23.150782, 89.221988",
#             "vehicle_type": "Lux",
#             "luggage_capacity": "Small",
#             "stops": [
#                 {
#                     "location": "dhaka",
#                 }
#             ],
#         }
#         response_exc4 = client.post(
#             reverse("static_trip_request"),
#             data=dataexc4,
#             content_type="application/json",
#             **{"HTTP_AUTHORIZATION": f"Bearer {token}"},
#         )

#         self.assertEqual(trip_response.status_code, 201)
#         self.assertEqual(response_exc.status_code, 400)
#         self.assertEqual(response_exc1.status_code, 400)
#         self.assertEqual(response_exc2.status_code, 400)
#         self.assertEqual(response_exc3.status_code, 400)
#         self.assertEqual(response_exc4.status_code, 400)


# class ToggleBlockStatusTest(TestCase):
#     def setUp(self) -> None:
#         create_users(10)
#         create_admin()

#     def test_toggles_user_block_status(self):
#         login_cred = {"email": "admin@gmail.com", "password": "123Password"}
#         token = log_in(self, login_cred)
#         users = user_model.objects.all()
#         for user in users:
#             response = self.client.get(
#                 reverse("toggle_block_status", args=(user.id,)),
#                 content_type="application/json",
#                 **{"HTTP_AUTHORIZATION": f"Bearer {token}"},
#             )
#             self.assertEqual(response.status_code, 200)
#             user.refresh_from_db()
#             self.assertEqual(user.blacklisted, True)
#             response = self.client.get(
#                 reverse("toggle_block_status", args=(user.id,)),
#                 content_type="application/json",
#                 **{"HTTP_AUTHORIZATION": f"Bearer {token}"},
#             )
#             self.assertEqual(response.status_code, 200)
#             user.refresh_from_db()
#             self.assertEqual(user.blacklisted, False)

#     def test_user_cant_block_if_not_admin(self):
#         for user in user_model.objects.all():
#             if not hasattr(user, "admin"):
#                 current_user = user
#                 break
#         user = user_model.objects.all()[0]
#         login_cred = {"email": current_user.email, "password": "123Password"}
#         token = log_in(self, login_cred)
#         user2 = user_model.objects.all()[1]
#         response = self.client.get(
#             reverse("toggle_block_status", args=(user2.id,)),
#             content_type="application/json",
#             **{"HTTP_AUTHORIZATION": f"Bearer {token}"},
#         )
#         self.assertEqual(response.status_code, 403)


# # class EditTripsTest(TestCase):
# #     def setUp(self) -> None:
# #         create_admin()
# #         create_trips(10)
# #         create_users(1)
# #
# #     def test_editing_trip_info(self):
# #         login_cred = {'email': 'admin@gmail.com', 'password': '123Password'}
# #         token = log_in(self, login_cred)
# #         data = {'pickup_location': 'Mars'}
# #         for trip in Trip.objects.all():
# #             response = self.client.patch(reverse('edit_trips', args=(trip.id,)),
# #                                          content_type='application/json', data=data,
# #                                          **{'HTTP_AUTHORIZATION': f'Bearer {token}'})
# #             self.assertEqual(response.status_code, 200)
# #             trip.refresh_from_db()
# #             self.assertEqual(trip.pickup_location, 'Mars')
# #
# #     def test_users_cant_edit_trips_if_not_admin(self):
# #         for user in user_model.objects.all():
# #             if not hasattr(user, 'admin'):
# #                 current_user = user
# #                 break
# #         login_cred = {'email': current_user.email, 'password': '123Password'}
# #         token = log_in(self, login_cred)
# #         data = {'pickup_location': 'Mars'}
# #         trip = Trip.objects.all()[0]
# #         response = self.client.patch(reverse('edit_trips', args=(trip.id,)),
# #                                      content_type='application/json', data=data,
# #                                      **{'HTTP_AUTHORIZATION': f'Bearer {token}'})
# #         self.assertEqual(response.status_code, 403)


# class VehicleRegisterTest(TestCase):
#     def setUp(self) -> None:
#         create_driver(1)

#     def test_vehicle_register(self):
#         driver = Driver.objects.all()[0]
#         img = Image.new("RGB", (250, 250))
#         content = img.tobytes()
#         imagefile = SimpleUploadedFile(
#             "test", content=content, content_type="image/jpeg"
#         )
#         # imagefile = SimpleUploadedFile('accounts/tests/images/2.jpg', b''),
#         data = {
#             "manufacturer": "test",
#             "owner": driver,
#             "vehicle_class": "test",
#             "mot": imagefile,
#             "has_child_seat": False,
#             "maximum_passengers": 4,
#             "luggage_capacity": "Small",
#             "vehicle_type": "Lux",
#             "vehicle_registration_number": "54654153153",
#             "bluebook": imagefile,
#             "vehicle_insurance": imagefile,
#             # "vehicle_left_image": imagefile,
#             # "vehicle_right_image": imagefile,
#             "vehicle_front_image": imagefile,
#             "vehicle_back_image": imagefile,
#             "vehicle_interior_image": imagefile,
#         }
#         login_cred = {"email": driver.user.email, "password": "123Password"}
#         token = log_in(self, login_cred)
#         response = self.client.post(
#             reverse("register_vehicle"),
#             format="multipart",
#             data=data,
#             **{"HTTP_AUTHORIZATION": f"Bearer {token}"},
#         )
#         self.assertEqual(response.status_code, 201)


# # class CancelTripTest(TestCase):
# #     def setUp(self) -> None:
# #         create_trips(1)
# #         create_users(1)
# #         create_admin()
# #         create_driver(1)
# #
# #     def test_admin_cancels_trip(self):
# #         trip = Trip.objects.all()[0]
# #         login_cred = {'email': 'admin@gmail.com', 'password': '123Password'}
# #         token = log_in(self, login_cred)
# #         response = self.client.get(reverse('cancel_trip', args=(trip.id,)), content_type='application/json',
# #                                    **{'HTTP_AUTHORIZATION': f'Bearer {token}'})
# #         self.assertEqual(response.status_code, 200)
# #
# #     def test_driver_cancels_trip(self):
# #         trip = Trip.objects.all()[0]
# #         trip.driver = Driver.objects.all()[0]
# #         trip.save()
# #         login_cred = {'email': trip.driver.user.email,
# #                       'password': '123Password'}
# #         token = log_in(self, login_cred)
# #         response = self.client.get(reverse('cancel_trip', args=(trip.id,)), content_type='application/json',
# #                                    **{'HTTP_AUTHORIZATION': f'Bearer {token}'})
# #         self.assertEqual(response.status_code, 200)
# #
# #     def test_user_cancels_trip(self):
# #         trip = Trip.objects.all()[0]
# #         login_cred = {'email': trip.user.email, 'password': '123Password'}
# #         token = log_in(self, login_cred)
# #         response = self.client.get(reverse('cancel_trip', args=(trip.id,)), content_type='application/json',
# #                                    **{'HTTP_AUTHORIZATION': f'Bearer {token}'})
# #         self.assertEqual(response.status_code, 200)
# #
# #     def test_completed_trip_cant_be_changed(self):
# #         trip = Trip.objects.all()[0]
# #         trip.trip_status = 'completed'
# #         trip.save()
# #         login_cred = {'email': trip.user.email, 'password': '123Password'}
# #         token = log_in(self, login_cred)
# #         response = self.client.get(reverse('cancel_trip', args=(trip.id,)), content_type='application/json',
# #                                    **{'HTTP_AUTHORIZATION': f'Bearer {token}'})
# #         self.assertEqual(response.status_code, 403)
# #
# #     def test_trip_cant_be_cancelled_if_user_not_trip_user_or_driver_or_admin(self):
# #         trip = Trip.objects.all()[0]
# #         trip.trip_status = 'completed'
# #         trip.save()
# #         user = create_users(1)[0]
# #         login_cred = {'email': user.email, 'password': '123Password'}
# #         token = log_in(self, login_cred)
# #         response = self.client.get(reverse('cancel_trip', args=(trip.id,)), content_type='application/json',
# #                                    **{'HTTP_AUTHORIZATION': f'Bearer {token}'})
# #         self.assertEqual(response.status_code, 403)


# class ViewsTest(APITestCase):
#     def setUp(self):
#         self.client = APIClient()
#         img = Image.new("RGB", (250, 250))
#         image = img.tobytes()
#         self.user = CustomUser.objects.create_user(
#             email="test@gmail.com", password="test1234"
#         )
#         self.driver = Driver.objects.create(
#             user=self.user,
#             national_insurance="34523874",
#             is_condemned_prior=True,
#             is_verified=True,
#             status="Verified",
#             driving_license_back_image=image,
#             driving_license_front_image=image,
#         )
#         self.driver.save()
#         self.user.save()

#     def test_user_login(self, email="test@gmail.com", password="test1234"):
#         client = Client()
#         response = client.post(reverse("login"), {"email": email, "password": password})

#         self.assertEqual(response.status_code, 200)

#     def test_user_details_view(self):
#         client = Client()
#         response = client.get(reverse("all_users"))

#         self.assertEqual(response.status_code, 200)

#     def test_driver_detail_view(self):
#         client = Client()
#         response = client.get(reverse("all_drivers"))

#         self.assertEqual(response.status_code, 200)

#     def test_individual_user_view(self):
#         client = Client()

#         res = client.post(
#             reverse("login"), {"email": "test@gmail.com", "password": "test1234"}
#         )
#         token = res.data["access"]

#         response = self.client.get(
#             reverse("get_user"),
#             content_type="application/json",
#             **{"HTTP_AUTHORIZATION": f"Bearer {token}"},
#         )
#         self.assertEqual(response.status_code, 200)

#     def test_logout_view(self):
#         client = Client()

#         res = client.post(
#             reverse("login"), {"email": "test@gmail.com", "password": "test1234"}
#         )
#         refresh_token = res.data["refresh"]
#         access_token = res.data["access"]
#         data = json.dumps(
#             {
#                 "refresh": refresh_token,
#             }
#         )
#         response = self.client.post(
#             reverse("logout"),
#             data,
#             content_type="application/json",
#             **{"HTTP_AUTHORIZATION": f"Bearer {access_token}"},
#         )
#         self.assertEqual(response.status_code, 200)

#     def test_create_driver_view(self):
#         client = Client()
#         imagefile = (SimpleUploadedFile("accounts/tests/images/1.jpeg", b""),)

#         data = {
#             "first_name": "test",
#             "last_name": "test",
#             "email": "test@email.com",
#             "phone": "+440123456789",
#             "address": "test address",
#             "password": "Asdas312312",
#             "driving_license_front_image": imagefile,
#             "driving_license_back_image": imagefile,
#             "drivers_bank_account_number": "123456789",
#             "drivers_pco_license_number": "123456789",
#             "national_insurance": "34523874",
#             "is_condemned_prior": False,
#             "gender": "Male",
#         }
#         headers = {"content_type": "multipart/form-data"}
#         response = client.post(reverse("create_driver"), data=data, headers=headers)
#         self.assertEqual(response.status_code, 201)

#     def test_vehicle_api_view(self):
#         client = Client()
#         res = client.post(
#             reverse("login"), {"email": "test@gmail.com", "password": "test1234"}
#         )
#         owner = CustomUser.objects.get(email="test@gmail.com")
#         refresh_token = res.data["refresh"]
#         access_token = res.data["access"]

#         imagefile = (SimpleUploadedFile("accounts/tests/images/2.jpeg", b""),)

#         data = {
#             "manufacturer": "test",
#             "owner": owner,
#             "vehicle_class": "test",
#             "mot": imagefile,
#             "has_child_seat": False,
#             "maximum_passengers": 4,
#             "luggage_capacity": "Small",
#             "vehicle_type": "Lux",
#             "vehicle_registration_number": "54654153153",
#             "bluebook": imagefile,
#             "vehicle_insurance": imagefile,
#             # "vehicle_left_image": imagefile,
#             # "vehicle_right_image": imagefile,
#             "vehicle_front_image": imagefile,
#             "vehicle_back_image": imagefile,
#             "vehicle_interior_image": imagefile,
#         }
#         # headers={'content_type':'multipart/form-data',
#         #          'Authorization': f'Bearer {access_token}'}
#         # response = client.post(reverse('register_vehicle'), json=data, headers=headers)
#         response = self.client.post(
#             reverse("register_vehicle"),
#             data=data,
#             format="multipart",
#             **{"HTTP_AUTHORIZATION": f"Bearer {access_token}"},
#         )
#         self.assertEqual(response.status_code, 201)

#     def test_validate_token(self):
#         client = Client()
#         data = {
#             "email": "tester@gmail.com",
#             "first_name": "Afsan",
#             "last_name": "Saeed",
#             "phone": "+440123456789",
#             "address": "Dhaka",
#             "password": "Afsan9802345",
#         }
#         headers = {"content_type": "multipart/form-data"}
#         response = client.post(reverse("signup"), data=data, headers=headers)
#         temp_id = response.data["id"]
#         user_data = models.UserData(id=response.data["id"])
#         # token = models.UserToken.objects.get(user_data=user_data)
#         data2 = {"id": response.data["id"]} #, "token": token
#         response = client.post(reverse("validate_token"), data=data2, headers=headers)
#         self.assertEqual(response.status_code, 200)

#         response = client.post(reverse("validate_token"), data={}, headers=headers)
#         self.assertEqual(response.status_code, 400)
#         response = client.post(
#             reverse("validate_token"),
#             data={"id": temp_id, "token": "123"},
#             headers=headers,
#         )
#         self.assertEqual(response.status_code, 400)

#     def test_resend_token(self):
#         client = Client()
#         data = {
#             "email": "tester@gmail.com",
#             "first_name": "Afsan",
#             "last_name": "Saeed",
#             "phone": "+440123456789",
#             "address": "Dhaka",
#             "password": "Afsan9802345",
#         }
#         headers = {"content_type": "multipart/form-data"}
#         response = client.post(reverse("signup"), data=data, headers=headers)
#         temp_id = response.data["id"]
#         user_data = models.UserData(id=response.data["id"])
#         # token = models.UserToken.objects.get(user_data=user_data)
#         data2 = {
#             "id": response.data["id"],
#         }
#         response = client.post(reverse("resend_token"), data=data2, headers=headers)
#         self.assertEqual(response.status_code, 200)

#         response = client.post(reverse("resend_token"), data={}, headers=headers)
#         self.assertEqual(response.status_code, 400)

#     def test_reset_password_api_view(self):
#         client = Client()

#         res = client.post(
#             reverse("login"), {"email": "test@gmail.com", "password": "test1234"}
#         )
#         refresh_token = res.data["refresh"]
#         access_token = res.data["access"]
#         data = {"email": "test@gmail.com"}
#         headers = {"content_type": "multipart/form-data"}
#         response = client.post(reverse("password_reset"), data=data, headers=headers)
#         response_exc = client.post(reverse("password_reset"), data={}, headers=headers)
#         response_exc1 = client.post(
#             reverse("password_reset"),
#             data={"email": "jaman@gmail.com"},
#             headers=headers,
#         )
#         user = models.CustomUser.objects.get(email="test@gmail.com")
#         # token = models.UserOTP.objects.get(user_data=user)
#         data2 = {
#             "email": "test@gmail.com",
#             # "otp": token.otp,
#         }
#         response1 = client.post(
#             reverse("password_reset_validation"), data=data2, headers=headers
#         )

#         data4 = {
#             "email": "test@gmail.com",
#             "password": "Test@1234354",
#         }
#         response4 = client.post(
#             reverse("password_reset_confirm"),
#             data=data4,
#             content_type="application/json",
#             **{"HTTP_AUTHORIZATION": f'Bearer {response1.data["access"]}'},
#         )
#         response4_exc1 = client.post(
#             reverse("password_reset_confirm"),
#             data={},
#             content_type="application/json",
#             **{"HTTP_AUTHORIZATION": f'Bearer {response1.data["access"]}'},
#         )
#         response4_exc2 = client.post(
#             reverse("password_reset_confirm"),
#             data={"email": "test43@gmail.com", "password": "Test@1234354"},
#             content_type="application/json",
#             **{"HTTP_AUTHORIZATION": f'Bearer {response1.data["access"]}'},
#         )

#         response1_exc = client.post(
#             reverse("password_reset_validation"), data={}, headers=headers
#         )
#         response2_exc = client.post(
#             reverse("password_reset_validation"),
#             data={
#                 "email": "a@gmail.com",
#                 "otp": token.otp,
#             },
#             headers=headers,
#         )
#         response3_exc = client.post(
#             reverse("password_reset_validation"),
#             data={
#                 "email": "test@gmail.com",
#                 "otp": "3526",
#             },
#             headers=headers,
#         )

#         data3 = {"email": "test@gmail.com"}
#         response3 = client.post(reverse("password_resend"), data=data3, headers=headers)
#         response3_exc1 = client.post(
#             reverse("password_resend"), data={}, headers=headers
#         )
#         response3_exc2 = client.post(
#             reverse("password_resend"),
#             data={"email": "fake@gmail.com"},
#             headers=headers,
#         )
#         # headers1 = {
#         #     'content_type': 'multipart/form-data',
#         #     'HTTP_AUTHORIZATION': f'Bearer {response1.data["access"]}'
#         # }

#         self.assertEqual(response.status_code, 200)
#         self.assertEqual(response1.status_code, 200)
#         self.assertEqual(response3.status_code, 200)
#         self.assertEqual(response_exc.status_code, 400)
#         self.assertEqual(response_exc1.status_code, 400)
#         self.assertEqual(response1_exc.status_code, 400)
#         self.assertEqual(response2_exc.status_code, 400)
#         self.assertEqual(response3_exc.status_code, 400)
#         self.assertEqual(response3_exc1.status_code, 400)
#         self.assertEqual(response3_exc2.status_code, 400)
#         self.assertEqual(response4.status_code, 200)
#         self.assertEqual(response4_exc1.status_code, 400)
#         self.assertEqual(response4_exc2.status_code, 400)


# class FevoriteDriverApiViewTest(TestCase):
#     def setUp(self):
#         self.user = models.CustomUser.objects.create_user(
#             email="t1@gmail.com", password="Test@1234"
#         )
#         self.driver = create_driver(1)[0]
#         self.fev_drivers_list = models.FevoriteDriverModel.objects.create(
#             user=self.user, driver=self.driver
#         )

#     def test_fevorite_driver_api_view(self):
#         client = Client()
#         login_data = {"email": "t1@gmail.com", "password": "Test@1234"}
#         token = log_in(self, login_data)
#         response = client.post(
#             reverse("get_fevorites"),
#             data={"gender": "Male"},
#             content_type="application/json",
#             **{"HTTP_AUTHORIZATION": f"Bearer {token}"},
#         )
#         response_exc = client.post(
#             reverse("get_fevorites"),
#             data={"gender": "ale"},
#             content_type="application/json",
#             **{"HTTP_AUTHORIZATION": f"Bearer {token}"},
#         )
#         response_exc1 = client.post(
#             reverse("get_fevorites"),
#             data={},
#             content_type="application/json",
#             **{"HTTP_AUTHORIZATION": f"Bearer {token}"},
#         )

#         response_exc2 = client.post(
#             reverse("get_fevorites"),
#             data={},
#             content_type="application/json",
#             **{"HTTP_AUTHORIZATION": f"Bearer 71964555-6936-44c7-977a-01f0416a686c"},
#         )

#         self.assertEqual(response.status_code, 200)
#         self.assertEqual(response_exc.status_code, 400)
#         self.assertEqual(response_exc1.status_code, 400)
#         self.assertEqual(response_exc2.status_code, 401)


# # class TestViewsP2(TestCase):
# #     def setUp(self):
# #         self.user = models.CustomUser.objects.create_user(
# #             email="t2@gmail.com", password="Test@1234")
# #         self.user2 = models.CustomUser.objects.create_user(
# #             email="t3@gmail.com", password="Test@1234")
# #
# #         self.driver = create_driver(1)[0]
# #         self.vehicle = create_vehicle(self.driver)
# #         self.fev_drivers_list = models.FevoriteDriverModel.objects.create(
# #             user=self.user, driver=self.driver)
# #         self.trip = models.Trip.objects.create(
# #             date='2022-12-20', user=self.user, booking_method='Hourly', pickup_location='dhaka',
# #             pickup_time='13:23', drop_off_location='chittagong', number_of_passengers=5, payment_status='Paid'
# #         )
# #         self.custom_trip = Trip.objects.create(
# #             date='2022-12-25', user=self.user, booking_method='hourly',
# #             hours=5,
# #             pickup_location='23.150782, 89.222988',
# #             pickup_time='13:23', drop_off_location='23.150782, 89.222988', number_of_passengers=5,
# #             payment_status='paid', preferred_drivers_gender="Male", luggage_size="Small", vehicle_type="Lux",
# #         )
# #         self.custom_trip1 = Trip.objects.create(
# #             date='2022-12-29', user=self.user, booking_method='hourly',
# #             hours=5,
# #             pickup_location='23.150782, 89.222988',
# #             pickup_time='13:23', drop_off_location='23.150782, 89.222988', number_of_passengers=5,
# #             payment_status='paid', luggage_size="Small", vehicle_type="Lux",
# #         )
# #         img = Image.new('RGB', (250, 250))
# #         image = img.tobytes()
# #         self.custom_vehicle = Vehicle.objects.create(
# #             manufacturer='test', vehicle_class='test', mot=image, has_child_seat=True,
# #             maximum_passengers=8, luggage_capacity='Small', vehicle_type='Lux',
# #             vehicle_registration_number='54654153153', bluebook=image, vehicle_insurance=image,
# #             vehicle_left_image=image, vehicle_right_image=image, vehicle_front_image=image,
# #             vehicle_back_image=image, vehicle_interior_image=image, owner=self.driver
# #         )
# #         self.custom_driver = Driver.objects.create(
# #             user=self.user2, driving_license_front_image=image, driving_license_back_image=image,
# #             national_insurance='1224',
# #             is_condemned_prior=False,
# #             status="Verified",
# #             is_verified=True,
# #             gender="Male"
# #         )
# #
# #     def test_individual_users_all_trips_api_view(self):
# #         client = Client()
# #         login_data = {
# #             "email": "t2@gmail.com",
# #             "password": "Test@1234"
# #         }
# #         token = log_in(self, login_data)
# #         login_data1 = {
# #             "email": "t3@gmail.com",
# #             "password": "Test@1234"
# #         }
# #         token1 = log_in(self, login_data1)
# #         response = client.get(
# #             reverse('users_all_trips'), content_type='application/json', **{'HTTP_AUTHORIZATION': f'Bearer {token}'})
# #         response1 = client.get(
# #             reverse('users_all_trips'), content_type='application/json', **{'HTTP_AUTHORIZATION': f'Bearer {token1}'})
# #         self.assertEqual(response.status_code, 200)
# #         self.assertEqual(response1.status_code, 404)
# #
# #     def test_set_trip_status_api_view(self):
# #         client = Client()
# #         login_data = {
# #             "email": "t2@gmail.com",
# #             "password": "Test@1234"
# #         }
# #         token = log_in(self, login_data)
# #         response = client.post(
# #             reverse('set_trip_status'), data={
# #                 "id": self.trip.id,
# #                 "status": "completed"
# #             }, content_type='application/json', **{'HTTP_AUTHORIZATION': f'Bearer {token}'})
# #
# #         response1 = client.post(
# #             reverse('set_trip_status'), data={
# #                 "id": "71964555-6936-44c7-977a-01f0416a686c",
# #                 "status": "completed"
# #             }, content_type='application/json', **{'HTTP_AUTHORIZATION': f'Bearer {token}'})
# #         self.assertEqual(response.status_code, 200)
# #         self.assertEqual(response1.status_code, 404)
# #
# #     def test_assign_vehicle_api_view(self):
# #         client = Client()
# #         login_data = {
# #             "email": "t2@gmail.com",
# #             "password": "Test@1234"
# #         }
# #         token = log_in(self, login_data)
# #
# #         data = {
# #             "trip_id": self.trip.id,
# #             "vehicle_id": self.vehicle.id,
# #             "driver_id": self.driver.id
# #         }
# #         response = client.post(
# #             reverse('assign_vehicle'), data=data, content_type='application/json',
# #             **{'HTTP_AUTHORIZATION': f'Bearer {token}'})
# #         response_ex1 = client.post(
# #             reverse('assign_vehicle'), data={
# #                 "trip_id": "",
# #                 "vehicle_id": self.vehicle.id,
# #                 "driver_id": self.driver.id
# #             }, content_type='application/json', **{'HTTP_AUTHORIZATION': f'Bearer {token}'})
# #         response_ex2 = client.post(
# #             reverse('assign_vehicle'), data={
# #                 "trip_id": self.trip.id,
# #                 "vehicle_id": "",
# #                 "driver_id": self.driver.id
# #             }, content_type='application/json', **{'HTTP_AUTHORIZATION': f'Bearer {token}'})
# #         response_ex3 = client.post(
# #             reverse('assign_vehicle'), data={
# #                 "trip_id": self.trip.id,
# #                 "vehicle_id": self.vehicle.id,
# #                 "driver_id": ""
# #             }, content_type='application/json', **{'HTTP_AUTHORIZATION': f'Bearer {token}'})
# #         response_ex4 = client.post(
# #             reverse('assign_vehicle'), data={
# #                 "trip_id": self.trip.id,
# #                 "vehicle_id": self.vehicle.id,
# #                 "driver_id": self.driver.id
# #             }, content_type='application/json', **{'HTTP_AUTHORIZATION': f'Bearer {token}'})
# #
# #         self.assertEqual(response.status_code, 200)
# #         self.assertEqual(response_ex1.status_code, 404)
# #         self.assertEqual(response_ex2.status_code, 404)
# #         self.assertEqual(response_ex3.status_code, 404)
# #         self.assertEqual(response_ex4.status_code, 400)
# #
# #     def test_show_drivers_for_trip_api_view(self):
# #         client = Client()
# #         login_data = {
# #             "email": "t2@gmail.com",
# #             "password": "Test@1234"
# #         }
# #         token = log_in(self, login_data)
# #
# #         response1 = client.get(
# #             reverse('show_drivers_for_trip', args=(self.custom_trip.id,)), content_type='application/json',
# #             **{'HTTP_AUTHORIZATION': f'Bearer {token}'})
# #         response2 = client.get(
# #             reverse('show_drivers_for_trip', args=(self.custom_trip1.id,)), content_type='application/json',
# #             **{'HTTP_AUTHORIZATION': f'Bearer {token}'})
# #         response_ex = client.get(
# #             reverse('show_drivers_for_trip', args=(self.trip.id,)), content_type='application/json',
# #             **{'HTTP_AUTHORIZATION': f'Bearer {token}'})
# #         response_ex1 = client.get(
# #             reverse('show_drivers_for_trip', args=(
# #                 "71964555-6936-44c7-977a-01f0416a686c",)),
# #             content_type='application/json', **{'HTTP_AUTHORIZATION': f'Bearer {token}'})
# #
# #         self.assertEqual(response1.status_code, 200)
# #         self.assertEqual(response2.status_code, 200)
# #         self.assertEqual(response_ex.status_code, 404)
# #         self.assertEqual(response_ex1.status_code, 400)
# #
# #     def test_trip_request_status_update_api_view(self):
# #         client = Client()
# #         login_data = {
# #             "email": "t2@gmail.com",
# #             "password": "Test@1234"
# #         }
# #         token = log_in(self, login_data)
# #         self.trip.trip_status = "accepted"
# #
# #     def test_user_profile_api_view(self):
# #         client = Client()
# #         login_data = {
# #             "email": "t2@gmail.com",
# #             "password": "Test@1234"
# #         }
# #         token = log_in(self, login_data)
# #         response = client.get(reverse(
# #             'user_profile'), content_type='application/json', **{'HTTP_AUTHORIZATION': f'Bearer {token}'})
# #         self.assertEqual(response.status_code, 200)
# #
# #     def test_accept_or_deny_vehicle_assign_request_api_view(self):
# #         client = Client()
# #         login_data = {
# #             "email": "t3@gmail.com",
# #             "password": "Test@1234"
# #         }
# #         token = log_in(self, login_data)
# #         login_data1 = {
# #             "email": "t2@gmail.com",
# #             "password": "Test@1234"
# #         }
# #         token1 = log_in(self, login_data1)
# #         models.VehicleAssignWaitingList.objects.create(
# #             trip=self.custom_trip, driver=self.custom_driver, vehicle=self.custom_vehicle)
# #         obj = models.VehicleAssignWaitingList.objects.filter(
# #             driver=self.custom_driver)
# #         response = client.post(reverse('vehicle_assign_request_status'), data={
# #             "status": "Accepted"
# #         }, content_type='application/json', **{'HTTP_AUTHORIZATION': f'Bearer {token}'})
# #
# #         models.VehicleAssignWaitingList.objects.create(
# #             trip=self.custom_trip, driver=self.custom_driver, vehicle=self.custom_vehicle)
# #         response_ex1 = client.post(reverse('vehicle_assign_request_status'), data={
# #             "status": "whatever"
# #         }, content_type='application/json', **{'HTTP_AUTHORIZATION': f'Bearer {token}'})
# #         response_ex2 = client.post(reverse('vehicle_assign_request_status'),
# #                                    content_type='application/json', **{'HTTP_AUTHORIZATION': f'Bearer {token}'})
# #         response_ex = client.post(reverse('vehicle_assign_request_status'), data={
# #             "status": "Accepted"
# #         }, content_type='application/json', **{'HTTP_AUTHORIZATION': f'Bearer {token1}'})
# #         self.assertEqual(response.status_code, 200)
# #         self.assertEqual(response_ex1.status_code, 400)
# #         self.assertEqual(response_ex2.status_code, 400)
# #         self.assertEqual(response_ex.status_code, 400)


# class DriverSignUpTest(APITestCase):
#     def test_signup(self):
#         img = Image.new("RGB", (250, 250)).tobytes()
#         # data = {
#         #     'driving_license_front_image': img,
#         #     'driving_license_back_image': img,
#         #     'national_insurance': 5657868798,
#         #     'is_condemned_prior': True,
#         #     'drivers_pco_license_number': 87998789,
#         #     'drivers_bank_account_number': 6778798,
#         #     'gender': 'Male',
#         #     'first_name': 'Harry',
#         #     'last_name': 'Potter',
#         #     'email': 'k@gmail.com',
#         #     'address': 'jessore',
#         #     'password': '89u6yiu8udunfujhfujjK687uh',
#         #     'phone': '+44 1234567890'
#         # }
#         # response = self.client.post(reverse('create_driver'), data=data)

#         # self.assertEqual(response.status_code, status.HTTP_201_CREATED)
#         imagefile = (SimpleUploadedFile("accounts/tests/images/1.jpeg", b""),)

#         data = {
#             "first_name": "test",
#             "last_name": "test",
#             "email": "test@email.com",
#             "phone": "+440123456789",
#             "address": "test address",
#             "password": "Asdas312312",
#             "driving_license_front_image": img,
#             "driving_license_back_image": img,
#             "drivers_bank_account_number": "123456789",
#             "drivers_pco_license_number": "123456789",
#             "national_insurance": "34523874",
#             "is_condemned_prior": False,
#             "gender": "Male",
#         }
#         headers = {"content_type": "multipart/form-data"}
#         response = self.client.post(
#             reverse("create_driver_v2"), data=data, headers=headers
#         )

#         self.assertEqual(response.status_code, 201)
