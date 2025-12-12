from django.contrib import admin

from account.admin import BaseAdmin
from payment.models import Transaction, BankAccount


@admin.register(Transaction)
class TransactionAdmin(BaseAdmin):
    list_display = ["user__first_name", "reference", "transaction_type", "amount", "paid_amount", "status"]


@admin.register(BankAccount)
class BankAccountAdmin(BaseAdmin):
    list_display = ["user__first_name", "bank_name", "account_number", "account_name", "paystack_recipient_code"]