from PIL import Image
from django.contrib.auth import get_user_model
from django.test import TestCase
from accounts.helpers import create_user
# from accounts.models import SavedAddress, Driver


user_model = get_user_model()


# class CreateUserTest(TestCase):
#     def setUp(self) -> None:
#         UserData.objects.create(first_name=f'First_name', last_name=f'last_name', phone='01757578',
#                                 address='dhaka', email=f"email@gmail.com")
#
#     def test_user_creation(self):
#         user_data = UserData.objects.all()[0]
#         img = Image.new('RGB', (250, 250))
#         image = img.tobytes()
#         DriverData.objects.create(user_data=user_data, driving_license_front_image=image,
#                                   driving_license_back_image=image, national_insurance='dhhddjh',
#                                   is_condemned_prior=True, gender='male')
#         for data in UserData.objects.all():
#             user = create_user(data.id)
#             assert isinstance(user['user'], user_model), True
#             assert isinstance(user['driver'], Driver), True
#
#     def test_creation_without_driver_data(self):
#         user_data = UserData.objects.all()[0]
#         user = create_user(user_data.id)
#         assert isinstance(user['user'], user_model), True
#         assert user['driver'] == None

# class SendingDataToCentralTest(TestCase):
#     def setUp(self) -> None:
#         create_trips(1)


# def create_n_saved_addresses(users):
#     for user in users:
#         SavedAddress.objects.create(title="test", address="dhaka", user=user)
