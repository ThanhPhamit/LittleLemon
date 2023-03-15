from rest_framework import serializers
from .models import MenuItem, Category, Rating, Cart, Order, OrderItem
from decimal import Decimal
from rest_framework.validators import UniqueValidator, UniqueTogetherValidator
import bleach
from django.contrib.auth.models import User


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'slug', 'title']


class MenuItemSerializer(serializers.ModelSerializer):
    stock = serializers.IntegerField(source='inventory')
    price_after_tax = serializers.SerializerMethodField(
        method_name="calculate_tax")
    # category = CategorySerializer(read_only=True)
    category_id = serializers.IntegerField(write_only=True)
    price = serializers.DecimalField(
        max_digits=6, decimal_places=2, min_value=2)
    title = serializers.CharField(
        max_length=255,
        validators=[UniqueValidator(queryset=MenuItem.objects.all())],
    )

    class Meta:
        model = MenuItem
        fields = ['id', 'title', 'price', 'stock',
                  'price_after_tax', 'category', 'category_id']

    def calculate_tax(self, product: MenuItem):
        return product.price * Decimal(1.1)

    # For sanitization data
    def validate_title(self, value):
        return bleach.clean(value)

    # Validate category_id
    def validate_category_id(self, value):
        try:
            Category.objects.get(pk=value)
            return value
        except Category.DoesNotExist:
            raise serializers.ValidationError("Invalid category id")


class RatingSerializer (serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        default=serializers.CurrentUserDefault()
    )

    class Meta:
        model = Rating
        fields = ['user', 'menuitem_id', 'rating']

        validators = [
            UniqueTogetherValidator(
                queryset=Rating.objects.all(),
                fields=['user', 'menuitem_id', 'rating']
            )
        ]

        extra_kwargs = {
            'rating': {
                'max_value': 5,
                'min_value': 0
            }
        }


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ('id','username', 'email', 'first_name', 'last_name', 'password', 'date_joined', 'last_login')
        extra_kwargs = {
            'password': {'write_only': True}
        }



class CartSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        default=serializers.CurrentUserDefault(),
    )
    # menuitem = MenuItemSerializer(read_only=True)
    menuitem_id = serializers.IntegerField()
    class Meta:
        model = Cart
        fields = ['user', 'menuitem_id', 'quantity', 'unit_price', 'price']

        validators = [
            UniqueTogetherValidator(
                queryset=Cart.objects.all(),
                fields=['user', 'menuitem_id']
            )
        ]
    
    # Validate menuitem_id
    def validate_menuitem_id(self, value):
        try:
            MenuItem.objects.get(pk=value)
            return value
        except MenuItem.DoesNotExist:
            raise serializers.ValidationError("Invalid menu item id")
        
    # Validate quanity
    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Cart quantity must greater")
        return value
    

class OrderSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    delivery_crew = UserSerializer()
    date = serializers.DateField(read_only=True)
    class Meta:
        model = Order
        fields = ['user', 'delivery_crew', 'status', 'total', 'date']


class OrderItemSerializer(serializers.ModelSerializer):
    # order = OrderSerializer(read_only=True)
    # menuitem = MenuItemSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = ['order_id', 'menuitem_id', 'quantity', 'unit_price', 'price']


        
