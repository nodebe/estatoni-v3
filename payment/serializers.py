from rest_framework import serializers
from account.v1.serializers.profile import VerySimpleProfileSerializer
from payment.models import Bank, BankAccount, Transaction


class BankSerializer(serializers.ModelSerializer):

    class Meta:
        model = Bank
        fields = ["name", "code"]


class VerifyAccountSerializer(serializers.Serializer):
    bank_code = serializers.CharField(required=True)
    account_number = serializers.CharField(required=True)


class BankAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankAccount
        fields = ["id", "bank_name", "bank_code", "account_number", "account_name", "created_at"]


class CommunityTransactionSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=True)
    subscription_id = serializers.IntegerField(required=False)


class SimpleTransactionSerializer(serializers.Serializer):
    class Meta:
        model = Transaction
        fields = ["id", "reference", "amount", "created_at"]


class TransactionSerializer(serializers.ModelSerializer):
    user = VerySimpleProfileSerializer(read_only=True)

    class Meta:
        model = Transaction
        fields = ["id", "reference", "user", "amount", "paid_amount", "status", "source", "destination", "description",
                  "created_at"]


class CreateTransactionSerializer(serializers.Serializer):
    transaction_type = serializers.CharField(required=True)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)

    def validate(self, attrs):
        pass


class PaystackCallbackDataSerializer(serializers.Serializer):
    status = serializers.CharField(required=True)
    reference = serializers.CharField(required=True)
    amount = serializers.IntegerField(required=True)


class PaystackCallbackSerializer(serializers.Serializer):
    event = serializers.CharField(required=True)
    data = PaystackCallbackDataSerializer(required=True)


class WithdrawalSerializer(serializers.Serializer):
    otp = serializers.CharField(required=True, min_length=5, max_length=5)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    bank_account_id = serializers.IntegerField(required=True)
