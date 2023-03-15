from django.http import HttpRequest
from django.shortcuts import render, get_object_or_404
from django.forms.models import model_to_dict
from django.urls import reverse
import json
from rest_framework import generics, status, views, viewsets
from .models import MenuItem, Category, Rating, Cart, Order, OrderItem
from .serializers import MenuItemSerializer, CategorySerializer, RatingSerializer, UserSerializer, CartSerializer, OrderItemSerializer, OrderSerializer
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.response import Response
from django.core.paginator import EmptyPage, Paginator
import bleach
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from .throttles import TenCallsPerMinute
from django.contrib.auth.models import User, Group
from djoser.views import UserViewSet
from .utils.constants import GroupName, ONLY_CUSTOMER_RESPONSE
from .utils.functions import getOrderWithJsonType, isCustomer
from datetime import date
# Create your views here.


# IMPLEMENTION

# Lists all menu items
@throttle_classes([UserRateThrottle, AnonRateThrottle])
@permission_classes([IsAuthenticated])
class MenuItemList(views.APIView):
    menu_item_view_name = 'menu-item-view'
    # Get menuitems list for Customer, Delivery crew, Manager
    def get(self, request: HttpRequest):
        menu_items_list = MenuItem.objects.all()
        menu_items_list_length = 0

        # Query
        category_name = request.query_params.get('category')
        to_price = request.query_params.get('to_price')
        search = request.query_params.get('search')
        ordering = request.query_params.get('ordering')
        perpage = request.query_params.get('perpage', default=2)
        page = request.query_params.get('page', default=1)


        if category_name:
            menu_items_list = menu_items_list.filter(category__title__contains=category_name)
        if to_price:
            menu_items_list = menu_items_list.filter(price__lte=to_price)
        if search:
            search = bleach.clean(search)
            menu_items_list = menu_items_list.filter(title__contains=search)
        if ordering:
            ordering_fields = ordering.split(',')
            menu_items_list = menu_items_list.order_by(*ordering_fields)
        # get size
        menu_items_list_length = len(menu_items_list)

        # Paginator
        paginator = Paginator(menu_items_list, per_page=perpage)
        try:
            menu_items_list = paginator.page(number=page)
        except EmptyPage:
            menu_items_list = []
        
        # Get another response value
        query_params=request.GET.copy()
        query_params.pop('page', None)
        url = request.build_absolute_uri(reverse(MenuItemList.menu_item_view_name))
        url_with_params = f"{url}?{'&'.join([f'{k}={v}' for k, v in query_params.items()])}" 
        previous = None
        if page == "1":
            previous = None
        elif page == "2":
            previous = url_with_params
        elif int(page) > 2:
            previous = url_with_params + "&page={0}".format(int(page) - 1)
    
        serializer_items = MenuItemSerializer(menu_items_list, many=True)
        response_data = {
            "count": menu_items_list_length,
            "previous": previous,
            "next": url_with_params + "&page={0}".format(int(page) + 1),
            "result": serializer_items.data
        }
        return Response(response_data, status=status.HTTP_200_OK)

    # Create new menu item for Manager
    def post(self, request: HttpRequest):
        if request.user.groups.filter(name=GroupName().MANAGER).exists():
            serializer_item = MenuItemSerializer(data=request.data)
            serializer_item.is_valid(raise_exception=True)
            serializer_item.save()
            response_data = {
                "message": "Created menu item successfully",
                "result": serializer_item.data
            }
            return Response(response_data, status=status.HTTP_201_CREATED)
        else:
            return Response({"message": "Area for only manager"}, status=status.HTTP_403_FORBIDDEN)

    def put(self, request: HttpRequest):
        return Response(status=status.HTTP_403_FORBIDDEN)

    def patch(self, request: HttpRequest):
        return Response(status=status.HTTP_403_FORBIDDEN)

    def delete(self, request: HttpRequest):
        return Response(status=status.HTTP_403_FORBIDDEN)


# Single menuitem endpoint with generic view
@throttle_classes([UserRateThrottle, AnonRateThrottle])
@permission_classes([IsAuthenticated])
class SingleMenuItemView(generics.RetrieveUpdateDestroyAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer

    def update_menu_item(response: Response):
        response.data = {
            "message": "Updated menu item successfully",
            "result": response.data
        }

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        response.data = {
            "result": response.data
        }
        return response

    def post(self, request, *args, **kwargs):
        return Response(status=status.HTTP_403_FORBIDDEN)

    # Updates single menu item for Manager
    def put(self, request, *args, **kwargs):
        if request.user.groups.filter(name=GroupName().MANAGER).exists() == False:
            return Response({"message": "Area for only manager"}, status=status.HTTP_403_FORBIDDEN)
        response = super().patch(request, *args, **kwargs)
        SingleMenuItemView.update_menu_item(response)
        return response

    def patch(self, request, *args, **kwargs):
        if request.user.groups.filter(name=GroupName().MANAGER).exists() == False:
            return Response({"message": "Area for only manager"}, status=status.HTTP_403_FORBIDDEN)
        response = super().patch(request, *args, **kwargs)
        SingleMenuItemView.update_menu_item(response)
        return response

    # Delete single menu item for Manager
    def delete(self, request, *args, **kwargs):
        if request.user.groups.filter(name=GroupName().MANAGER).exists() == False:
            return Response({"message": "Area for only manager"}, status=status.HTTP_403_FORBIDDEN)
        response = super().delete(request, *args, **kwargs)
        response.data = {'message': 'Deleted menu item'}
        return response


# Manager
@throttle_classes([UserRateThrottle, AnonRateThrottle])
@permission_classes([IsAuthenticated])
class ManagerListView(views.APIView):
    def get(self, request: HttpRequest):
        if request.user.groups.filter(name=GroupName().MANAGER).exists() == False:
            return Response({"message": "Area for only manager"}, status=status.HTTP_403_FORBIDDEN)
        manager_list = User.objects.all()
        manager_list = manager_list.filter(groups__name=GroupName().MANAGER)
        serializer_items = UserSerializer(manager_list, many=True)
        response_data = {
            "count": len(manager_list),
            "result": serializer_items.data
        }
        response_data.add()
        return Response(response_data, status=status.HTTP_200_OK)

    def post(self, request: HttpRequest):
        if request.user.groups.filter(name=GroupName().MANAGER).exists() == False:
            return Response({"message": "Area for only manager"}, status=status.HTTP_403_FORBIDDEN)
        try:
            username = request.data['username']
            user = get_object_or_404(User, username=username)
            if user.groups.filter(name=GroupName().MANAGER).exists():
                return Response({"message": username + " already belongs to group Manager"}, status=status.HTTP_200_OK)
            manager = Group.objects.get(name=GroupName().MANAGER)
            manager.user_set.add(user)
            return Response({"message": "Added " + username + " to Manager group"}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"message": "Invalid username: " + type(e).__name__}, status=status.HTTP_400_BAD_REQUEST)


@throttle_classes([UserRateThrottle, AnonRateThrottle])
@permission_classes([IsAuthenticated])
class SingleManagerView(views.APIView):
    def delete(self, request: HttpRequest, pk):
        if request.user.groups.filter(name=GroupName().MANAGER).exists() == False:
            return Response({"message": "Area for only manager"}, status=status.HTTP_403_FORBIDDEN)
        user = get_object_or_404(User, pk=pk)
        if user.groups.filter(name=GroupName().MANAGER).exists() == False:
            return Response({"message": user.username + " does not belongs to group Manager"}, status=status.HTTP_200_OK)
        manager = Group.objects.get(name=GroupName().MANAGER)
        manager.user_set.remove(user)
        return Response({"message": "Removed " + user.username + " from Manager group"}, status=status.HTTP_200_OK)


# Delivery person
@throttle_classes([UserRateThrottle, AnonRateThrottle])
@permission_classes([IsAuthenticated])
class DeliveryCrewView(views.APIView):
    def get(self, request: HttpRequest):
        if request.user.groups.filter(name=GroupName().MANAGER).exists() == False:
            return Response({"message": "Area for only manager"}, status=status.HTTP_403_FORBIDDEN)
        delivery_crew = User.objects.all()
        delivery_crew = delivery_crew.filter(
            groups__name=GroupName().DELIVERY_CREW)
        serializer_items = UserSerializer(delivery_crew, many=True)
        response_data = {
            "count": len(delivery_crew),
            "result": serializer_items.data
        }
        return Response(response_data, status=status.HTTP_200_OK)

    def post(self, request: HttpRequest):
        if request.user.groups.filter(name=GroupName().MANAGER).exists() == False:
            return Response({"message": "Area for only manager"}, status=status.HTTP_403_FORBIDDEN)
        try:
            username = request.data['username']
            user = get_object_or_404(User, username=username)
            if user.groups.filter(name=GroupName().DELIVERY_CREW).exists():
                return Response({"message": username + " already belongs to Delivery Crew"}, status=status.HTTP_200_OK)
            delivery_person = Group.objects.get(name=GroupName().DELIVERY_CREW)
            delivery_person.user_set.add(user)
            return Response({"message": "Added " + username + " to Deliver Crew group"}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"message": "Invalid username: " + type(e).__name__}, status=status.HTTP_400_BAD_REQUEST)


@throttle_classes([UserRateThrottle, AnonRateThrottle])
@permission_classes([IsAuthenticated])
class SingleDeliveryPersonView(views.APIView):
    def delete(self, request: HttpRequest, pk):
        if request.user.groups.filter(name=GroupName().MANAGER).exists() == False:
            return Response({"message": "Area for only manager"}, status=status.HTTP_403_FORBIDDEN)
        user = get_object_or_404(User, pk=pk)
        if user.groups.filter(name=GroupName().DELIVERY_CREW).exists() == False:
            return Response({"message": user.username + " does not belongs to group Delivery Crew"}, status=status.HTTP_200_OK)
        delivery_person = Group.objects.get(name=GroupName().DELIVERY_CREW)
        delivery_person.user_set.remove(user)
        return Response({"message": "Removed " + user.username + " from Delivery Crew group"}, status=status.HTTP_200_OK)


# Cart management
@throttle_classes([UserRateThrottle, AnonRateThrottle])
@permission_classes([IsAuthenticated])
class CartView(generics.ListCreateAPIView):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer

    def get(self, request, *args, **kwargs):
        if isCustomer(request=request) == False:
            return ONLY_CUSTOMER_RESPONSE
        response = super().get(request, *args, **kwargs)
        response.data = {
            "count": len(response.data),
            "result": response.data
        }
        return response

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        response.data = {
            "message": "Added menu items to cart successfully",
            "result": response.data
        }
        return response

    def delete(self, request, *args, **kwargs):
        if isCustomer(request=request) == False:
            return ONLY_CUSTOMER_RESPONSE
        user = request.user
        cart_items = Cart.objects.all().filter(user=user)
        for item in cart_items:
            item.delete()
        return Response({"message": "Remove all {0}'s cart items".format(user.username)}, status=status.HTTP_204_NO_CONTENT)

    def get_queryset(self):
        user = self.request.user
        return super().get_queryset().filter(user=user)


# Order management endpoints
@throttle_classes([UserRateThrottle, AnonRateThrottle])
@permission_classes([IsAuthenticated])
class OrderListView(views.APIView):
    def get(self, request: HttpRequest):
        order = None
        # Manager get all orders
        # Customer get his orders
        # Get all orders with order items assigned to the delivery crew
        if request.user.groups.filter(name=GroupName().MANAGER).exists():
            orders = Order.objects.all()
        elif request.user.groups.filter(name=GroupName().DELIVERY_CREW).exists():
            orders = Order.objects.all().filter(delivery_crew=request.user)
        else:
            orders = Order.objects.all().filter(user=request.user)
        response_data = '{}'
        response_data = json.loads(response_data)
        response_data['count'] = len(orders)
        orders_value = []
        for order in orders:
            orders_value.append(getOrderWithJsonType(order))
        response_data['result'] = orders_value
        return Response(response_data, status=status.HTTP_200_OK)

    # Post
    def post(self, request: HttpRequest):
        if isCustomer(request=request) == False:
            return ONLY_CUSTOMER_RESPONSE
        current_user = request.user
        current_user_cart_items = Cart.objects.all().filter(user=current_user)
        if len(current_user_cart_items) == 0:
            return Response({"message": "No menu item on {0}'s cart to order processing".format(current_user.username)}, status=status.HTTP_400_BAD_REQUEST)
        # Get total price
        total = 0
        for item in current_user_cart_items:
            total += item.price
        # Create order
        order = Order.objects.create(
            user_id=current_user.id, total=total, date=date.today())
        # Create order items
        order_items = []
        for item in current_user_cart_items:
            order_item = OrderItem.objects.create(
                order=order, menuitem=item.menuitem, quantity=item.quantity,  unit_price=item.unit_price,  price=item.price)
            order_items.append(order_item)

        # Clear cart items
        for item in current_user_cart_items:
            item.delete()
        # print(len(current_user_cart_items))
        # for item in current_user_cart_items:
        #     print(item)
        return Response({"message": "Created order for user successfully"}, status=status.HTTP_201_CREATED)


# Single order
@throttle_classes([UserRateThrottle, AnonRateThrottle])
@permission_classes([IsAuthenticated])
class SingleOrderView(views.APIView):
    def update_order_status(request: HttpRequest, order: Order):
        try:
            order_status = request.data['status']
            if str(order_status) == "1":
                order.status = True
                order.save()
                return True
            else:
                return False
        except Exception as e:
            return False

    def update_order_delivery_crew(request: HttpRequest, order: Order):
        delivery_crew = None
        try:
            delivery_crew = request.data['delivery_crew']
            if order.delivery_crew:
                return Response({"message": "Order already assigned to another delivery person"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return False

        delivery_person = get_object_or_404(User, pk=delivery_crew)
        if delivery_person.groups.filter(name=GroupName().DELIVERY_CREW).exists() == False:
            return Response({"message": "Must belong to Delivery crew"}, status=status.HTTP_400_BAD_REQUEST)
        order.delivery_crew = delivery_person
        order.save()
        return True

    def get(self, request: HttpRequest, pk):
        if isCustomer(request=request):
            order = get_object_or_404(Order, pk=pk)
            if order.user.id != request.user.id:
                return Response({"message": "The order does not belong to you"}, status=status.HTTP_406_NOT_ACCEPTABLE)
            response = {
                "result": getOrderWithJsonType(order)
            }
            return Response(response, status=status.HTTP_200_OK)
        return Response(status=status.HTTP_403_FORBIDDEN)

    def put(self, request: HttpRequest, pk):
        if request.user.groups.filter(name=GroupName().MANAGER).exists() == False:
            return Response({"message": "Area for only manager"}, status=status.HTTP_403_FORBIDDEN)
        order = get_object_or_404(Order, pk=pk)
        SingleOrderView.update_order_status(request=request, order=order)
        SingleOrderView.update_order_delivery_crew(
            request=request, order=order)
        return Response({"message": "Updated sucessfully"}, status=status.HTTP_200_OK)

    def patch(self, request: HttpRequest, pk):
        if request.user.groups.filter(name=GroupName().MANAGER).exists():
            order = get_object_or_404(Order, pk=pk)
            SingleOrderView.update_order_status(request=request, order=order)
            SingleOrderView.update_order_delivery_crew(
                request=request, order=order)
            return Response({"message": "Updated sucessfully"}, status=status.HTTP_200_OK)
        elif request.user.groups.filter(name=GroupName().DELIVERY_CREW).exists():
            order = get_object_or_404(Order, pk=pk)
            SingleOrderView.update_order_status(request=request, order=order)
            return Response({"message": "Updated sucessfully"}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "Area for only manager, delivery crew"}, status=status.HTTP_403_FORBIDDEN)

    def delete(self, request:HttpRequest, pk):
        if request.user.groups.filter(name=GroupName().MANAGER).exists() == False:
            return Response({"message": "Area for only manager"}, status=status.HTTP_403_FORBIDDEN)
        order = get_object_or_404(Order, pk=pk)
        order.delete()
        return Response({"message": "Deleted order successfully"}, status=status.HTTP_204_NO_CONTENT)

        
# EXAMPLE
# Using Model serializer
class RatingsView(generics.ListCreateAPIView):
    queryset = Rating.objects.all()
    serializer_class = RatingSerializer

    def get_permissions(self):
        if (self.request.method == 'GET'):
            return []

        return [IsAuthenticated()]


class MenuItemsView(generics.ListCreateAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer


# class SingleMenuItemView(generics.RetrieveUpdateDestroyAPIView):
#     queryset = MenuItem.objects.all()
#     serializer_class = MenuItemSerializer


class CategoryView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class SingleCategoryView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


# Using serializer
@api_view(['GET', 'POST'])
def menu_items(request: HttpRequest):
    if request.method == 'GET':
        items = MenuItem.objects.all()

        # Query params:
        category_name = request.query_params.get('category')
        to_price = request.query_params.get('to_price')
        search = request.query_params.get('search')
        ordering = request.query_params.get('ordering')
        perpage = request.query_params.get('perpage', default=2)
        page = request.query_params.get('page', default=1)

        # handle for query params:
        if category_name:
            items = items.filter(category__title=category_name)
        if to_price:
            items = items.filter(price__lte=to_price)
        if search:
            search = bleach.clean(search)
            items = items.filter(title__contains=search)
        if ordering:
            ordering_fields = ordering.split(',')
            items = items.order_by(*ordering_fields)

        paginator = Paginator(items, per_page=perpage)
        try:
            items = paginator.page(number=page)
        except EmptyPage:
            items = []
        serializer_item = MenuItemSerializer(items, many=True)

        return Response(serializer_item.data)
    if request.method == 'POST':
        serializer_item = MenuItemSerializer(data=request.data)
        serializer_item.is_valid(raise_exception=True)
        serializer_item.save()
        return Response(serializer_item.data, status=status.HTTP_201_CREATED)


@api_view()
def single_item(request: HttpRequest, id):
    items = get_object_or_404(MenuItem, pk=id)
    serialized_item = MenuItemSerializer(items)
    return Response(serialized_item.data)


# permision
@api_view()
@permission_classes([IsAuthenticated])
def secret(request):
    return Response({"message": "Some secret message"})


# Permision for user belong to Manager group
@api_view()
@permission_classes([IsAuthenticated])
def manager_view(request: HttpRequest):
    if request.user.groups.filter(name='Manager').exists():
        return Response({"message": "Only manager should see this"})
    else:
        return Response({"message": "You are not authorized"}, 403)


# Throttle check for anon
@api_view()
@throttle_classes([AnonRateThrottle])
def throttle_check(request):
    return Response({"message": "successful"})


# Throttle check for user rate throttle
@api_view()
@throttle_classes([TenCallsPerMinute, AnonRateThrottle])
def throttle_check_auth(request):
    return Response({"message": "message for the logged in user only"})


# Admin page
@api_view(['POST', 'DELETE'])
@permission_classes([IsAdminUser])
def admin_page(request: HttpRequest):
    username = request.data['username']
    if username:
        user = get_object_or_404(User, username=username)
        manager = Group.objects.get(name="Manager")
        if request.method == "POST":
            manager.user_set.add(user)
            return Response({"message": "Added " + username + " to Manager group"})
        elif request.method == "DELETE":
            manager.user_set.remove(user)
            return Response({"message": "Deleted " + username + " from Manager group"})
    return Response({"message": "error"}, status=status.HTTP_400_BAD_REQUEST)
