from rest_framework import serializers

class BusinessLoginSerializer(serializers.Serializer):
  user_type = serializers.ChoiceField(required=True ,choices=["OWNER", "STAFF"])
  email = serializers.EmailField(required=True)
  password = serializers.CharField(write_only=True, min_length=8)
  platform = serializers.ChoiceField(required=True, choices=["web", "ios", "android"])

class CustomerLoginSerializer(serializers.Serializer):
  user_type = serializers.ChoiceField(required=True ,choices=["CUSTOMER"])
  email = serializers.EmailField(required=True)
  password = serializers.CharField(write_only=True, min_length=8)
  platform = serializers.ChoiceField(required=True, choices=["web", "ios", "android"])