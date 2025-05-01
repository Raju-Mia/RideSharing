from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from organization_manager.models import (
    Organization, 
    OrganizationAccount, 
    OrganizationTransaction,
    )
from organization_manager.serializers import OrganizationSerializer, OrganizationAccountSerializer, OrganizationTransactionSerializer




def create_organization(name, email, phone_number):
    try:
        organization = Organization.objects.create(
            name=name,
            email=email,
            phone_number=phone_number,
            stripe_organization_id='',  # Set to default values if needed
            stripe_connected_account_id=''
        )
        return {
            'status': 'success',
            'data': OrganizationSerializer(organization).data
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e)
        }



def create_organization_account(organization_id, total_paid):
    try:
        organization = Organization.objects.get(id=organization_id)
        account = OrganizationAccount.objects.create(
            organization=organization,
            total_paid=total_paid,
            total_dealings=0.00,
            total_due=0.00,
            total_trips_completed=0,
            credit=0.00,
            debit=0.00,
            balance=0.00,
            is_active=True,
            status=True
        )
        return {
            'status': 'success',
            'data': OrganizationAccountSerializer(account).data
        }
    except Organization.DoesNotExist:
        return {
            'status': 'error',
            'message': 'Organization not found'
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e)
        }



def create_organization_transaction(organization_account_id, amount, transaction_type):
    try:
        account = OrganizationAccount.objects.get(id=organization_account_id)
        transaction = OrganizationTransaction.objects.create(
            organization_account=account,
            amount=amount,
            transaction_type=transaction_type,
            status='pending'
        )
        return {
            'status': 'success',
            'data': OrganizationTransactionSerializer(transaction).data
        }
    except OrganizationAccount.DoesNotExist:
        return {
            'status': 'error',
            'message': 'Organization Account not found'
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e)
        }





# from organization_manager.models import Organization, OrganizationAccount, OrganizationTransaction

# def create_organization(name, email, phone_number, stripe_organization_id='', stripe_connected_account_id=''):
#     organization = Organization.objects.create(
#         name=name,
#         email=email,
#         phone_number=phone_number,
#         stripe_organization_id=stripe_organization_id,
#         stripe_connected_account_id=stripe_connected_account_id
#     )
#     return organization

# def create_organization_account(organization, total_paid, total_dealings=0.00, total_due=0.00, total_trips_completed=0, credit=0.00, debit=0.00, balance=0.00):
#     account = OrganizationAccount.objects.create(
#         organization=organization,
#         total_paid=total_paid,
#         total_dealings=total_dealings,
#         total_due=total_due,
#         total_trips_completed=total_trips_completed,
#         credit=credit,
#         debit=debit,
#         balance=balance
#     )
#     return account

# def create_organization_transaction(account, amount, transaction_type='payment', status='pending'):
#     transaction = OrganizationTransaction.objects.create(
#         organization_account=account,
#         amount=amount,
#         transaction_type=transaction_type,
#         status=status
#     )
#     return transaction



