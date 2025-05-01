# from accounts.models import Employee
from http.client import HTTPException

import stripe
from uc_back import settings
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView
# from stripe.error import InvalidRequestError
from payment.helpers import create_account_link, is_stripe_customer
from payment.serializers import CardSerializer
from trip_management.models import Trip



User = get_user_model()

# Stripe Account Secret Key
stripe.api_key = settings.STRIPE_SECRET_KEY


# class CheckoutSession(APIView):  # nedd to empliment
#     def get(self, request, trip_id):
#         print('You dont have stripe ID ', request.user.stripe_id or ' ') 

#         trip = get_object_or_404(Trip, id=trip_id)
#         checkout_session = stripe.checkout.Session.create(
#             customer_email=trip.user.email,
#             payment_method_types=["card"],
#             line_items=[
#                 {
#                     "price_data": {
#                         "currency": "usd",
#                         "product_data": {
#                             "name": trip.pickup_location_name,
#                         },
#                         "unit_amount": int(trip.fare),
#                     },
#                     "quantity": 1,
#                 }
#             ],
#             mode="payment",
#             success_url=settings.CHECKOUT_SUCCESS_URL,
#             cancel_url=settings.CHECKOUT_FAILED_URL,
#         )
#         return Response(checkout_session.url, status=status.HTTP_200_OK)


# class CreatePaymentIntent(APIView):  # need to impliment
#     def get(self, request, trip_id):
#         print('You dont have stripe ID ', request.user.stripe_id or ' ') 

#         trip = get_object_or_404(Trip, id=trip_id)
#         intent = stripe.PaymentIntent.create(
#             amount=int(trip.fare),
#             currency="gbp",
#             automatic_payment_methods={"enabled": True},
#             metadata={"trip_id": str(trip.id)},
#         )
#         return Response(intent.client_secret)


# class SaveCustomerInfo(APIView):  # done
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         print('You dont have stripe ID ', request.user.stripe_id or ' ') 

#         user = self.request.user
#         if is_stripe_customer(user):
#             return Response(status=status.HTTP_403_FORBIDDEN)
#         customer = stripe.Customer.create()
#         user.stripe_id = str(customer.id)
#         user.save()
#         intent = stripe.SetupIntent.create(
#             payment_method_types=["card"], customer=str(customer.id)
#         )
#         data = {"client_secret": intent.client_secret}
#         return Response(data, status=status.HTTP_200_OK)


# class CreateStripeCustomer(APIView):  # done perhaps 1
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         user = request.user
#         if user.stripe_id:
#             return Response({"detail": "Stripe customer already exists."}, status=status.HTTP_403_FORBIDDEN)

#         try:
#             customer = stripe.Customer.create(email=user.email)
#             user.stripe_id = str(customer.id)
#             user.save()
            
            
#             return Response({"detail": "Stripe customer created successfully."}, status=status.HTTP_201_CREATED)
#         except stripe.error.StripeError as e:
#             return Response({"detail": f"Stripe error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
#         except Exception as e:
#             return Response({"detail": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)






# class UserIsStripeCustomer(APIView):  # done
#     def get(self, request):
#         print('You dont have stripe ID ', request.user.stripe_id or ' ') 

#         out = {"is_stripe_customer": True if self.request.user.stripe_id else False}
#         print(
#             "hello there ",
#             {"is_stripe_customer": True if self.request.user.stripe_id else False},
#         )
#         return Response(out, status=status.HTTP_200_OK)


# class CreatePaymentMethod(APIView):  # done 2
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         user = self.request.user
#         if not request.user.stripe_id:
#             customer = stripe.Customer.create()
#             self.request.user.stripe_id = str(customer.id)
#             self.request.user.save()
#         serializer = CardSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         try:
#             out = stripe.PaymentMethod.create(
#                 type="card", card=serializer.data)
#             try:
#                 stripe.PaymentMethod.attach(out.id, customer=user.stripe_id)
#                 return Response(
#                     {"detail": "Card added successfully"},
#                     status=status.HTTP_201_CREATED,
#                 )
#             except Exception as e:
#                 return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
#         except Exception as e:
#             return Response(str(e), status=status.HTTP_400_BAD_REQUEST)




# class AddNewCard(APIView):  # need to impliment 3
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         if not request.user.stripe_id:
#             customer = stripe.Customer.create()
#             self.request.user.stripe_id = str(customer.id)
#             self.request.user.save()
#             print("Create stripe account!")
#         intent = stripe.SetupIntent.create(
#             payment_method_types=["card"], customer=str(request.user.stripe_id)
#             )
#         data = {"client_secret": intent.client_secret}
#         return Response(status=status.HTTP_200_OK, data=data)


#     def post(self, request):
#         print('-----------------1---------------')
#         user = request.user
#         print('-----------------2---------------')

#         if not user.stripe_id:
#             print('-----------------3---------------')
#             try:
#                 customer = stripe.Customer.create(email=user.email, name=user.full_name)
#                 print('-----------------4---------------')
#                 user.stripe_id = customer.id
#                 user.save()
#                 print('-----------------5---------------')
#             except stripe.error.StripeError as e:
#                 print(f'Error creating customer: {e}')
#                 return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

#         print('Request Data:', request.data)
#         card_data = request.data
#         print('-----------------6---------------')

#         try:
#             payment_methods = stripe.PaymentMethod.list(
#                 customer=user.stripe_id, type="card"
#             ).data
#             print(payment_methods)
#             print('-----------------7---------------')
            
#             payment_method = stripe.PaymentMethod.create(
#                 type="card",
#                 card={
#                     "number": card_data.get("number"),
#                     "exp_month": card_data.get("exp_month"),
#                     "exp_year": card_data.get("exp_year"),
#                     "cvc": card_data.get("cvc"),
#                 },
#             )
            
#             # payment_method = stripe.PaymentMethod.create(
#             #     type="card",
#             #     card={
#             #         "number": card_data.get("number"),
#             #         "exp_month": card_data.get("exp_month"),
#             #         "exp_year": card_data.get("exp_year"),
#             #         "cvc": card_data.get("cvc"),
#             #     },
#             #     billing_details={
#             #         "name": card_data.get("name"),  # Cardholder's name
#             #         "address": {
#             #             "country": card_data.get("country"),  # Cardholder's country
#             #         }
#             #     }
#             # )



#             print('--------8------')

#             stripe.PaymentMethod.attach(
#                 payment_method.id, customer=user.stripe_id
#             )
#             print('--------9--------')

#             if not payment_methods:
#                 stripe.Customer.modify(
#                     user.stripe_id,
#                     invoice_settings={
#                         "default_payment_method": payment_method.id
#                     },
#                 )
#                 print('------------10------------')
#                 message = "Primary card added successfully"
#             else:
#                 print('--------11--------')
#                 message = "Card added successfully"

#             return Response({"detail": message}, status=status.HTTP_201_CREATED)

#         except stripe.error.StripeError as e:
#             print(f'Error handling payment method: {e}')
#             return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        






# class ViewUserCardsInfo(APIView):  # done ======= Old main ==========
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         print('You dont have stripe ID ', request.user.stripe_id or ' ') 

#         try:
#             if not self.request.user.stripe_id:
#                 customer = stripe.Customer.create()
#                 self.request.user.stripe_id = str(customer.id)
#                 self.request.user.save()
#             customer = stripe.Customer.retrieve(request.user.stripe_id)
#             payment_methods = stripe.PaymentMethod.list(
#                 customer=customer.id, type="card"
#             )
#             payment_method_objects = payment_methods.data
#             payload = []
#             for payment_method in payment_method_objects:
#                 payload.append(
#                     {
#                         "id": payment_method.id,
#                         "brand": payment_method.card.brand,
#                         "last4": payment_method.card.last4,
#                         "exp_month": payment_method.card.exp_month,
#                         "exp_year": payment_method.card.exp_year,
#                         "funding": payment_method.card.funding,
#                         "logo": "https://drive.google.com/uc?export=view&id=1Vayk-L92CjrGk-ZjYLIlxw9XEwnS3X4G",
#                         "is_primary": payment_method.id
#                         == customer.invoice_settings.default_payment_method,
#                     }
#                 )
#             payload.sort(key=lambda x: not x['is_primary'])

#             return Response({"cards": payload}, status=status.HTTP_200_OK)
#         except stripe.error.StripeError as e:
#             return Response(status=status.HTTP_400_BAD_REQUEST, data=str(e))








# class SetPrimaryCard(APIView):  # done
#     permission_classes = [IsAuthenticated]

#     def post(self, request, method_id):
#         print('You dont have stripe ID ', request.user.stripe_id or ' ') 

#         user = self.request.user
#         try:
#             _ = stripe.Customer.modify(
#                 user.stripe_id, invoice_settings={
#                     "default_payment_method": method_id}
#             )

#             return Response(
#                 {"message": "Primary card set successfully"}, status=status.HTTP_200_OK
#             )
#         except stripe.error.StripeError as e:
#             return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# class GetPrimaryCard(APIView):  # done
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         print('You dont have stripe ID ', request.user.stripe_id or ' ') 

#         user = self.request.user  # Access the user associated with the request

#         try:
#             customer = stripe.Customer.retrieve(user.stripe_id)
#             payment_methods = stripe.PaymentMethod.list(
#                 customer=customer.id, type="card"
#             )
#             payment_method_objects = payment_methods.data
#             payload = {}
#             for payment_method in payment_method_objects:
#                 if (
#                     payment_method.id
#                     == customer.invoice_settings.default_payment_method
#                 ):
#                     payload = {
#                         "id": payment_method.id,
#                         "brand": payment_method.card.brand,
#                         "last4": payment_method.card.last4,
#                         "exp_month": payment_method.card.exp_month,
#                         "exp_year": payment_method.card.exp_year,
#                         "funding": payment_method.card.funding,
#                         "is_primary": payment_method.id
#                         == customer.invoice_settings.default_payment_method,
#                     }
#                     break

#             return Response({"card": payload}, status=status.HTTP_200_OK)
#         except stripe.error.StripeError as e:
#             return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class UserHasCard(APIView):  # dont know what is this
    permission_classes = [IsAuthenticated]

    def get(self, request):
        print('You dont have stripe ID ', request.user.stripe_id or ' ') 

        data = {"has_card": True}
        user = self.request.user

        # if user.is_hotel and Employee.objects.filter(user=user).exists():
        #     org = Employee.objects.get(user=user).organization
            
        if user.is_hotel:
            # org = Employee.objects.get(user=user).organization
            
            
            if is_stripe_customer(user):
                return Response(
                    {
                        "org_has_card": True,
                    },
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {
                        "org_has_card": False,
                    },
                    status=status.HTTP_200_OK,
                )

        if is_stripe_customer(user):
            return Response(data, status=status.HTTP_200_OK)
        return Response({"has_card": False}, status=status.HTTP_200_OK)


# # Checkig if user has enough balance to pay for the trip

# #  TODO: 1. Please make sure that the currency is correct for both balance and retieve amount from the request


# class UserHasBalance(APIView):  # dont know what is this
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         print('You dont have stripe ID ', request.user.stripe_id or ' ') 

#         user = self.request.user
#         fare = request.data.get("fare")
#         if not user.stripe_id:
#             return Response({"has_balance": False}, status=status.HTTP_200_OK)
#         try:
#             balance = stripe.Balance.retrieve()
#             balance = balance["available"][0]["amount"]
#         except InvalidRequestError:
#             return Response({"has_balance": False}, status=status.HTTP_200_OK)
#         if int(balance) > int(fare):
#             return Response({"has_balance": True}, status=status.HTTP_200_OK)
#         return Response({"has_balance": False}, status=status.HTTP_200_OK)


# class RemoveACard(APIView):  # done
#     permission_classes = [IsAuthenticated]

#     def delete(self, request, method_id):
#         print('You dont have stripe ID ', request.user.stripe_id or ' ') 

#         user = self.request.user
#         if not user.stripe_id:
#             return Response(status=status.HTTP_403_FORBIDDEN)
#         try:
#             _ = stripe.Customer.retrieve_payment_method(
#                 user.stripe_id, method_id)
#         except InvalidRequestError:
#             return Response(status=status.HTTP_403_FORBIDDEN)
#         stripe.PaymentMethod.detach(method_id)
#         return Response(
#             status=status.HTTP_200_OK, data={
#                 "detail": "Card removed successfully"}
#         )


class CreateAccountLink(APIView):  # Payments directly into their bank accounts through Stripe
    
    '''
    Summary:
    The CreateAccountLink API view allows a user to start the process of creating a 
    connected Stripe account and then provides them with a link to complete the necessary
    onboarding steps. This is a crucial step for platforms where users need to
    receive payments directly into their bank accounts through Stripe.
    '''
    def get(self, request):
        print('You dont have stripe ID ', request.user.stripe_id or ' ') 

        account_id = create_account()
        url = create_account_link(account_id)
        data = {"url": url}
        return Response(data, status=status.HTTP_200_OK)


# class Payout(APIView):  #
    
#     '''
#     The purpose of this code is to allow the platform to send 
#     a specified amount of money from the platform's Stripe account 
#     to a user's connected bank account.
    
#     '''
#     def get(self, request, user_id):
#         print('You dont have stripe ID ', request.user.stripe_id or ' ') 

#         user = get_object_or_404(User, id=user_id)
#         stripe_id = str(user.stripe_id)
#         accounts = stripe.Customer.list_sources(
#             stripe_id,
#             object="bank_account",
#             limit=3,
#         )
#         account_id = accounts.data[0]["id"]
#         try:
#             payout = stripe.Payout.create(
#                 amount=10, currency="usd", destination=account_id  # Amount in cents
#             )
#             print("Payout created: ", payout)
#         except stripe.error.StripeError as e:
#             print("Error creating payout: ", e)
#         return Response(status=status.HTTP_200_OK)





# class PerformPayment(APIView): 
#     '''
#     Purpose:
#     The purpose of this code is to create and confirm
#     a payment using a specified payment method for a given trip,
#     charging the user's card through Stripe.
#     '''
#     def get(self, request, trip_id, payment_method):
#         print('You dont have stripe ID ', request.user.stripe_id or ' ') 

#         trip = get_object_or_404(Trip, id=trip_id)
#         if trip.fare <= 0:
#             return Response(status=status.HTTP_403_FORBIDDEN)
#         user = trip.user
#         if not user.stripe_id:
#             data = ":)"
#             return Response(data, status=status.HTTP_200_OK)
#         try:
#             stripe.PaymentIntent.create(
#                 amount=int(trip.fare),
#                 currency="gbp",
#                 customer=user.stripe_id,
#                 payment_method=payment_method,
#                 off_session=True,
#                 confirm=True,
#                 metadata={"trip_id": str(trip.id)},
#             )
#             return Response(status=status.HTTP_200_OK)
#         except stripe.error.CardError as e:
#             err = e.error
#             # Error code will be authentication_required if authentication is needed
#             print("Code is: %s" % err.code)
#             payment_intent_id = err.payment_intent["id"]
#             payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)


# class WebHook(APIView):
    
#     '''
#     Summary:
#     The WebHook API view is a crucial component for integrating with
#     Stripe's real-time event system. It allows your application 
#     to respond immediately to key events such as successful payments or 
#     updates to customer payment methods. This feature is essential 
#     for maintaining up-to-date payment information and ensuring that your
#     application's state reflects the latest data from Stripe.
#     '''
#     def post(self, request):
#         print('You dont have stripe ID ', request.user.stripe_id or ' ') 

#         event = None
#         payload = request.body.decode("utf-8")
#         sig_header = request.META["HTTP_STRIPE_SIGNATURE"]

#         try:
#             event = stripe.Webhook.construct_event(
#                 payload, sig_header, settings.STRIPE_HOOK_SECRET
#             )
#         except ValueError as err:
#             # Invalid payload
#             raise err
#         except stripe.error.SignatureVerificationError as err:
#             # Invalid signature
#             raise err

#         # Handle the event
#         if event.type == "payment_intent.succeeded":
#             payment_intent = event.data.object
#             trip_id = payment_intent["metadata"]["trip_id"]
#             amount = payment_intent["amount"]
#             trip = get_object_or_404(Trip, id=trip_id)
#             trip.payment_status = "Paid"
#             trip.save()
#         elif event.type == "payment_method.attached":
#             payment_method = event.data.object
#             print("--------payment_method ---------->", payment_method)
#         # ... handle other event types
#         else:
#             print("Unhandled event type {}".format(event.type))

#         return Response(status=status.HTTP_200_OK)


