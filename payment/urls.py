from django.urls import path
from payment.views import BanksAPIView, VerifyAccountAPIView, AccountDetailsAPIView, UpdateDeleteAccountDetailsAPIView, \
    TransactionAPIView, TransactionTypesAPIView, PaystackCallbackAPIView

urlpatterns = [
    path("banks", BanksAPIView.as_view(), name='bank_list'),
    path("verify-account", VerifyAccountAPIView.as_view(), name='verify_account'),
    path("account-details", AccountDetailsAPIView.as_view(), name='account_details'),
    path("account-details/<int:account_detail_id>", UpdateDeleteAccountDetailsAPIView.as_view(),
         name='update_delete_account_details'),

    path("transaction", TransactionAPIView.as_view(), name='transaction'),
    path("transaction-types", TransactionTypesAPIView.as_view(), name='transaction_types'),

    # Callbacks
    path("callback/paystack", PaystackCallbackAPIView.as_view(), name='paystack_callback'),
]
