import datetime
from rest_framework import serializers


class CardSerializer(serializers.Serializer):
    number = serializers.CharField()
    exp_month = serializers.IntegerField(max_value=12, min_value=1)
    exp_year = serializers.IntegerField()
    cvc = serializers.CharField(max_length=4)

    class Meta:
        fields = ["number", "exp_month", "exp_year", "cvc"]

    def validate(self, attrs):
        now = datetime.datetime.now()
        if attrs["exp_year"] < now.year:
            raise serializers.ValidationError("Year cant be in the past")
        if attrs["exp_year"] == now.year:
            if attrs["exp_month"] < now.month:
                raise serializers.ValidationError("Month cant be in the past")
        return super().validate(attrs)



class BookingPaymentSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    driver_id = serializers.IntegerField()

    def validate(self, attrs):
        if attrs['amount'] <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return attrs





class ChargeSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    driver_id = serializers.IntegerField()
    payment_method_id = serializers.CharField()  # Stripe Payment Method ID



#----------------------------- New --------------------------------