from time import time
import stripe
from django.conf import settings
from stripe.error import CardError, IdempotencyError
from rest_framework.views import APIView
from rest_framework.response import Response
from stripe.oauth_error import InvalidRequestError
from django.core.exceptions import ValidationError

#Import
from accounts.models import Services
from payment.models import ClientWallet, DriverWallet, OrganizationWallet, Transaction

stripe.api_key = settings.STRIPE_SECRET_KEY


# ==================================New==================================
def is_stripe_customer_account(user):
    
    if not user.stripe_id:
        # Create a Stripe customer
        customer = stripe.Customer.create()
        
        # User Scripe ID add
        user.stripe_id = customer.id
        user.save()

        # Create or get the user's wallet
        wallet, created = ClientWallet.objects.get_or_create(user=user)
        wallet.stripe_customer_id = customer.id
        wallet.save()
        
        return customer
                    
                
                
    if not user.stripe_id:
        return False
    try:
        data_from_stripe = stripe.PaymentMethod.list(
            customer=user.stripe_id, type="card"
        )
    except:
        return False
    if not data_from_stripe["data"]:
        return False
    return True


#===============================================old ==================
def is_stripe_customer(user):
    if not user.stripe_id:
        return False
    try:
        data_from_stripe = stripe.PaymentMethod.list(
            customer=user.stripe_id, type="card"
        )
    except:
        return False
    if not data_from_stripe["data"]:
        return False
    return True


def hold_amount(customer, amount, payment_method, metadata):
    intent = stripe.PaymentIntent.create(
        amount=int(amount),
        currency="gbp",
        customer=customer,
        payment_method=payment_method,
        automatic_payment_methods={"enabled": True},
        payment_method_options={"card": {"capture_method": "manual"}},
        metadata=metadata,
    )
    return intent.id


def capture_amount(payment_intent_id, amount):
    intent = stripe.PaymentIntent.capture(payment_intent_id, amount_to_capture=amount)


def create_bank_account_token(
    country,
    currency,
    account_number,
    routing_number,
    account_holder_name,
    account_holder_type,
):
    data = {
        "country": country,
        "currency": currency,
        "account_number": account_number,
        "routing_number": routing_number,
        "account_holder_name": account_holder_name,
        "account_holder_type": account_holder_type,
    }
    try:
        token = stripe.Token.create(bank_account=data)
    except (CardError, IdempotencyError, InvalidRequestError):
        return None
    return token


def add_bank_account_to_a_customer(bank_account_token, customer_id):
    res = stripe.Customer.create_source(customer_id, source=bank_account_token)
    return res








# ============== Create Stripe Customer ======1=====
def create_stripe_customer(user):
    """
    Creates a Stripe customer with email, name, and additional details.
    - If the user has an email, it will be used.
    - If no email is available, it will use a placeholder email with the phone number.
    - If neither is available, the email field will be omitted.
    """
    try:
        # Determine the email value
        email = user.email or (f"{user.phone}@gmail.com" if user.phone else None)

        # Prepare customer creation payload
        customer_data = {
            "name": user.get_full_name(),  # Pass user's name (if available)
            "metadata": {
                "user_id": str(user.id),  # Pass user's unique ID or UUID
                "phone": user.phone if user.phone else "N/A",
                "service": user.service,  # Any additional information you want to store
            }
        }
        if email:  # Include email only if it exists
            customer_data["email"] = email

        # Create the Stripe customer
        customer = stripe.Customer.create(**customer_data)
        return customer
    except stripe.error.StripeError as e:
        print(f"Stripe error: {str(e)}")
        raise e
    except Exception as e:
        print(f"Error: {str(e)}")
        raise e



# ============== Updating a Stripe Customer================
def update_stripe_customer(user):
    """
    Updates the Stripe customer details such as name, email, and metadata.
    """
    try:
        # Ensure the user has a Stripe customer ID
        if not user.stripe_id:
            raise ValueError("User does not have a Stripe customer ID.")

        # Prepare updated data
        update_data = {
            "name": user.get_full_name(),
            "email": user.email,  # Can be updated or left as is
            "metadata": {
                "user_id": str(user.id),
                "phone": user.phone,
                "service": user.service,
            }
        }

        # Perform the update
        customer = stripe.Customer.modify(user.stripe_id, **update_data)

        print(f"Customer updated successfully: {customer}")
        return customer

    except stripe.error.StripeError as e:
        print(f"Stripe error: {str(e)}")
        raise e
    except Exception as e:
        print(f"Error: {str(e)}")
        raise e




# =========== Customer 'connected Stripe account'======3======
# def create_connected_account(user):
#     """
#     Function to create a Stripe connected account for a user.
#     This is required for direct payouts to drivers or service providers.
#     """
    
#     if not user.stripe_id:
#             raise ValidationError("User does not have a Stripe customer ID.")
        
#     try:
#         connected_account = stripe.Account.create(
#             type="express",
#             country="US",  # Adjust to your supported country
#             email=user.email,
#             capabilities={
#                 "transfers": {"requested": True},
#                 "card_payments": {"requested": True},
#             },
#             business_type="individual",
#             business_profile={
#                 "name": "United Chauffeur",
#                 "product_description": "Ride-sharing services",
#             },
#             tos_acceptance={
#                 "service_agreement": "full"
#                 # "date": int(time.time()),
#                 # "ip": ip_address
        
#             }
            
        
#         )
#         print(f"Connected account created successfully for {user.email}.")
#         return connected_account.id
#     except stripe.error.StripeError as e:
#         print(f"Stripe error while creating connected account: {str(e)}")
#         raise e
#     except Exception as e:
#         print(f"Error while creating connected account: {str(e)}")
#         raise e



import stripe
import time
from django.core.exceptions import ValidationError

def create_connected_account(user, ip_address=None):
    """
    Function to create a Stripe connected account for a user.
    This is required for direct payouts to drivers or service providers.
    """
    print("=== Create connected account functionCalling======")
    if not user.stripe_id:
        raise ValidationError("User does not have a Stripe customer ID.")

    try:
        print("Connected account here.1")
        # Create a connected account
        connected_account = stripe.Account.create(
            type="express",
            country="US",  # Adjust based on your supported country
            email=user.email,
            capabilities={
                "transfers": {"requested": True},
                "card_payments": {"requested": True},
            },
            business_type="individual",  # Change if your user type varies
            business_profile={
                "name": "United Chauffeur",
                "product_description": "Ride-sharing services",
            },
            
            tos_acceptance={
                "service_agreement": "full",
                "date": int(time.time()),  # Add current time in seconds
                "ip": ip_address or "0.0.0.0",  # Add IP address, fallback to default
            }
        )
        print("Connected account here.2")

        print(f"Connected account created successfully for {user.email}.")
        return connected_account.id

    except stripe.error.InvalidRequestError as e:
        print(f"Invalid request: {e.user_message}")
        raise e
    except stripe.error.AuthenticationError as e:
        print(f"Authentication error: {e.user_message}")
        raise e
    except stripe.error.APIConnectionError as e:
        print(f"Network error: {e.user_message}")
        raise e
    except stripe.error.StripeError as e:
        print(f"Stripe error: {e.user_message}")
        raise e
    except Exception as e:
        print(f"General error: {str(e)}")
        raise e







# =========== Create Wallet and 'connected account'=======2=====
def create_wallet_and_connected_account(user):
    """
    Creates a wallet for the user based on their service type and a connected account if needed.
    """
    try:
        if not user.service:
            raise ValidationError("User service type is not specified.")
        
        wallet = None
        created = False
        
        print("User Service is: ", user.service)

        # Map service types to corresponding wallet models
        if user.service == Services.united_chauffeur:
            print(f"Creating wallet for {Services.united_chauffeur} service.")
            wallet, created = ClientWallet.objects.get_or_create(user=user)
        
        elif user.service == Services.united_rydr_driver:
            print(f"Creating wallet for {Services.united_rydr_driver} service.")
            wallet, created = DriverWallet.objects.get_or_create(user=user)

        # Add additional service cases as needed here
        elif user.service in [
            Services.concierge_service,
            Services.united_rydr_client,
            Services.chauffeurs_driven,
            Services.kingdom_chauffeur,
            Services.royal_chauffeur,
            Services.city_chauffeur,
            Services.all_chauffeur_cars,
            Services.bro_cab,
            Services.buses,
            Services.echo_drive,
            Services.hello_mini_cab,
            Services.luxury_cruise_experience,
            Services.rainbow_chauffeurs,
            Services.redlimos,
            Services.royale_limousine_service,
            Services.street_mini_cabs,
        ]:
            print(f"Wallet creation for service type {user.service} is not implemented yet.")
            # raise NotImplementedError(f"Wallet creation for {user.service} is not supported.")
            pass

        else:
            print(f"Invalid service type: {user.service}")
            raise ValidationError(f"Invalid service type: {user.service}")

        # If a wallet was created or already exists, update Stripe customer info
        if wallet:
            wallet.stripe_customer_id = user.stripe_id
            wallet.save()

            try:
                # Create a connected account if not already created
                if not wallet.stripe_connected_account_id and user.service == Services.united_rydr_driver: #only for Driver
                    print("I am Here for Creating Connected Account")
                    connected_account_id = create_connected_account(user)
                    print("Connected account successfully create and id is: ", connected_account_id)
                    if connected_account_id:
                        wallet.stripe_connected_account_id = connected_account_id
                        wallet.save()
                        print(f"Connected account created: {connected_account_id}")
                    
            except Exception as e:
                print(f"=========Error while creating connected account: {str(e)}")
                '''
                **If you want to create a connected account for a user, 
                you can use the create_connected_account function.
                for handling the creation of the connected account.
                '''
                pass

        print(f"Wallet and connected account process completed for service type: {user.service}")
        return wallet

    except ValidationError as e:
        print(f"Validation Error: {str(e)}")
        raise e
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        raise e





def create_account_link(acc_id):
    res = stripe.AccountLink.create(
        account=acc_id,
        refresh_url="https://example.com/reauth",
        return_url="https://example.com/return",
        type="account_onboarding",
    )
    return res.url


def create_setup_intent(user):
    if not user.stripe_id:
        customer = stripe.Customer.create()
        user.stripe_id = str(customer.id)
        user.save()
    intent = stripe.SetupIntent.create(
        payment_method_types=["card"], customer=user.stripe_id
    )
    return intent.client_secret



card_logos = {
    "visa": "https://drive.google.com/uc?export=view&id=1ngjJ-okelAQ3Ir13dm6xKrIkdKJCC7Gb",
    "mastercard": "https://drive.google.com/uc?export=view&id=1Vayk-L92CjrGk-ZjYLIlxw9XEwnS3X4G",
    "amex": "https://drive.google.com/uc?export=view&id=1JOlwvY8oI6UlM6Pn1ymGft650ilEfumT",
    "discover": "https://drive.google.com/uc?export=view&id=15XnJS04RsVmf-cq5N6VMzRKUulwHYr-0",
    "diners_club": "https://drive.google.com/uc?export=view&id=190EAGJy6bE2p9TrpI99FllkcFJ6h3cNk",
    "jcb": "https://drive.google.com/uc?export=view&id=1mSqQ8bLXH-v4piIXDEH_FaOrH1n-4f_i",
    "maestro": "https://drive.google.com/uc?export=view&id=1LAaGfquaj5LHBdLYFMVkVhYapb3Kw0xF",
    "unionpay": "https://drive.google.com/uc?export=view&id=1KqWnslX1GytGrHWXNqZroiwf2DozWhNB",
    "solo": "https://drive.google.com/uc?export=view&id=1d1JVaarj4hVi4r1y46l5wPtccYPwMNnY",
    "visa_electron": "https://drive.google.com/uc?export=view&id=1mO9gzVqEDv0xhrFtKDChw7iRtDAe-ld7",
    "amazon": "https://drive.google.com/uc?export=view&id=12e-mldOXU7lB31q1fYEjB4uWL3ISfqyH",
    "circus": "https://drive.google.com/uc?export=view&id=1WYsLzWgEfw42DtYfQaPXgWJ1OQtj52HU",
    "direct_debit": "https://drive.google.com/uc?export=view&id=1VJSEYe-ZGk06dJURkVdNVZIQz2CQsU7e",
    "ebuy": "https://drive.google.com/uc?export=view&id=1RHijU04CEDx99Spmfls4fmYvleqDA1lV",
    "eway": "https://drive.google.com/uc?export=view&id=1jhWFM4fpzD41t2CcQcsC6mJwHcDUpBrC",
    "google_wallet": "https://drive.google.com/uc?export=view&id=1olVJNh1Kjw9yerZW_YsRG9tTW0rhWCuD",
    "moneybookers": "https://drive.google.com/uc?export=view&id=1BnClkJaWrDwlq5_QPGtYKAivwrDJJjE2",
    "paypal": "https://drive.google.com/uc?export=view&id=1rt-psVjKL-27PH8ZP5MjP_3P9o4r1-Hv",
    "sage": "https://drive.google.com/uc?export=view&id=11Zs7ryXwYXU2L7MAw45KxRIuuK6pmMv-",
    "shopify": "https://drive.google.com/uc?export=view&id=1ERlcbCMO-vaIx6SFpNTpolSJpPh8eI1z",
    "skrill": "https://drive.google.com/uc?export=view&id=1ucL9JgIgpIYVIJQyNNNOQFb2y5ZJbyfE",
    "worldpay": "https://drive.google.com/uc?export=view&id=1NLNT5dfS6IZWuGiWrIe5aqkZKy4dY1N1",
    "default": "https://drive.google.com/uc?export=view&id=1ngjJ-okelAQ3Ir13dm6xKrIkdKJCC7Gb"  # Add a generic card logo URL here
}



#================ Create Organization customer ID ===========
def create_organization_stripe_customer(organization): #not used still
    
    # Step 1: Create Stripe Customer for the organization (if not already created)
    if not organization.stripe_organization_id:
        customer = stripe.Customer.create(
            name=organization.name,
            email=organization.email,
        )
        organization.stripe_organization_id = customer['id']
        organization.save()

        return customer




# ===== *** ======= Create Stripe Customer and User Wallet =====(main)=====
def create_stripe_account(user):
    """
    Function to check if a Stripe account exists for the user.
    If not, create a new Stripe customer and wallet account based on the service type.
    """
    if not user.stripe_id:
        print("---------I am here-- 0--")
        try:
            # Create a new Stripe customer
            customer = create_stripe_customer(user) # 1
            user.stripe_id = str(customer.id)
            user.save()
            
            try:
                create_wallet_and_connected_account(user)
            except Exception as e:
                print(f"Error creating Stripe customer or wallet: {str(e)}")
                raise e

            print(f"Stripe customer and wallet created successfully for {user.email}.")
            return user.stripe_id

        except stripe.error.StripeError as e:
            print(f"Stripe error: {str(e)}")
            raise e

        except Exception as e:
            print(f"Error creating Stripe customer or wallet: {str(e)}")
            raise e
    else:
        print(f"User {user.email} already has a Stripe account with ID: {user.stripe_id}")
        print("---------I am here-- 0--")
        return user.stripe_id
    




def stipe_customer_id_validation_and_cross_check(user):
    if user.stripe_id == DriverWallet.objects.get(user=user).stripe_customer_id:
        print("User stripe cross check passed")
        return True
    else:
        print("User stripe cross check failed")
        return False
    
    
    
    
#================ Driver Account ======================

from driver_app.models import Driver


#1. Create Driver Stripe Account and Connect Account Link
def driver_stripe_account_create(user):
    # Create a Stripe Connect Custom Account for the driver
    driver = Driver.objects.get(user=user)
    print("Driver Account: ", driver)
    
    # Extract day, month, and year
    day = driver.date_of_birth.day
    month = driver.date_of_birth.month
    year = driver.date_of_birth.year
    print("date of brith: ", day, month, year)
    
    
    
    # Create the Connected Account
    account = stripe.Account.create(
        type='express',
        country='UK',
        email=user.email,
        capabilities={
                    "card_payments": {"requested": True},
                    "transfers": {"requested": True}
                },
        
        business_type='individual',
        individual={
            'first_name': user.full_name,
            'last_name': user.full_name,
            'dob': {
                'day': day,
                'month': month,
                'year': year,
            },
            'address': {
                'line1': driver.address,
                'city': driver.city,
                'postal_code': driver.postal_code,
                'country': driver.country,
            },
        },
        
        # tos_acceptance={"date": int(time.time()), "ip": ip_address},
    )
    return account



def driver_onboarding_link_account(account_id):
    """
    Generate an account onboarding link for the driver.
    """

    try:
        link = stripe.AccountLink.create(
            account=account_id,
            refresh_url="http://0.0.0.0:9090/api/payments/v1/driver/onboarding/refresh",
            return_url="http://0.0.0.0:9090/api/payments/v1/driver/onboarding/complete",
            type="account_onboarding",
        )
        return ({'url': link['url']})
    
    except Exception as e:
        print(f"Error creating account onboarding link: {str(e)}")
        return False





#2. Link Bank Account or Debit Card to Driver’s Account
def link_driver_bank_account(driver_account_id, bank_account_details):
    ''''
    bank_account_details should be a dictionary containing fields like 
    country, currency, account_holder_name, account_holder_type, routing_number, and account_number.
    '''
    # Create a bank account token
    bank_account_token = stripe.Token.create(
        bank_account=bank_account_details
    )
    
    # Attach the bank account to the driver's account
    external_account = stripe.Account.create_external_account(
        driver_account_id,
        external_account=bank_account_token.id
    )
    return external_account


# 3. Ensure Verification of Driver’s Account
def verify_driver_account(driver_account_id, verification_data):
    # Submit required documents or details to Stripe
    updated_account = stripe.Account.modify(
        driver_account_id,
        individual=verification_data  # Provide data like id_document, etc.
    )
    return updated_account


# 4. Set Up Payout Schedule
def setup_payout_schedule(driver_account_id, interval):
    '''
    interval can be "daily", "weekly", "monthly", or "manual".
    '''
    # Set up the payout schedule (e.g., daily, weekly, monthly, manual)
    updated_account = stripe.Account.modify(
        driver_account_id,
        settings={
            "payouts": {"schedule": {"interval": interval}}
        }
    )
    return updated_account


# 5. Request Payout with Custom Amount (With Balance Check)
def request_payout(driver_account_id, amount):
    '''
    This function checks the driver’s available balance and, if sufficient, initiates a payout.
    '''
    # Check the balance first
    driver_balance = stripe.Balance.retrieve(stripe_account=driver_account_id)
    available_balance = driver_balance["available"][0]["amount"]

    if available_balance < amount:
        return {"error": "Insufficient balance for payout."}

    # Create a payout if the balance is sufficient
    payout = stripe.Payout.create(
        amount=amount,
        currency="usd",
        stripe_account=driver_account_id
    )
    return payout





def get_the_user_wallet(user):
    
    if not user.stripe_id:
        raise ValidationError("User service type is not specified.")
    
    try:
        wallet = None

        print("User Service is: ", user.service)
        # Map service types to corresponding wallet models
        if user.service == Services.united_chauffeur:
            print(f"Creating wallet for {Services.united_chauffeur} service.")
            wallet = ClientWallet.objects.get(user=user)
        
        elif user.service == Services.united_rydr_driver:
            print(f"Creating wallet for {Services.united_rydr_driver} service.")
            wallet = DriverWallet.objects.get(user=user)

        # Add additional service cases as needed here
        elif user.service in [
            Services.concierge_service,
            Services.united_rydr_client,
            Services.chauffeurs_driven,
            Services.kingdom_chauffeur,
            Services.royal_chauffeur,
            Services.city_chauffeur,
            Services.all_chauffeur_cars,
            Services.bro_cab,
            Services.buses,
            Services.echo_drive,
            Services.hello_mini_cab,
            Services.luxury_cruise_experience,
            Services.rainbow_chauffeurs,
            Services.redlimos,
            Services.royale_limousine_service,
            Services.street_mini_cabs,
        ]:
            print(f"Wallet creation for service type {user.service} is not implemented yet.")
            # raise NotImplementedError(f"Wallet creation for {user.service} is not supported.")
            pass
        
        return wallet
    
    
    except Exception as e:
        print(f"Error creating Stripe customer or wallet: {str(e)}")
        raise e
    

    
