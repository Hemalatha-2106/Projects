from django.urls import path
from . import views

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('add/<int:id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.view_cart, name='view_cart'),
    path('remove/<int:id>/', views.remove_from_cart, name='remove_from_cart'),
    path('update-cart/<int:id>/<str:action>/', views.update_cart, name='update_cart'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.user_login, name='user_login'),
    path('logout/', views.user_logout, name='user_logout'),
    path('profile/', views.profile, name='profile'),
    path('address/', views.manage_address, name='manage_address'),
    path('product/<int:id>/', views.product_detail, name='product_detail'),
    path('checkout/', views.checkout, name='checkout'),
    path('saved-addresses/', views.saved_addresses, name='saved_addresses'),
    path('my-orders/', views.my_orders, name='my_orders'),
   path( 'cancel-order/<int:order_id>/', views.cancel_order, name='cancel_order',
),
]

