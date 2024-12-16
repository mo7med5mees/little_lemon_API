from django.urls import path, include
from . import views

from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'menu-items', views.MenuItemViewSet, basename='menuitem')


urlpatterns = [
    path('register/', views.RegisterUserAPIView.as_view()),
    path('customer-dashboard/', views.customer_dashboard),

    path('', include(router.urls)),

    path('auth-token/', obtain_auth_token),

    path('api/users/', include('djoser.urls')),  # For user registration and management
    path('token/', include('djoser.urls.authtoken')), 


    path('api/groups/manager/users', views.ManagerUsersView.as_view(), name='manager-users'),
    path('api/groups/manager/users/<int:user_id>', views.ManagerUserDetailView.as_view(), name='manager-user-detail'),
    path('api/groups/delivery-crew/users', views.DeliveryCrewUsersView.as_view(), name='delivery-crew-users'),
    path('api/groups/delivery-crew/users/<int:user_id>', views.DeliveryCrewUserDetailView.as_view(), name='delivery-crew-user-detail'),
    path('api/cart/menu-items', views.CartManagementView.as_view(), name='cart-management'),
    path('api/orders', views.OrderManagementView.as_view(), name='order-management'),
    path('api/orders/<int:order_id>', views.OrderDetailView.as_view(), name='order-detail'),
]