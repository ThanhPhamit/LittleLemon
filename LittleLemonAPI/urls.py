from django.urls import path, include
from . import views
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework import routers


urlpatterns = [
    # STUDYING API
    # Using model serializers
    # path('menu-items', views.MenuItemsView.as_view()),
    # path('menu-items/<int:pk>', views.SingleMenuItemView.as_view()),
    # path('category', views.CategoryView.as_view()),
    # path('category/<int:pk>', views.SingleCategoryView.as_view()),
    # path('ratings/', views.RatingsView.as_view()),
    # # Using serializers
    # path('menu-items/', views.menu_items),
    # # path('menu-items/<int:id>', views.single_item)

    # path('secret/', views.secret),
    # path('api-token-auth/', obtain_auth_token),
    # path('manager-view/', views.manager_view),
    # path('throttle-check/', views.throttle_check),
    # path('throttle-check-auth/', views.throttle_check_auth),

    # # Admin page
    # path('groups/manager/users/', views.admin_page)

    # IMPLEMENTATION
    # User registration and token generation endpoints
    path('users/', include('djoser.urls')),
    path('', include('djoser.urls.authtoken')),

    # Menu items endpoints
    path('menu-items', views.MenuItemList.as_view(), name=views.MenuItemList.menu_item_view_name),
    path('menu-items/<int:pk>', views.SingleMenuItemView.as_view()),

    # Manager
    path('groups/manager/users', views.ManagerListView.as_view()),
    path('groups/manager/users/<int:pk>', views.SingleManagerView.as_view()),
    path('groups/delivery-crew/users', views.DeliveryCrewView.as_view()),
    path('groups/delivery-crew/users/<int:pk>', views.SingleDeliveryPersonView.as_view()),

    # Cart
    path('cart/menu-items', views.CartView.as_view()),

    # Order
    path('orders', views.OrderListView.as_view()),
    path('orders/<int:pk>', views.SingleOrderView.as_view()),


]