from rest_framework import serializers

class ValidateInvitationSerializer(serializers.Serializer):
  """招待トークンの検証用"""
  token = serializers.CharField(required=True, max_length=255)