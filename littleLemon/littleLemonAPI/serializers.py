from rest_framework import serializers
from .models import Cart, MenuItem, Order, OrderItem
from django.contrib.auth.models import User, Group


class RegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)
    group = serializers.ChoiceField(choices=[
        ('Customers', 'Customers'),
        ('Managers', 'Managers'),
        ('Delivery Crew', 'Delivery Crew')
    ])

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm', 'group']

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({"password": "Passwords do not match!"})
        return data

    def create(self, validated_data):
        group_name = validated_data.pop('group')
        password = validated_data.pop('password')
        validated_data.pop('password_confirm')

        # Create the user
        user = User.objects.create_user(password=password, **validated_data)

        # Add user to the selected group
        group, created = Group.objects.get_or_create(name=group_name)
        user.groups.add(group)

        # Return the created user instance
        return user




class MenuItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItem
        fields = ['id', 'title', 'price', 'featured', 'category']



# Cart Serializers
class CartItemSerializer(serializers.ModelSerializer):
    menu_item = serializers.StringRelatedField()

    class Meta:
        model = Cart
        fields = ['id', 'menu_item', 'quantity', 'price']



class OrderItemSerializer(serializers.ModelSerializer):
    menu_item = serializers.StringRelatedField()

    class Meta:
        model = OrderItem
        fields = ['menu_item', 'quantity', 'price']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, source='orderitem_set')

    class Meta:
        model = Order
        fields = ['id', 'user', 'status', 'delivery_crew', 'total', 'date', 'items']