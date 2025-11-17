from rest_framework import serializers

class ActivationSerializer(serializers.Serializer):

  session_token = serializers.CharField(required=True, max_length=64)
  user_type = serializers.ChoiceField(required=True ,choices=["STAFF"])
  email = serializers.EmailField(required=True)
  password = serializers.CharField(write_only=True, min_length=8)
  country = serializers.CharField(required=False, default='AU', max_length=10)
  timezone = serializers.CharField(required=False, allow_blank=True, max_length=50)

