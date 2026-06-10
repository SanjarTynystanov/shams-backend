from django.urls import path
from . import views

urlpatterns = [
    # АВТОРИЗАЦИЯ
    path('send-code/', views.send_code, name='send_code'),
    path('verify-code/', views.verify_code, name='verify_code'),
    path('sync-user/', views.sync_user, name='sync_user'),
    path('user/<str:phone>/', views.get_user, name='get_user'),
    path('user/update-name/', views.update_user_name, name='update_user_name'),
    path('user/save-fcm-token/', views.save_fcm_token, name='save_fcm_token'),
    path('user/notifications/<str:phone>/', views.get_user_notifications, name='get_user_notifications'),
    path('notification/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('create-notification/', views.create_notification, name='create_notification'),
    # КАЛЬКУЛЯТОР
    path('rates/', views.get_rates, name='get_rates'),
    path('calculate/', views.calculate_price, name='calculate_price'),
    
    # ЗАКАЗЫ
    path('create-order/', views.create_order, name='create_order'),
    path('orders/<str:phone>/', views.user_orders, name='user_orders'),
    
    # КОРЗИНА
    path('cart/add/', views.add_to_cart, name='add_to_cart'),
    path('cart/<str:phone>/', views.get_cart, name='get_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/update/<int:item_id>/', views.update_cart_quantity, name='update_cart_quantity'),
    path('checkout/', views.checkout, name='checkout'),
    
    # УПРАВЛЕНИЕ ЗАКАЗАМИ (АДМИН)
    path('order/<int:order_id>/status/', views.update_order_status, name='update_order_status'),
    path('order/<int:order_id>/weight/', views.update_order_weight, name='update_order_weight'),
    path('order/<int:order_id>/tracking/', views.add_tracking_number, name='add_tracking_number'),
    path('orders/shams/<str:shams_id>/', views.get_order_by_shams_id, name='get_order_by_shams_id'),

    path('create-notification/', views.create_notification, name='create_notification'),
]