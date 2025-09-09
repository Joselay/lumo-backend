from rest_framework import serializers


class ChatMessageSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=1000, help_text="User's message to send to AI")


class ChatResponseSerializer(serializers.Serializer):
    response = serializers.CharField(help_text="AI's response to the user's message")
    success = serializers.BooleanField(help_text="Whether the request was successful")
    error = serializers.CharField(required=False, allow_blank=True, help_text="Error message if any")