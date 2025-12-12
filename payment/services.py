from decimal import Decimal
from payment.models import Bank, BankAccount, TransactionTypeChoices, Transaction, TransactionStatusChoices
from utils.constants.messages import ResponseMessages
from utils.errors import ServerError, UnprocessableEntityError, UserError, NotFoundError
from utils.models import ModelService
from utils.third_party_connection import PaystackAPIService
from utils.util import CustomApiRequest
from django.core.cache import cache
from django.utils.crypto import get_random_string
from django.utils import timezone
from django.db.models import Q, TextChoices
from django.conf import settings


class PaystackEventsChoices(TextChoices):
    charge_success = "charge.success"
    transfer_success = "transfer.success"
    transfer_failed = "transfer.failed"
    transfer_reversed = "transfer.reversed"


class BankAccountService(CustomApiRequest):
    def __init__(self, request):
        super().__init__(request)

    def save_account_details(self, payload):
        user = self.auth_user
        payload["user"] = user

        if user.bank_accounts.count() >= 1:
            raise UserError(ResponseMessages.max_accounts_exceeded)

        model_service = ModelService(self.request)
        bank_account = model_service.create_model_instance(model=BankAccount, payload=payload)

        return bank_account

    def update(self, payload, account_detail_id):
        user = self.auth_user
        account_detail = user.bank_accounts.filter(id=account_detail_id).first()

        if account_detail is None:
            raise NotFoundError(message=ResponseMessages.account_details_not_exist)

        model_service = ModelService(self.request)
        account_detail = model_service.update_model_instance(model_instance=account_detail, **payload)

        return account_detail

    def delete(self, account_detail_id):
        user = self.auth_user
        account_detail = user.bank_accounts.filter(id=account_detail_id).first()

        if account_detail is None:
            raise NotFoundError(message=ResponseMessages.account_details_not_exist)

        account_detail.delete()

        return {
            "message": ResponseMessages.account_deleted_successfully
        }

    def fetch_list(self, filter_params, **extra_args):
        user = self.auth_user

        return user.bank_accounts.all()

    def fetch_bank_account_by_id(self, bank_account_id):
        def __do_fetch_single():
            try:
                return BankAccount.objects.filter(id=bank_account_id).first()

            except Exception as e:
                raise ServerError(error=e, error_position="BankService.fetch_single")

        cache_key = self.generate_cache_key("bank_account", bank_account_id, model=BankAccount)
        return cache.get_or_set(cache_key, __do_fetch_single)


class BankService(CustomApiRequest):
    def __init__(self, request):
        super().__init__(request)

    def fetch_list(self, filter_params, **extra_args):
        def __do_fetch():
            try:
                return Bank.objects.all()

            except Exception as e:
                raise ServerError(error=e, error_position="BankService.fetch_list")

        cache_key = self.generate_cache_key("banks", model=Bank)
        return cache.get_or_set(cache_key, __do_fetch)

    def fetch_list_online(self, filter_params, **extra_args):
        def __do_fetch():
            try:
                paystack_service = PaystackAPIService()
                bank_list_response = paystack_service.fetch_bank_list()
                return bank_list_response.get("data")

            except Exception as e:
                raise ServerError(error=e, error_position="BankService.fetch_list_online")

        cache_key = self.generate_cache_key("online_banks")
        return cache.get_or_set(cache_key, __do_fetch)

    def verify_account(self, payload):
        account_number = payload.get("account_number")
        bank_code = payload.get("bank_code")

        if not account_number or not bank_code:
            raise UnprocessableEntityError()

        def __do_verify_single(account_number=account_number):
            service = PaystackAPIService()
            account_details = service.verify_account_number(account_number, bank_code)

            if account_details.get("status") in ["200", 200, True]:
                data = account_details.get("data", {})
                account_name = data.get("account_name")
                account_number = data.get("account_number")

                return {
                    "account_number": account_number,
                    "account_name": account_name,
                }

            else:
                return {
                    "message": "Account not found",
                }

        cache_key = self.generate_cache_key("bank_account", account_number, bank_code)
        return cache.get_or_set(cache_key, __do_verify_single)


class TransactionService(CustomApiRequest):
    def __init__(self, request):
        from payment.serializers import TransactionSerializer

        super().__init__(request)
        self.serializer_class = TransactionSerializer

    def fetch_list(self, filter_params, **extra_args):
        user = self.auth_user
        keyword = filter_params.get("keyword")
        status = filter_params.get("status")
        transaction_type = filter_params.get("transaction_type")
        amount = filter_params.get("amount")

        q = Q()

        if keyword:
            q &= (Q(reference__icontains=keyword) |
                  Q(description__icontains=keyword))

        if status:
            q &= Q(status__icontains=status)

        if transaction_type:
            q &= Q(transaction_type=transaction_type)

        if amount:
            amount = self.digify_number(amount, "amount")
            q &= Q(amount=amount)

        queryset = Transaction.objects.filter(q)

        return queryset

    def fetch_transaction_types(self):
        return TransactionTypeChoices.values

    def fetch_transaction_by_ref(self, reference):
        return Transaction.objects.filter(reference=reference).first()

    def fee_calculation(self, amount, percentage_cut=None):
        percentage_cut = percentage_cut or settings.PLATFORM_FEE_PERCENTAGE

        fee_amount = int((amount * percentage_cut) / 100)
        new_amount = amount - fee_amount

        return new_amount, fee_amount

    def create_transaction(self, payload):
        user = payload.get("user") or self.auth_user
        transaction_type = payload.get("transaction_type")

        payload["user"] = user
        payload["reference"] = f"CB-{user.id}-{get_random_string(length=10)}".upper()

        model_service = ModelService(self.request)

        #  Create Transaction object
        transaction = model_service.create_model_instance(model=Transaction, payload=payload)

        # TODO: Do something with the transaction object

        return transaction

    def verify_account_balance_after_transaction(self, account_balance, supposed_amount):
        return account_balance == supposed_amount

    def reverse_transaction(self, transaction):
        amount = transaction.amount
        fee = transaction.fee

        if fee > 0:
            amount += fee

        return self.fund_balance(
            user=transaction.user,
            amount=amount,
            transaction_type=TransactionTypeChoices.credit,
            description=f"Reversal for Transaction with ID: {transaction.reference}",
            source="Platform",
            destination="Wallet"
        )

    def fund_balance(self, user, amount, transaction_type, description, **kwargs):
        """
        :param user:
        :param amount:
        :param transaction_type: Credit, Debit, Withdrawal
        :param description:
        :param kwargs: source, destination, fee
        :return:
        """
        amount = Decimal(amount)

        amount_before = user.balance
        is_credit = transaction_type in [TransactionTypeChoices.credit]

        amount_after = amount_before + amount if is_credit else amount_before - amount

        if is_credit:
            user.balance += amount
        else:
            user.balance -= amount

        if not self.verify_account_balance_after_transaction(user.balance, amount_after):
            raise UserError(ResponseMessages.possible_duplicate_error)

        transaction_status = TransactionStatusChoices.success
        paid_amount = amount

        if transaction_type == TransactionTypeChoices.withdrawal:
            transaction_status = TransactionStatusChoices.pending
            paid_amount = 0.00

        transaction_payload = {
            "user": user,
            "amount": amount,
            "transaction_type": transaction_type,
            "description": description,
            "paid_amount": paid_amount,
            "status": transaction_status,
            "fee": kwargs.get("fee", 0),
            "source": kwargs.get("source"),
            "destination": kwargs.get("destination"),
        }

        user.save(update_fields=["balance"])

        return self.create_transaction(transaction_payload)


class PaystackService(CustomApiRequest):

    def __init__(self, request):
        super().__init__(request)
        self.service = PaystackAPIService()

    def verify_transaction(self, transaction_ref):
        response = self.service.verify_transaction(transaction_ref)
        if not response:
            return False

        verification_data = response.get("data")

        return verification_data

    def successful_transaction(self, paystack_response_data, transaction, transaction_ref):
        """ Take action after successful transaction """
        user_full_name = ""

        # Verify Transaction status from Paystack
        verification_data = self.verify_transaction(transaction_ref)

        if not verification_data:
            raise UserError("Verification failed")

        transaction_status = verification_data.get("status")
        transaction_amount = verification_data.get("amount") / 100
        transaction_date = timezone.now()

        transaction.response_data = paystack_response_data

        if transaction_amount < transaction.amount:
            """
            If the main amount for the transaction initialized is not equal to the transaction_amount gotten from 
            verification
            """
            transaction.status = TransactionStatusChoices.ongoing
            transaction_owner = transaction.user

            message = f"""Your payment of ₦{transaction_amount} for transaction with ref. {transaction.reference} 
            is lower than the amount ₦{transaction.amount} to be paid. Please check your transaction, and try again."""
            # _ = send_notification_alert.delay(user_id=transaction_owner.user_id, message=message,
            #                                   notification_type=DynamicNotificationType.transaction_update)

            transaction.save(update_fields=["status", "response_data"])
            return True

        transaction.status = transaction_status

        transaction.save(update_fields=["response_data", "status", "paid_amount"])

    def successful_transfer(self, paystack_response_data, transaction):
        amount = int(paystack_response_data.get("amount", 0) / 100)

        transaction.paid_amount = amount
        transaction.status = paystack_response_data.get("status")
        transaction.response_data = paystack_response_data

        transaction.save(update_fields=["response_data", "status", "paid_amount"])

    def failed_transfer(self, paystack_response_data, transaction):
        transaction.status = TransactionStatusChoices.failed
        transaction.response_data = paystack_response_data

        transaction.save(update_fields=["response_data", "status"])

    def callback(self, payload):
        event = payload.get("event")
        transaction_data = payload.get("data")

        transaction_ref = transaction_data.get("reference")

        if not transaction_ref:
            raise UserError("Transaction reference not found")

        # Fetch Transaction from DB
        transaction_service = TransactionService(self.request)
        transaction = transaction_service.fetch_transaction_by_ref(transaction_ref)

        if transaction is None:
            raise UserError("Transaction reference not found")

        if transaction.status != TransactionStatusChoices.pending:
            raise UserError("Transaction already acted upon!")

        if event == PaystackEventsChoices.charge_success:
            self.successful_transaction(paystack_response_data=transaction_data, transaction=transaction,
                                        transaction_ref=transaction_ref)

        elif event == PaystackEventsChoices.transfer_success:
            self.successful_transfer(paystack_response_data=transaction_data, transaction=transaction)

        elif event in [PaystackEventsChoices.transfer_failed, PaystackEventsChoices.transfer_reversed]:
            self.failed_transfer(paystack_response_data=transaction_data, transaction=transaction)
            transaction_service.reverse_transaction(transaction)

        return True
