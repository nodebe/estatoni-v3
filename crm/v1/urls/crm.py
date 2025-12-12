from django.urls import path

from crm.v1.views.others import ListOptionsAPIView, ListIdTypesAPIView

urlpatterns = [
    path('id-types', ListIdTypesAPIView.as_view(), name="list_id_types"),
    path('options', ListOptionsAPIView.as_view(), name="list_options"),
]
