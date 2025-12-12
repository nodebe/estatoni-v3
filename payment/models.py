from django.db import models

from base.models import BaseModel


class TransactionStatusChoices(models.TextChoices):
    success = "success"
    abandoned = "abandoned"
    failed = "failed"
    ongoing = "ongoing"
    pending = "pending"
    processing = "processing"
    queued = "queued"
    reversed = "reversed"


class TransactionTypeChoices(models.TextChoices):
    withdrawal = "Withdrawal"
    credit = "Credit"
    debit = "Debit"


# Create your models here.
class Bank(BaseModel):
    name = models.CharField(max_length=255, unique=True, blank=False, null=False)
    code = models.CharField(max_length=255, unique=True, blank=False, null=False)
    country = models.CharField(max_length=255, blank=False, null=False)


class BankAccount(BaseModel):
    user = models.ForeignKey("account.User", on_delete=models.CASCADE, related_name="bank_accounts")
    bank_name = models.CharField(max_length=255, null=False)
    bank_code = models.CharField(max_length=255, null=False)
    account_number = models.CharField(max_length=255, null=False)
    account_name = models.CharField(max_length=255, null=False)
    paystack_recipient_code = models.CharField(max_length=255, null=True, blank=True)


class Transaction(BaseModel):
    user = models.ForeignKey("account.User", on_delete=models.CASCADE, related_name="transactions")
    reference = models.CharField(max_length=255, null=False, unique=True)
    transaction_type = models.CharField(max_length=50, choices=TransactionTypeChoices.choices)
    amount = models.DecimalField(decimal_places=2, max_digits=10, blank=False, null=False)
    fee = models.DecimalField(decimal_places=2, max_digits=10, blank=False, null=True, default=0.00)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=50, choices=TransactionStatusChoices.choices,
                              default=TransactionStatusChoices.pending)
    source = models.CharField(max_length=255, null=True)
    destination = models.CharField(max_length=255, null=True)
    description = models.TextField(blank=True)
    response_data = models.JSONField(default=dict, blank=True)
