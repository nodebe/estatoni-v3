from django.shortcuts import render
from drf_spectacular.utils import extend_schema
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework import status

from location.v1.services import location_service
from location.v1.serializers import CitySerializer, CountrySerializer, StateSerializer
from utils.util import CustomApiResponse


@extend_schema(tags=["Location"])
class CountryApiView(ListAPIView, CustomApiResponse):
    serializer_class = CountrySerializer

    def get(self, request, *args, **kwargs):
        try:
            countries = location_service.fetch_active_countries()

            response = self.serializer_class(instance=countries, many=True)

            data = {
                "results": response.data
            }

            return Response(data, status=status.HTTP_200_OK)

        except Exception as e:
            return self.error_response(e)


@extend_schema(tags=["Location"])
class StateApiView(ListAPIView, CustomApiResponse):
    serializer_class = StateSerializer

    def get(self, request, *args, **kwargs):
        try:
            country_id = self.kwargs.get("country_id")
            states = location_service.fetch_active_states(country_id=country_id)
            response = self.serializer_class(instance=states, many=True)

            data = {
                "results": response.data
            }

            return Response(data, status=status.HTTP_200_OK)

        except Exception as e:
            return self.error_response(e)


@extend_schema(tags=["Location"])
class CityApiView(ListAPIView, CustomApiResponse):
    serializer_class = CitySerializer

    def get(self, request, *args, **kwargs):
        try:
            state_id = self.kwargs.get("state_id")
            cities = location_service.fetch_active_cities(state_id=state_id)
            response = self.serializer_class(instance=cities, many=True)

            data = {
                "results": response.data
            }

            return Response(data, status=status.HTTP_200_OK)

        except Exception as e:
            return self.error_response(e)
