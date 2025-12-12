from rest_framework.generics import CreateAPIView, DestroyAPIView, ListAPIView, RetrieveAPIView, UpdateAPIView
from rest_framework.permissions import IsAuthenticated

from payment.serializers import BankSerializer, VerifyAccountSerializer, BankAccountSerializer, \
    CreateTransactionSerializer, TransactionSerializer, PaystackCallbackSerializer, WithdrawalSerializer
from payment.services import BankService, BankAccountService, TransactionService, PaystackService
from payment.utils import IsPaystackAuthenticated
from utils.util import CustomApiRequest


class BanksAPIView(ListAPIView, CustomApiRequest):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        self.response_serializer = BankSerializer
        self.response_serializer_requires_many = True

        service = BankService(request)

        return self.process_request(request, target_function=service.fetch_list_online, filter_params=None)


class VerifyAccountAPIView(RetrieveAPIView, CustomApiRequest):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        self.serializer_class = VerifyAccountSerializer

        service = BankService(request)

        return self.process_request(request, target_function=service.verify_account)


class AccountDetailsAPIView(CreateAPIView, CustomApiRequest):
    permission_classes = [IsAuthenticated]
    serializer_class = BankAccountSerializer
    response_serializer = BankAccountSerializer

    def post(self, request, *args, **kwargs):
        service = BankAccountService(request)
        return self.process_request(request, target_function=service.save_account_details)

    def get(self, request, *args, **kwargs):
        self.response_serializer_requires_many = True
        service = BankAccountService(request)
        return self.process_request(request, target_function=service.fetch_list, filter_params=None)


class UpdateDeleteAccountDetailsAPIView(UpdateAPIView, DestroyAPIView, CustomApiRequest):
    permission_classes = [IsAuthenticated]

    def put(self, request, *args, **kwargs):
        self.serializer_class = BankAccountSerializer
        self.response_serializer = BankAccountSerializer
        service = BankAccountService(request)
        account_detail_id = kwargs.get('account_detail_id')

        return self.process_request(request, target_function=service.update, account_detail_id=account_detail_id)

    def delete(self, request, *args, **kwargs):
        service = BankAccountService(request)
        account_detail_id = kwargs.get('account_detail_id')

        return self.process_request(request, target_function=service.delete, account_detail_id=account_detail_id)


class TransactionAPIView(CreateAPIView, CustomApiRequest):
    permission_classes = [IsAuthenticated]
    serializer_class = CreateTransactionSerializer

    def post(self, request, *args, **kwargs):
        self.response_serializer = TransactionSerializer
        service = TransactionService(request)

        return self.process_request(request, target_function=service.create_transaction)

    def get(self, request, *args, **kwargs):
        service = TransactionService(request)
        filter_params = self.get_request_filter_params("transaction_type", "status", "community_id", "amount")

        return self.process_request(request, target_function=service.fetch_paginated_list, filter_params=filter_params)


class TransactionTypesAPIView(CreateAPIView, CustomApiRequest):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        service = TransactionService(request)

        return self.process_request(request, target_function=service.fetch_transaction_types)


class PaystackCallbackAPIView(CreateAPIView, CustomApiRequest):
    permission_classes = [IsPaystackAuthenticated]

    def post(self, request, *args, **kwargs):
        self.serializer_class = PaystackCallbackSerializer
        service = PaystackService(request)

        return self.process_request(request, target_function=service.callback)


class WithdrawalAPIView(CreateAPIView, CustomApiRequest):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        self.serializer_class = WithdrawalSerializer
        self.response_serializer = TransactionSerializer

        service = TransactionService(request)

        return self.process_request(request, target_function=service.withdrawal)


class WithdrawalVerificationAPIView(CreateAPIView, CustomApiRequest):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        service = TransactionService(request)

        return self.process_request(request, target_function=service.send_withdrawal_otp)