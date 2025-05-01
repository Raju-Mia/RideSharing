

# import uuid
# from django.utils import timezone
# import stripe
# from django.conf import settings
# from django.shortcuts import get_object_or_404

# from django.http import JsonResponse
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status
# from django.http import HttpResponseRedirect
# from django.views.decorators.csrf import csrf_exempt
# from decimal import Decimal

# from rest_framework.pagination import PageNumberPagination
# from rest_framework.permissions import IsAuthenticated


# #Import
# from organization_manager.models import Organization, OrganizationAccount, OrganizationTransaction
# from trip_management.models import PaymentStatus, TripStatus, Trip
# #Stripe
# stripe.api_key = settings.STRIPE_SECRET_KEY  # Use your Stripe secret key




# class CreatePaymentLinkView(APIView):  # Payment by payment link
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
        
#         print("============i am here===============")
#         # Get the authenticated user and organization
#         user = request.user
#         try:
#             organization = user.organization  # Access the related organization directly
#             print("Organization is:", organization)
#         except Organization.DoesNotExist:
#             return Response({"error": "Organization not found"}, status=status.HTTP_404_NOT_FOUND)

#         # Step 1: Create Stripe Customer for the organization (if not already created)
#         if not organization.stripe_organization_id:
#             try:
#                 customer = stripe.Customer.create(
#                     name=organization.name,
#                     email=organization.email,
#                 )
#                 organization.stripe_organization_id = customer['id']
#                 organization.save()
#             except stripe.error.StripeError as e:
#                 return Response({'error': f"Failed to create Stripe customer: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

#         # Step 2: Calculate total fare from trip IDs provided in the request data
#         trip_ids = request.data.get('trip_ids', [])
        
#         # # trip_ids = request.data.get('trip_ids', ['e240598b-f84e-4119-bcd8-ad39b230ede3/change', '69b103b1-89df-4c07-b196-a9923a2e8733'])
        
#         # # Get trip_ids from the request
#         # trip_ids = request.data.get('trip_ids', [
#         #     'e240598b-f84e-4119-bcd8-ad39b230ede3', 
#         #     '69b103b1-89df-4c07-b196-a9923a2e8733'
#         # ])
        
        
#         if not trip_ids:
#             return Response({'error': 'A list of trip IDs is required to calculate the total fare.'}, status=status.HTTP_400_BAD_REQUEST)

#         total_fare = self.calculate_total_fare(user, trip_ids)
#         print("=======total_fare==here===: ", total_fare)
        
#         if total_fare is None:
#             return Response({'error': 'Failed to calculate total fare. Please check trip IDs.'}, status=status.HTTP_400_BAD_REQUEST)

#         amount_in_cents = int(total_fare * 100)  # Convert to cents for Stripe

#         try:
#             # Step 3: Create a checkout session with the calculated fixed amount in GBP
#             checkout_session = stripe.checkout.Session.create(
#                 payment_method_types=['card'],
#                 customer=organization.stripe_organization_id,  # Use existing Stripe customer ID
#                 line_items=[{
#                     'price_data': {
#                         'currency': 'gbp',  # Currency in GBP
#                         'product_data': {
#                             'name': f"Payment for {organization.name}",
#                         },
#                         'unit_amount': amount_in_cents,
#                     },
#                     'quantity': 1,
#                 }],
#                 mode='payment',
#                 success_url=settings.PAYMENT_SUCCESS_URL,  # Your success page URL
#                 cancel_url=settings.PAYMENT_CANCEL_URL,  # Your cancel page URL
#                 billing_address_collection='auto',  # Optionally collect billing address
#                 metadata={  # Send organization ID and trip IDs as metadata for tracking
#                     'organization_id': str(organization.id),
#                     'trip_ids': ','.join(map(str, trip_ids)),  # Send trip IDs as comma-separated string
#                     'total_fare': str(total_fare),  # Send total fare for tracking
#                 }
#             )

#             # Return the Stripe-hosted checkout page URL
#             return Response({
#                 'status': 'success',
#                 'payment_url': checkout_session.url,
#             }, status=status.HTTP_200_OK)

#         except stripe.error.StripeError as e:
#             return Response({'error': f"Failed to create payment session: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

#     def calculate_total_fare(self, user, trip_ids):
#         """
#         Calculates the total fare based on a list of trip IDs and the authenticated user.
#         """
#         try:
#             # Assuming you have a Trip model with a 'fare' field
#             trips = Trip.objects.filter(user=user, id__in=trip_ids, trip_status=TripStatus.COMPLETED)
#             print("=======trips count=====: ", trips.count())
            
#             total_fare = sum(trip.final_fare for trip in trips)
#             print("=======total_fare=====: ", total_fare)
#             return total_fare
#         except Exception as e:
#             print(f"Error calculating total fare: {str(e)}")
#             return None







# # views.py
# class PaymentSuccessView(APIView):
#     def get(self, request):
#         # Logic for successful payment
#         return Response({"message": "Payment was successful!"}, status=status.HTTP_200_OK)

# class PaymentCancelView(APIView):
#     def get(self, request):
#         # Logic for canceled payment
#         return Response({"message": "Payment was canceled!"}, status=status.HTTP_200_OK)





# class CreatePaymentSessionView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request, *args, **kwargs):
#         print("hellow")
#         # Get the authenticated user
#         user = request.user

#         try:
#             # Retrieve the organization related to the authenticated user
#             organization = user.organization  # Access the related organization directly
#             print("organization", organization)

#             if not organization:
#                 return Response({"error": "User is not associated with any organization"}, status=status.HTTP_400_BAD_REQUEST)

#             # Retrieve and validate the amount
#             amount_str = request.data.get('amount')  # Amount sent from client (as string)

#             try:
#                 amount = int(amount_str)  # Convert to integer
#             except (ValueError, TypeError):
#                 return Response({"error": "Invalid amount"}, status=status.HTTP_400_BAD_REQUEST)

#             if amount <= 0:
#                 return Response({"error": "Amount must be greater than zero"}, status=status.HTTP_400_BAD_REQUEST)

#             # Convert amount to pence (Stripe requires the smallest unit)
#             amount_in_pence = amount * 100

#             # Check if stripe_organization_id exists for the organization
#             if not organization.stripe_organization_id:
#                 # Create a Stripe organization account (if required)
#                 stripe_account = stripe.Account.create(type="express")
#                 organization.stripe_organization_id = stripe_account.id
#                 organization.save()

#             print("I am here---1")
#             # Create a Stripe payment session
#             line_items = [{
#                 'price_data': {
#                     'currency': 'gbp',  # Use GBP for pounds
#                     'product_data': {
#                         'name': 'Payment',
#                         'description': 'Payment for services',
#                     },
#                     'unit_amount': amount_in_pence,  # Amount in pence
#                 },
#                 'quantity': 1,
#             }]
            
#             print("I am here---2")
#             session = stripe.checkout.Session.create(
#                 payment_method_types=["card"],
#                 mode="payment",
#                 line_items=line_items,
                
#                 success_url=settings.PAYMENT_SUCCESS_URL,  # Defined in settings.py
#                 cancel_url=settings.PAYMENT_CANCEL_URL,  # Defined in settings.py
                
#                 payment_intent_data={
#                     "capture_method": "automatic",
#                     "metadata": {
#                         "organization_id": organization.id  # Pass organization ID as metadata
#                         # "organization_id": str(organization.id),  # Pass organization ID as metadata
#                         # "organization_name": organization.name,  # You can add more metadata if needed
#                     }
#                 }
#             )
#             print("I am here---3")
#             # Return the session URL for redirection
#             return Response({"session_url": session.url}, status=status.HTTP_200_OK)

#         except Organization.DoesNotExist:
#             return Response({"error": "Organization not found"}, status=status.HTTP_404_NOT_FOUND)
#         except Exception as e:
#             return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# #------------
# import requests
# from django.http import JsonResponse
# from django.views import View
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework.permissions import AllowAny
# from rest_framework import status
# from decimal import Decimal
# from urllib.parse import urlencode
# from django.shortcuts import redirect
# from urllib.parse import urlencode
# from django.shortcuts import redirect
# import json

# import logging
# logger = logging.getLogger(__name__)

# from django.shortcuts import redirect
# from django.urls import reverse
# import uuid






# class SubscriptionPaymentView(APIView):
#     permission_classes = [permissions.IsAuthenticated]

#     def post(self, request, *args, **kwargs):
#         user = request.user  # Ensure user is authenticated
#         print("User is ", user)
#         data = request.data

#         try:
#             # Validate subscription plan
#             subscription_plan_id = data.get("subscription_plan")
#             subscription_type = data.get("subscription_type")
#             coupon_code = data.get("coupon_code")
#             request_source = data.get("request_source") or "android" #New Add

#             subscription_plan = SubscriptionPlan.objects.filter(id=subscription_plan_id, is_active=True).first()
#             if not subscription_plan:
#                 return Response({"error": "Invalid or inactive subscription plan."}, status=status.HTTP_400_BAD_REQUEST)

#             # # Apply coupon if provided
#             # if coupon_code:
#             #     if subscription_plan.coupon_code != coupon_code or not subscription_plan.coupon_status:
#             #         return Response({"error": "Invalid or expired coupon code."}, status=status.HTTP_400_BAD_REQUEST)

#             #     # Apply discount
#             #     discount_amount = subscription_plan.discount_price or 0
#             # else:
#             #     discount_amount = 0


#             # Apply coupon if provided
#             discount_amount = 0
#             if coupon_code:
#                 coupon = Coupon.objects.filter(code=coupon_code, is_active=True).first()
#                 if not coupon:
#                     return Response({"message": "Invalid or expired coupon code."}, status=status.HTTP_400_BAD_REQUEST)
                
#                 if coupon:
#                     if not coupon.is_valid():
#                         return Response({"message": "Coupon code is no longer valid."}, status=status.HTTP_400_BAD_REQUEST)

#                     # Ensure the subscription plan matches the coupon type
#                     if subscription_type != coupon.type:
#                         return Response({"message": "Coupon code does not apply to this subscription type."}, status=status.HTTP_400_BAD_REQUEST)

#                     # Apply discount
#                     if coupon.discount_type == 'flat':
#                         discount_amount = Decimal(coupon.discount_value)
#                     elif coupon.discount_type == 'percent':
#                         print("Percentage here i am ")
#                         # Convert subscription_plan.price and coupon.discount_value to Decimal
#                         discount_amount = (Decimal(subscription_plan.price) * Decimal(coupon.discount_value)) / Decimal(100)
#                         print("Monthly discount is:", discount_amount)

#                         if coupon.type == "yearly":
#                             discount_amount = discount_amount * Decimal(12)  # Use Decimal multiplication
#                             print("Yearly discount is:", discount_amount)



            

#             # Calculate final price
#             total_price = subscription_plan.final_total_price or 0
#             print("total_price======", total_price)
#             if subscription_type == "yearly":
#                 total_price = Decimal(total_price * 12)
#             final_price = Decimal(total_price - discount_amount)


#         except Exception as e:
#             return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)





#         user_id = user.user_id
#         user_name = user.full_name
#         # user_email = user.email
#         user_phone = user.phone_number
#         user_address = user.address
#         product_name = subscription_plan.title
#         product_price = final_price
#         subscription_plan_id = subscription_plan_id  # Get subscription_plan_id
#         transaction_id = str(uuid.uuid4())  # Unique transaction ID
#         subscription_type = subscription_type

#         settings = {
#             "store_id": "miiic6772383282c75",
#             "store_pass": "miiic6772383282c75@ssl",
#             "issandbox": True
#         }
#         sslcz = SSLCOMMERZ(settings)


#         print("user_id=======", user_id)

#         print("product_price", product_price)

#         post_body = {
#             "total_amount": product_price,
#             "currency": "BDT",
#             "tran_id": transaction_id,

#             # "success_url": request.build_absolute_uri(reverse('payments:payment-success')),
#             # "fail_url": request.build_absolute_uri(reverse('payments:payment-fail')),
#             # "cancel_url": request.build_absolute_uri(reverse('payments:payment-cancel')),

#             "success_url": request.build_absolute_uri(reverse('payments:payment-success')).replace("http://", "https://"),
#             "fail_url": request.build_absolute_uri(reverse('payments:payment-fail')).replace("http://", "https://"),
#             "cancel_url": request.build_absolute_uri(reverse('payments:payment-cancel')).replace("http://", "https://"),

            
#             "emi_option": 0,
#             "cus_name": (user_name, "Customer Name"),
#             "cus_email": request.data.get("cus_email", "test@test.com"),
#             "cus_phone": (user_phone, "01700000000"),

#             "cus_add1": (user_address, "Customer Address"),
#             "cus_city": request.data.get("cus_city", "Dhaka"),
#             "cus_country": request.data.get("cus_country", "Bangladesh"),
#             "shipping_method": "NO",
#             "multi_card_name": "",
#             "num_of_item": 1,
#             "product_name": product_name,
#             "product_category": "Test Category",
#             "product_profile": "general",
#             "value_a": subscription_plan_id,  # Include subscription_plan_id in value_a
#             "value_b": subscription_type,
#             "value_c": user_id,
#             "value_d": request_source,
#             "subscription_id": "acb",
#         }

#         response = sslcz.createSession(post_body)  # API response

#         # Handle the API response
#         if response.get("status") == "SUCCESS":
#             return JsonResponse({
#                 "status": "SUCCESS",
#                 "gateway_url": response["GatewayPageURL"],
#                 "subscription_plan_id": subscription_plan_id  # Send back to client
#             })
#         else:
#             return JsonResponse({
#                 "status": "FAILED",
#                 "message": response.get("failedreason", "Something went wrong.")
#             }, status=400)





# class PaymentSuccessView(APIView):
#     permission_classes = [AllowAny]
    
#     def post(self, request):
#         # Process payment success details
#         data = request.data  # Incoming payment success data
#         # print("date is: ======", data)
#         if data['status'] == 'VALID':
#             # Retrieve subscription_plan_id from value_a and ensure it's a string
#             subscription_plan_id = str(data.get("value_a", ""))  # Use empty string if value_a is missing
#             subscription_type = data.get("value_b", "monthly")
#             total_price = data.get("total_amount", 0)
#             user_id = data.get("value_c", "")

#             tran_id = data.get("tran_id", "")
#             val_id = data.get("val_id", "")
#             bank_tran_id = data.get("bank_tran_id", "")
#             verify_sign = data.get("verify_sign", "")
#             verify_sign_sha2 = data.get("verify_sign_sha2", "")
#             amount = data.get("amount", "")
#             card_type = data.get("card_type", "")
#             store_amount = data.get("store_amount", "")
#             card_no = data.get("card_no", "")
#             status = data.get("status", "")
#             tran_date = data.get("tran_date", "")
#             error = data.get("error", "")
#             currency = data.get("currency", "")
#             card_issuer = data.get("card_issuer", "")
#             card_brand = data.get("card_brand", "")
#             status = data.get("status", "")

#             request_source = data.get("value_d", "")

            
            


            
#             # Fetch the subscription plan
#             print("subscription_plan_id", subscription_plan_id)
#             subscription_plan = SubscriptionPlan.objects.get(id=subscription_plan_id)
#             print("subscription_plan: ", subscription_plan)

#             # Fetch the user and the current active subscription
#             user = CustomUser.objects.get(user_id=user_id)
#             print("user", user)
#             current_active_subscription = Subscription.objects.filter(user=user, active_status=True).first()
#             print("Now current Plan is: ", current_active_subscription)

#             # Determine the current active subscription end date
#             current_active_subscription_end_date = (
#                 current_active_subscription.end_date if current_active_subscription else None
#             )

#             # Set the start date for the new subscription
#             start_date = timezone.now()
#             if current_active_subscription_end_date and current_active_subscription_end_date > timezone.now():
#                 # If there's an active subscription with an end date in the future, set the start date to its end date
#                 start_date = current_active_subscription_end_date



#             # Determine the duration of the subscription
#             duration_days = subscription_plan.days_duration or 30  # Default to 30 days
#             duration_of_month = 1
#             if subscription_type == "yearly":
#                 duration_days = 365
#                 duration_of_month = 12

#             # Calculate the end date
#             end_date = start_date + timedelta(days=duration_days)

#             print("New subscription start date:", start_date)
#             print("New subscription end date:", end_date)
#             print("days duration:", duration_days)



#             # Ols Subscription active_status False
#             print("-----now all old subscription inactive---1--")
#             print("----current_active_subscription: ", current_active_subscription)
#             if current_active_subscription is not None:
#                 current_active_subscription.active_status = False
#                 current_active_subscription.subscription_status = False
#                 current_active_subscription.free_trial_status = False
#                 current_active_subscription.save()
#             print("-----now all old subscription inactive--2---")




#             # <QueryDict: {'tran_id': ['5c443bb3-93ae-422b-87b8-c0a18b86bdff'], 'val_id': ['250107144829kVhRmzBmPEUyjRp'], 'amount': ['2500.00'], 'card_type': ['ABBANKIB-AB Bank'], 'store_amount': ['2437.50'], 'card_no': [''], 'bank_tran_id': ['250107144829Mx6bqiYhoGdzgx9'], 'status': ['VALID'], 'tran_date': ['2025-01-07 14:48:22'], 'error': [''], 'currency': ['BDT'], 'card_issuer': ['AB Bank Limited'], 'card_brand': ['IB'], 'card_sub_brand': ['Classic'], 'card_issuer_country': ['Bangladesh'], 'card_issuer_country_code': ['BD'], 'store_id': ['miiic6772383282c75'], 'verify_sign': ['a2f65f22b604fd0dc9f246d0ff9b8268'], 'verify_key': ['amount,bank_tran_id,base_fair,card_brand,card_issuer,card_issuer_country,card_issuer_country_code,card_no,card_sub_brand,card_type,currency,currency_amount,currency_rate,currency_type,error,risk_level,risk_title,status,store_amount,store_id,tran_date,tran_id,val_id,value_a,value_b,value_c,value_d'], 'verify_sign_sha2': ['7f67e2b0d531e05295d271dd382420685d313a4798c8cd2384b4206e3b1511fc'], 'currency_type': ['BDT'], 'currency_amount': ['2500.00'], 'currency_rate': ['1.0000'], 'base_fair': ['0.00'], 'value_a': ['9784d0b6-01b6-4c35-b512-9ffdaa6312bc'], 'value_b': ['monthly'], 'value_c': ['1b862c73-9628-4542-a8ac-613aa9f31f6b'], 'value_d': ['ffff'], 'subscription_id': [''], 'risk_level': ['0'], 'risk_title': ['Safe']}



#             # Subscription Create =============
#             print("=========total_price: ", total_price)
#             subscription = Subscription.objects.create(
#                 user=user,
#                 subscription_plan=subscription_plan,
#                 subscription_type=subscription_type,
#                 payment_status = True,
#                 payment_date = timezone.now().date(),
#                 payment_time = timezone.now().time(),

#                 transaction_status = True,
#                 payment_method = card_type,
#                 # payment_account_number = int(card_no),
                
#                 price=total_price,
#                 # discount_amount=discount_amount,
#                 # total_price = total_price,
#                 final_total_price=amount, #total_price

#                 start_date=start_date,
#                 end_date=end_date,
#                 total_days = duration_days,
#                 duration_of_month = duration_of_month,

#                 currency_type = currency,
#                 active_status=True,
#             )

#             print("subscription Create Succesfully!")

#             # Transaction Create
#             transaction = Transaction.objects.create(
#                 user=user,
#                 subscription=subscription,
#                 amount = amount,
#                 store_amount = store_amount,
#                 tran_id = tran_id,
#                 val_id = val_id,
#                 bank_tran_id = bank_tran_id,
#                 verify_sign = verify_sign,
#                 verify_sign_sha2 = verify_sign_sha2,
#                 status = status

#             )

#             print("Transaction Create Succesfully!")

           
            
#             # Prepare the response data, ensuring subscription_plan_id is added correctly
#             subscription_data = SubscriptionCreateSerializer(subscription)
#             transaction_data = TransactionCreateSerializer(transaction)


#             # response_data = {
#             #     "message": "Payment Successful",
#             #     "subscription_data": subscription_data.data,
#             #     "transaction_data": transaction_data.data,
#             #     "user": {
#             #             "id": subscription.user.user_id,
#             #             "phone": subscription.user.phone_number,
#             #             # "email": subscription.user.email,
#             #         }
#             # }
#             # return Response(response_data, status=200)
            

#             # Serialize nested data into JSON strings for compatibility with URL parameters
#             if request_source == "web":
#                 print("i am  here--1")
#                 print("request_source is: ", request_source)
#                 # Prepare the query parameters
#                 query_params = {
#                     "subscription_plan": subscription.subscription_plan.title,
#                     "subscription_type": subscription.subscription_type,
#                     "start_date": subscription.start_date,
#                     "end_date": subscription.start_date,
#                     "total_cost": subscription.final_total_price,
#                     "amount": amount,
#                     "tran_id": tran_id,
#                     "auto_renew": subscription.auto_renew,
#                 }

#                 # Base URL for redirection
#                 # base_url = "http://0.0.0.0:8090/api/package/migration-success"
#                 base_url = "http://192.168.0.8:3000/package/migration-success"

#                 # http://192.168.0.8:3000/package/migration-success?start_date=31/01/2025&end_date=31/01/2025&auto_renew=false&total_cost=2500&tran_id=354657688097

#                 # Encode the query parameters
#                 query_string = urlencode(query_params)

#                 # Construct the final URL
#                 redirect_url = f"{base_url}?{query_string}"

#                 # Redirect to the constructed URL
#                 return redirect(redirect_url)
            
#             else:
#                 response_data = {
#                     "message": "Payment Successful",
#                     "subscription_data": subscription_data.data,
#                     "transaction_data": transaction_data.data,
#                     "user": {
#                             "id": subscription.user.user_id,
#                             "phone": subscription.user.phone_number,
#                             # "email": subscription.user.email,
#                         }
#                 }
#                 return Response(response_data, status=200)
        


#         return Response({'message': 'Payment validation failed'}, status=400)





# class PaymentCancelView(APIView):
#     permission_classes = [AllowAny]

#     def post(self, request):
#         # Process payment cancellation details
#         data = request.data  # Incoming payment cancellation data

        

#         if data['status'] == 'CANCELLED':

#             # Retrieve subscription_plan_id from value_a and ensure it's a string
#             error = data.get("error", "")
#             request_source = data.get("value_d", "")



#             # Prepare the response data with cancellation message
#             response_data = {
#                 "message": "Payment was cancelled",
#                 "data": {
#                     "tran_id": data.get("tran_id"),
#                     "val_id": data.get("val_id"),
#                     "amount": data.get("amount"),
#                     "card_type": data.get("card_type"),
#                     "store_amount": data.get("store_amount"),
#                     "card_no": data.get("card_no", ""),
#                     "bank_tran_id": data.get("bank_tran_id"),
#                     "status": data.get("status"),
#                     "tran_date": data.get("tran_date"),
#                     "error": data.get("error", ""),
#                     "currency": data.get("currency"),
#                     "card_issuer": data.get("card_issuer"),
#                     "card_brand": data.get("card_brand"),
#                     "card_sub_brand": data.get("card_sub_brand"),
#                     "card_issuer_country": data.get("card_issuer_country"),
#                     "card_issuer_country_code": data.get("card_issuer_country_code"),
#                     "store_id": data.get("store_id"),
#                     "verify_sign": data.get("verify_sign"),
#                     "verify_key": data.get("verify_key"),
#                     "verify_sign_sha2": data.get("verify_sign_sha2"),
#                     "currency_type": data.get("currency_type"),
#                     "currency_amount": data.get("currency_amount"),
#                     "currency_rate": data.get("currency_rate"),
#                     "base_fair": data.get("base_fair"),
#                     "value_a": data.get("value_a"),
#                     "value_b": data.get("value_b"),
#                     "value_c": data.get("value_c"),
#                     "value_d": data.get("value_d"),
#                     "subscription_id": data.get("subscription_id", ""),
#                     "risk_level": data.get("risk_level"),
#                     "risk_title": data.get("risk_title"),
#                     "subscription_plan_id": str(data.get("value_a", "")),  # Ensure it's a string
#                 }
#             }

#             # Serialize nested data into JSON strings for compatibility with URL parameters
            
#             if request_source == "web":
#                 print("i am  here--1")
#                 print("request_source is: ", request_source)

                
#                 # Prepare the query parameters
#                 query_params = {
#                     "cancel_message": error,
#                     # "amount": amount,
#                 }

#                 # base_url = "http://192.168.0.8:3000/package/ccf0d50a-d4eb-4a77-83ff-51e817df7478?cancel_message=Purchasing Process Cancelled"
#                 # Prepare the base URL with the subscription_plan_id dynamically included
#                 subscription_plan_id = data.get("value_a", "")  # Ensure it's retrieved dynamically
#                 base_url = f"http://192.168.0.8:3000/package/{subscription_plan_id}"
#                 print("base_url: ", base_url)


#                 # Encode the query parameters
#                 query_string = urlencode(query_params)

#                 # Construct the final URL
#                 redirect_url = f"{base_url}?{query_string}"

#                 # Redirect to the constructed URL
#                 return redirect(redirect_url)
            
#             else:
#                 return Response(response_data, status=200)
    
#         return Response({'message': 'Payment was cancelled', 'data': request.data})



# class PaymentFailView(APIView):
#     permission_classes = [AllowAny]

#     def post(self, request):
#         # Process payment failure details
#         data = request.data  # Incoming payment failure data
        

#         if data['status'] == 'FAILED':
#             # Prepare the response data with failure message


#             # Retrieve subscription_plan_id from value_a and ensure it's a string
#             subscription_plan_id = str(data.get("value_a", ""))  # Use empty string if value_a is missing
#             subscription_type = data.get("value_b", "monthly")
#             total_price = data.get("total_amount", 0)
#             error = data.get("error", "")
#             amount = data.get("amount", "")
#             request_source = data.get("value_d", "")




#             # Subscription Create =============
#             print("=========total_price: ", total_price)
#             subscription_plan = SubscriptionPlan.objects.get(id=subscription_plan_id)
#             print("---sub plan: ", subscription_plan)




#             response_data = {
#                 "message": "Payment failed",
#                 "data": {
#                     "tran_id": data.get("tran_id"),
#                     "val_id": data.get("val_id"),
#                     "amount": data.get("amount"),
#                     "card_type": data.get("card_type"),
#                     "store_amount": data.get("store_amount"),
#                     "card_no": data.get("card_no", ""),
#                     "bank_tran_id": data.get("bank_tran_id"),
#                     "status": data.get("status"),
#                     "tran_date": data.get("tran_date"),
#                     "error": data.get("error", ""),
#                     "currency": data.get("currency"),
#                     "card_issuer": data.get("card_issuer"),
#                     "card_brand": data.get("card_brand"),
#                     "card_sub_brand": data.get("card_sub_brand"),
#                     "card_issuer_country": data.get("card_issuer_country"),
#                     "card_issuer_country_code": data.get("card_issuer_country_code"),
#                     "store_id": data.get("store_id"),
#                     "verify_sign": data.get("verify_sign"),
#                     "verify_key": data.get("verify_key"),
#                     "verify_sign_sha2": data.get("verify_sign_sha2"),
#                     "currency_type": data.get("currency_type"),
#                     "currency_amount": data.get("currency_amount"),
#                     "currency_rate": data.get("currency_rate"),
#                     "base_fair": data.get("base_fair"),
#                     "value_a": data.get("value_a"),
#                     "value_b": data.get("value_b"),
#                     "value_c": data.get("value_c"),
#                     "value_d": data.get("value_d"),
#                     "subscription_id": data.get("subscription_id", ""),
#                     "risk_level": data.get("risk_level"),
#                     "risk_title": data.get("risk_title"),
#                     "subscription_plan_id": str(data.get("value_a", "")),  # Ensure it's a string
#                 }
#             }

#             # Serialize nested data into JSON strings for compatibility with URL parameters
            
#             if request_source == "web":
#                 print("i am  here--1")
#                 print("request_source is: ", request_source)
#                 # Prepare the query parameters
#                 query_params = {
#                     "subscription_plan": subscription_plan.title,
#                     "failed_reason": error,
#                     "amount": amount,
#                 }

#                 # Base URL for redirection
#                 # base_url = "http://0.0.0.0:8090/api/package/migration-success"
#                 # base_url = "http://192.168.0.8:3000/package/migration-failed?subscription_plan=Standard&failed_reason=Issuer Bank Declined&amount=440"
#                 base_url = "http://192.168.0.8:3000/package/migration-failed"

#                 # http://192.168.0.8:3000/package/migration-success?start_date=31/01/2025&end_date=31/01/2025&auto_renew=false&total_cost=2500&tran_id=354657688097

#                 # Encode the query parameters
#                 query_string = urlencode(query_params)

#                 # Construct the final URL
#                 redirect_url = f"{base_url}?{query_string}"

#                 # Redirect to the constructed URL
#                 return redirect(redirect_url)
            
#             else:

#                 return Response(response_data, status=200)

#         return Response({'message': 'Payment failed'}, status=400)




# from django.shortcuts import render
# from django.http import HttpResponseServerError

# def PaymentSuccessMessageView(request):
#     try:
#         return render(request, "success_message.html", {"foo": "bar"}, content_type="text/html")
#     except Exception as e:
#         return HttpResponseServerError(f"Error rendering page: {str(e)}")


