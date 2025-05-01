import stripe
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY  # Ensure this is in your settings

class CreateStripeConnectAccount(APIView):
    def post(self, request):
        # Assume driver details are passed in the request payload
        driver_data = request.data
        try:
            # Create a Stripe Custom Connect Account for the driver
            account = stripe.Account.create(
                type="custom",
                country="US",  # Set the driver's country
                email=driver_data["email"],  # Driver's email
                business_type="individual",  # Or "company" if relevant
                capabilities={
                    "card_payments": {"requested": True},
                    "transfers": {"requested": True},
                },
                tos_acceptance={
                    "date": int(time.time()),
                    "ip": request.META.get("REMOTE_ADDR"),  # Driver’s IP address
                },
                business_profile={
                    "mcc": "4121",  # Merchant category code for ride-sharing
                    "url": "https://your-ride-sharing-platform.com",  # Your platform's URL
                }
            )

            # Return the newly created account ID
            return Response({"account_id": account.id}, status=status.HTTP_201_CREATED)

        except stripe.error.StripeError as e:
            # Handle Stripe API errors
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

# {
#     "email": "driver@example.com"
# }



# Step 1: Verify and Connect the Driver's Account
# # Create or retrieve the driver’s Stripe Connect account
# stripe.Account.create(
#     type="custom",
#     country="US",  # or driver's country
#     email=driver_email,
#     business_type="individual",
#     requested_capabilities=["transfers"],
#     tos_acceptance={"date": int(time.time()), "ip": request.META["REMOTE_ADDR"]}
# )


# Step 3: Check the Driver's Account Balance
# driver_balance = stripe.Balance.retrieve(stripe_account=driver_account_id)
# available_balance = driver_balance["available"][0]["amount"]  # In cents


# Step 4: Initiate the Payout
# # Example: Payout £500 (50,000 pence/cents) from driver’s balance
# payout_amount = 500 * 100  # in pence or cents

# if available_balance >= payout_amount:
#     stripe.Payout.create(
#         amount=payout_amount,  # In cents/pence
#         currency="gbp",
#         description="Payout to driver for ride-sharing earnings",
#         stripe_account=driver_account_id
#     )
# else:
#     print("Insufficient balance for payout.")



# step: 4 Checking and Configuring Payout Schedule

# # Example: Set up an automatic weekly payout schedule for the driver
# stripe.Account.modify(
#     driver_account_id,
#     settings={
#         "payouts": {
#             "schedule": {"interval": "weekly"},
#             "statement_descriptor": "RideShare Earnings"
#         }
#     }
# )






import stripe
from django.conf import settings
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status

stripe.api_key = settings.STRIPE_SECRET_KEY

@api_view(["POST"])
def distribute_funds(request):
    data = request.data
    total_amount = data.get("amount")  # in cents, e.g., $10 would be 1000
    driver_account_id = data.get("driver_account_id")  # Driver's Stripe Connect account ID

    try:
        # Calculate split amounts (assuming `total_amount` is in cents)
        driver_amount = int(total_amount * 0.8)  # 80% to the driver
        platform_fee = int(total_amount * 0.2)   # 20% retained by the platform

        # Create a PaymentIntent with the application fee and transfer details
        payment_intent = stripe.PaymentIntent.create(
            amount=total_amount,
            currency="usd",
            payment_method_types=["card"],
            transfer_data={
                "destination": driver_account_id,  # Driver's account for 80% of the fare
                "amount": driver_amount,
            },
            application_fee_amount=platform_fee,  # Platform fee amount (20% of total fare)
            description="Ride fare distribution",
        )

        # Return the client_secret of the payment intent to confirm payment on the frontend
        return Response({
            "client_secret": payment_intent.client_secret,
            "payment_intent_id": payment_intent.id
        }, status=status.HTTP_201_CREATED)

    except stripe.error.StripeError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# {
#     "amount": 1000,  # Total fare in cents, e.g., $10.00
#     "driver_account_id": "acct_driverStripeConnectID"  # Replace with driver's actual Stripe Connect ID
# }
