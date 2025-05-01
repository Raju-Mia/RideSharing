
import uuid
from datetime import datetime
from django.conf import settings
from django.db import models




def phone_email_change_state_file_path(instance, filename):
    # Extract the file extension
    ext = filename.split('.')[-1]
    current_date = datetime.now().strftime('%Y%m%d')
    unique_number = uuid.uuid4().hex[:8]
    field_name = current_date # "used custom name"
    filename = f"{field_name}_{unique_number}.{ext}"
    return f'uc/AccountApp/PhoneEmailChangeState/{instance.user.username}/{current_date}/{filename}'


