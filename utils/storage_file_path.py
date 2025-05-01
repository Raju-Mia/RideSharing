
import uuid
from datetime import datetime
from django.conf import settings
from django.db import models




# # Define the custom file upload path function
# def driver_file_path(instance, filename, field_name):
#     # Extract the file extension
#     ext = filename.split('.')[-1]
    
#     # Get the current date in YYYYMMDD format
#     current_date = datetime.now().strftime('%Y%m%d')
    
#     # Generate a unique identifier
#     unique_number = uuid.uuid4().hex[:8]  # Generates an 8-character unique identifier
    
#     # Construct the final file path
#     filename = f"{field_name}_{unique_number}.{ext}"
#     return f'rydr/drivers/documents/{instance.user.username}/{current_date}/{filename}'

# # Field-specific helper functions
# def image_is_upload_path(instance, filename):
#     return driver_file_path(instance, filename, 'image_is')

# def file_is_upload_path(instance, filename):
#     return driver_file_path(instance, filename, 'file_is')




def phone_email_change_state_file_path(instance, filename):
    # Extract the file extension
    ext = filename.split('.')[-1]
    current_date = datetime.now().strftime('%Y%m%d')
    unique_number = uuid.uuid4().hex[:8]
    field_name = current_date # "used custom name"
    filename = f"{field_name}_{unique_number}.{ext}"
    return f'uc/AccountApp/PhoneEmailChangeState/{instance.user.username}/{current_date}/{filename}'


