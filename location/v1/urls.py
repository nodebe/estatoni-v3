from django.urls import path

from location.v1.views import CountryApiView, StateApiView, CityApiView


urlpatterns = [
    path("country", CountryApiView.as_view(), name="country"),
    path("country/<int:country_id>/state", StateApiView.as_view(), name="state"),
    path("country/state/<int:state_id>", CityApiView.as_view(), name="city"),
]