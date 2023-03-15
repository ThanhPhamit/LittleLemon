
from django.http import HttpRequest


from LittleLemonAPI.models import Order, OrderItem
from LittleLemonAPI.serializers import OrderItemSerializer
from LittleLemonAPI.utils.constants import GroupName

# Check user belong to Customer group
def isCustomer(request: HttpRequest):
    return (request.user.groups.filter(name=GroupName().MANAGER).exists() == False) & (request.user.groups.filter(name=GroupName().DELIVERY_CREW).exists() == False)


# Get json order
def getOrderWithJsonType(order: Order):
    return {
        "order_id": order.id,
        "user_id": order.user.id,
        "delivery_person_id": order.delivery_crew.id if order.delivery_crew else None,
        "status": order.status,
        "total": order.total,
        "date": order.date,
        "order_items": OrderItemSerializer(OrderItem.objects.all().filter(order_id=order.id), many=True).data
    }