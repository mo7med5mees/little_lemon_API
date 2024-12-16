from rest_framework import status, viewsets
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_201_CREATED, HTTP_404_NOT_FOUND, HTTP_200_OK, HTTP_204_NO_CONTENT
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from django.contrib.auth.models  import User, Group

from .models import MenuItem, Cart, Order, OrderItem
from .serializers import CartItemSerializer, MenuItemSerializer, OrderSerializer, RegistrationSerializer


class RegisterUserAPIView(APIView):
    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "User registered successfully."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def customer_dashboard(request):
    if not request.user.groups.filter(name='Customers').exists():
        return Response({"error": "Access restricted to Customers only."}, status=status.HTTP_403_FORBIDDEN)
    return Response({"message": "Welcome to the Customer Dashboard."})




# Custom permission classes
class IsManagerPermission(IsAuthenticated):
    """Allows access only to Managers."""
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.groups.filter(name='Manager').exists()
    
class IsCustomerPermission(IsAuthenticated):
    """Allows access only to users in the Customer group."""
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.groups.filter(name='Customer').exists()
    
class IsDeliveryCrewPermission(IsAuthenticated):
    """Allows access only to users in the Delivery Crew group."""
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.groups.filter(name='Delivery Crew').exists()


class IsCustomerOrDeliveryCrewPermission(IsAuthenticated):
    def has_permission(self, request, view):
        is_customer_or_delivery_crew = request.user.groups.filter(name__in=['Customers', 'Delivery Crew']).exists()
        print(f"User groups: {request.user.groups.all()}, Has Permission: {is_customer_or_delivery_crew}")
        return super().has_permission(request, view) and is_customer_or_delivery_crew
    

class GroupManagementBase(APIView):
    """Base class for group management views."""
    permission_classes = [IsManagerPermission]

    group_name = None  # To be defined in subclasses

    def get_group(self):
        """Retrieve the group instance."""
        try:
            return Group.objects.get(name=self.group_name)
        except Group.DoesNotExist:
            raise Response({"detail": f"Group '{self.group_name}' does not exist."}, status=HTTP_400_BAD_REQUEST)

    def get_users_in_group(self):
        """Returns all users in the specified group."""
        group = self.get_group()
        return group.user_set.all()
    
    def add_user_to_group(self, user_id):
        """Adds a user to the specified group."""
        try:
            user = User.objects.get(id=user_id)
            group = self.get_group()
            group.user_set.add(user)
            return Response({"detail": f"User {user.username} added to group {self.group_name}."}, status=HTTP_201_CREATED)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=HTTP_404_NOT_FOUND)

    def remove_user_from_group(self, user_id):
        """Removes a user from the specified group."""
        try:
            user = User.objects.get(id=user_id)
            group = self.get_group()
            group.user_set.remove(user)
            return Response({"detail": f"User {user.username} removed from group {self.group_name}."}, status=HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=HTTP_404_NOT_FOUND)


class ManagerUsersView(GroupManagementBase):
    group_name = 'Manager'

    def get(self, request):
        """Returns all managers."""
        users = self.get_users_in_group()
        return Response({"users": [{"id": user.id, "username": user.username} for user in users]}, status=HTTP_200_OK)

    def post(self, request):
        """Assigns a user to the manager group."""
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({"detail": "User ID is required."}, status=HTTP_400_BAD_REQUEST)
        return self.add_user_to_group(user_id)

class ManagerUserDetailView(GroupManagementBase):
    group_name = 'Manager'

    def delete(self, request, user_id):
        """Removes a user from the manager group."""
        return self.remove_user_from_group(user_id)


class DeliveryCrewUsersView(GroupManagementBase):
    group_name = 'Delivery Crew'

    def get(self, request):
        """Returns all delivery crew."""
        users = self.get_users_in_group()
        return Response({"users": [{"id": user.id, "username": user.username} for user in users]}, status=HTTP_200_OK)

    def post(self, request):
        """Assigns a user to the delivery crew group."""
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({"detail": "User ID is required."}, status=HTTP_400_BAD_REQUEST)
        return self.add_user_to_group(user_id)

class DeliveryCrewUserDetailView(GroupManagementBase):
    group_name = 'Delivery Crew'

    def delete(self, request, user_id):
        """Removes a user from the delivery crew group."""
        return self.remove_user_from_group(user_id)


    

class MenuItemViewSet(viewsets.ModelViewSet):
    """ViewSet for handling menu items."""
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated()]  # Temporary bypass for debugging
        elif self.request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            return [IsManagerPermission()]
        return super().get_permissions()
    
    def list(self, request, *args, **kwargs):
        """Handles GET requests for /api/menu-items."""
        if not request.user.groups.filter(name__in=['Managers', 'Customers', 'Delivery Crew']).exists():
            raise PermissionDenied("You do not have permission to view this resource.")
        return super().list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """Handles GET requests for /api/menu-items/{menuItem}."""
        return super().retrieve(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        """Handles POST requests for /api/menu-items."""
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """Handles PUT requests for /api/menu-items/{menuItem}."""
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        """Handles PATCH requests for /api/menu-items/{menuItem}."""
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Handles DELETE requests for /api/menu-items/{menuItem}."""
        return super().destroy(request, *args, **kwargs)
    



class CartManagementView(APIView):
    permission_classes = [IsCustomerPermission]

    def get(self, request):
        """Returns current items in the cart for the current user token."""
        cart_items = Cart.objects.filter(user=request.user)
        serializer = CartItemSerializer(cart_items, many=True)
        return Response({"cart_items": serializer.data}, status=status.HTTP_200_OK)

    def post(self, request):
        """Adds a menu item to the cart for the authenticated user."""
        menu_item_id = request.data.get('menu_item_id')
        quantity = request.data.get('quantity', 1)
        try:
            menu_item = MenuItem.objects.get(id=menu_item_id)
            cart_item, created = Cart.objects.get_or_create(user=request.user, menu_item=menu_item)
            if not created:
                cart_item.quantity += quantity
                cart_item.save()
            return Response({"detail": "Item added to cart."}, status=status.HTTP_201_CREATED)
        except MenuItem.DoesNotExist:
            return Response({"detail": "Menu item not found."}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request):
        """Deletes all menu items from the cart for the current user."""
        Cart.objects.filter(user=request.user).delete()
        return Response({"detail": "Cart cleared."}, status=status.HTTP_204_NO_CONTENT)
    




    # Order Management
class OrderManagementView(APIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            if self.request.user.groups.filter(name='Customer').exists():
                return [IsCustomerPermission()]
            elif self.request.user.groups.filter(name='Delivery Crew').exists():
                return [IsDeliveryCrewPermission()]
            elif self.request.user.groups.filter(name='Manager').exists():
                return [IsManagerPermission()]
        elif self.request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            return [IsManagerPermission()]
        return super().get_permissions()

    def get(self, request):
        """Returns orders based on the user role."""
        if request.user.groups.filter(name='Customer').exists():
            orders = Order.objects.filter(user=request.user)
        elif request.user.groups.filter(name='Delivery Crew').exists():
            orders = Order.objects.filter(delivery_crew=request.user)
        elif request.user.groups.filter(name='Manager').exists():
            orders = Order.objects.all()
        else:
            return Response({"detail": "Permission denied."}, status=HTTP_400_BAD_REQUEST)

        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data, status=HTTP_200_OK)
    
    def post(self, request):
        """Creates an order from the cart."""
        cart_items = Cart.objects.filter(user=request.user)
        if not cart_items.exists():
            return Response({"detail": "Cart is empty."}, status=HTTP_400_BAD_REQUEST)

        order = Order.objects.create(user=request.user, total=0)
        total = 0
        for cart_item in cart_items:
            OrderItem.objects.create(
                order=order,
                menu_item=cart_item.menu_item,
                quantity=cart_item.quantity,
                price=cart_item.price
            )
            total += cart_item.price
        order.total = total
        order.save()
        cart_items.delete()

        serializer = OrderSerializer(order)
        return Response(serializer.data, status=HTTP_201_CREATED)
    

class OrderDetailView(APIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsCustomerPermission()]
        elif self.request.method in ['PUT', 'PATCH']:
            if self.request.user.groups.filter(name='Manager').exists():
                return [IsManagerPermission()]
            elif self.request.user.groups.filter(name='Delivery Crew').exists():
                return [IsDeliveryCrewPermission()]
        elif self.request.method == 'DELETE':
            return [IsManagerPermission()]
        return super().get_permissions()

    def get(self, request, order_id):
        """Returns all items for a specific order ID."""
        try:
            order = Order.objects.get(id=order_id, user=request.user)
        except Order.DoesNotExist:
            return Response({"detail": "Order not found."}, status=HTTP_404_NOT_FOUND)

        serializer = OrderSerializer(order)
        return Response(serializer.data, status=HTTP_200_OK)
    
    def patch(self, request, order_id):
        """Updates order status or delivery crew."""
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return Response({"detail": "Order not found."}, status=HTTP_404_NOT_FOUND)

        if request.user.groups.filter(name='Manager').exists():
            delivery_crew_id = request.data.get('delivery_crew')
            status = request.data.get('status')

            if delivery_crew_id:
                try:
                    delivery_crew = User.objects.get(id=delivery_crew_id)
                    order.delivery_crew = delivery_crew
                except User.DoesNotExist:
                    return Response({"detail": "Delivery crew not found."}, status=HTTP_404_NOT_FOUND)

            if status is not None:
                order.status = status

            order.save()
            return Response({"detail": "Order updated."}, status=HTTP_200_OK)
        
        elif request.user.groups.filter(name='Delivery Crew').exists():
            status = request.data.get('status')
            if status is not None:
                order.status = status
                order.save()
                return Response({"detail": "Order status updated."}, status=HTTP_200_OK)
            return Response({"detail": "Invalid status."}, status=HTTP_400_BAD_REQUEST)

        return Response({"detail": "Permission denied."}, status=HTTP_400_BAD_REQUEST)
    

    def delete(self, request, order_id):
        """Deletes the order."""
        try:
            order = Order.objects.get(id=order_id)
            order.delete()
            return Response({"detail": "Order deleted."}, status=HTTP_204_NO_CONTENT)
        except Order.DoesNotExist:
            return Response({"detail": "Order not found."}, status=HTTP_404_NOT_FOUND)