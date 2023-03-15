from django.http import HttpRequest
from rest_framework.response import Response
from rest_framework import status

from LittleLemonAPI.models import Order, OrderItem
from LittleLemonAPI.serializers import OrderItemSerializer


class GroupName:
    @property
    def MANAGER(self):
        return "Manager"

    @property
    def DELIVERY_CREW(self):
        return "Delivery crew"


ONLY_CUSTOMER_RESPONSE = Response(
    {"message": "Only for customer"}, status=status.HTTP_403_FORBIDDEN)
