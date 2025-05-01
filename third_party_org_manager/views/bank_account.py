from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied


from organization_manager.models import OrganizationBankAccount
from third_party_org_manager.serializers.bank_account_serializer import OrganizationBankAccountSerializer


# List and Create API
class BankAccountListCreateView(generics.ListCreateAPIView):
    queryset = OrganizationBankAccount.objects.all()
    serializer_class = OrganizationBankAccountSerializer
    permission_classes = [IsAuthenticated]  # Restrict access to authenticated users only

    def get_queryset(self):
        # Restrict to bank accounts for the user's organization
        return OrganizationBankAccount.objects.filter(organization=self.request.user.organization)

    def perform_create(self, serializer):
        # Assign the bank account to the user's organization
        serializer.save(organization=self.request.user.organization)







class BankAccountDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Handles retrieving, updating, and deleting a specific bank account.
    """
    queryset = OrganizationBankAccount.objects.all()
    serializer_class = OrganizationBankAccountSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Restrict to bank accounts for the user's organization
        return OrganizationBankAccount.objects.filter(organization=self.request.user.organization)

    def get_object(self):
        # Retrieve the object and ensure it belongs to the user's organization
        obj = super().get_object()
        if obj.organization != self.request.user.organization:
            raise PermissionDenied("You do not have permission to access this bank account.")
        return obj

    def destroy(self, request, *args, **kwargs):
        # Override destroy to return a custom success message
        obj = self.get_object()
        obj.delete()
        return Response({"message": "Bank account successfully deleted."}, status=status.HTTP_200_OK)
