from rest_framework import serializers
from .models import City, Country, State
from .services import location_service

class CountrySerializer(serializers.ModelSerializer):

    class Meta:
        model = Country
        fields = ['id', 'name', 'code']
        read_only_fields = ["name", "code"]

    def validate(self, attrs):
        data = attrs.copy()

        country_id = data.get("id")
        country = location_service.fetch_country_by_id(country_id)

        return country

        
class StateSerializer(serializers.ModelSerializer):
    country = CountrySerializer()
    class Meta:
        model = State
        fields = ['id', 'name', 'code', "country"]
        read_only_fields = ["name", "code", "country"]


class CitySerializer(serializers.ModelSerializer):
    state = StateSerializer()

    class Meta:
        model = City
        fields = ['id', 'name', 'state']
        read_only_fields = ["name", "state"]