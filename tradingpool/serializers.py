from rest_framework import serializers
from .models import OrderBook

class OrderBookSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderBook
        fields = ['exchange', 'address', 'start', 'end', 'bid', 'ask', 'created_at']
