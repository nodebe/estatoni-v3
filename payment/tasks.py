from core.celery import app
from utils.third_party_connection import PaystackAPIService


@app.task
def generate_paystack_recipient_code(bank_account_id):
    from payment.services import BankAccountService

    service = BankAccountService(None)
    bank_account = service.fetch_bank_account_by_id(bank_account_id)

    if bank_account is None:
        return

    payload = {
        "name": bank_account.account_name,
        "account_number": bank_account.account_number,
        "bank_code": bank_account.bank_code,
    }

    if not bank_account.paystack_recipient_code:
        paystack_service = PaystackAPIService()
        response = paystack_service.create_transfer_recipient(payload)

        if response.get("status") in [200, "200", True]:
            data = response.get("data", {})
            recipient_code = data.get("recipient_code")

            bank_account.paystack_recipient_code = recipient_code
            bank_account.save()

            return recipient_code

    return True


@app.task
def initiate_paystack_transfer(bank_account_id, amount, transaction_reference):
    from payment.services import BankAccountService, TransactionService

    service = BankAccountService(None)

    bank_account = service.fetch_bank_account_by_id(bank_account_id)

    if bank_account is None:
        return

    paystack_recipient_code = bank_account.paystack_recipient_code

    if not paystack_recipient_code:
        paystack_recipient_code = generate_paystack_recipient_code(bank_account_id)

    transaction_service = TransactionService(None)
    transaction = transaction_service.fetch_transaction_by_ref(transaction_reference)

    paystack_service = PaystackAPIService()
    response = paystack_service.initiate_transfer(
        recipient=paystack_recipient_code,
        amount=amount,
        reference=transaction_reference,
        reason=transaction.description
    )

    transaction.response_data = response
    transaction.save(update_fields=["response_data"])


