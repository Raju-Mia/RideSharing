from rest_framework import serializers

from .models import Text


class TextSerializer(serializers.ModelSerializer):
    sender = serializers.SerializerMethodField()

    class Meta:
        model = Text
        fields = ["text", "sender", "created_at"]

    def get_sender(self, obj):
        return str(obj.sender.id)
