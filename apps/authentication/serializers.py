from rest_framework import serializers
from django.contrib.auth.models import User
from apps.core.models import Driver, Carrier


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=8)
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=30)
    last_name = serializers.CharField(max_length=150)
    license_number = serializers.CharField(max_length=50)
    carrier_name = serializers.CharField(max_length=255)
    carrier_address = serializers.CharField(max_length=255)

    def create(self, validated_data):
        carrier, _ = Carrier.objects.get_or_create(
            name=validated_data["carrier_name"],
            defaults={"main_office_address": validated_data["carrier_address"]},
        )
        user = User.objects.create_user(
            username=validated_data["username"],
            password=validated_data["password"],
            email=validated_data["email"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
        )
        driver = Driver.objects.create(
            user=user, carrier=carrier, license_number=validated_data["license_number"]
        )
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
