from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from decimal import Decimal
from .models import User, CurrencyRate, Order, CartItem
from .serializers import (
    UserSerializer, PhoneLoginSerializer, VerifyCodeSerializer, 
    SyncUserSerializer, CurrencyRateSerializer, CalculatePriceSerializer, 
    OrderSerializer, CartItemSerializer
)
import random
import string   

# ==================== АВТОРИЗАЦИЯ ====================

@api_view(['POST'])
def send_code(request):
    """Отправка SMS кода (пока без реальной SMS, просто имитация)"""
    serializer = PhoneLoginSerializer(data=request.data)
    if serializer.is_valid():
        phone = serializer.validated_data['phone']
        
        user, created = User.objects.get_or_create(phone=phone)
        code = user.generate_verification_code()
        user.save()
        
        return Response({
            'status': 'success',
            'message': 'Код подтверждения отправлен',
            'debug_code': code
        })
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def verify_code(request):
    """Подтверждение кода и выдача SHAMS ID"""
    serializer = VerifyCodeSerializer(data=request.data)
    if serializer.is_valid():
        phone = serializer.validated_data['phone']
        code = serializer.validated_data['code']
        
        try:
            user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            return Response({'error': 'Пользователь не найден'}, 
                          status=status.HTTP_404_NOT_FOUND)
        
        if user.verification_code != code:
            return Response({'error': 'Неверный код'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        user.is_verified = True
        
        if not user.shams_id:
            user.generate_shams_id()
        
        user.verification_code = None
        user.save()
        
        return Response({
            'status': 'success',
            'user': UserSerializer(user).data,
            'message': f'Добро пожаловать! Ваш SHAMS ID: {user.shams_id}. Сохраните его!'
        })
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def sync_user(request):
    """Синхронизация пользователя по телефону и SHAMS ID"""
    serializer = SyncUserSerializer(data=request.data)
    if serializer.is_valid():
        phone = serializer.validated_data['phone']
        shams_id = serializer.validated_data.get('shams_id')
        
        try:
            if shams_id:
                user = User.objects.get(phone=phone, shams_id=shams_id)
            else:
                user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            return Response({'error': 'Пользователь не найден. Проверьте номер телефона и SHAMS ID.'},
                          status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            'status': 'success',
            'user': UserSerializer(user).data
        })
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def get_user(request, phone):
    """Получение информации о пользователе"""
    try:
        user = User.objects.get(phone=phone)
        return Response(UserSerializer(user).data)
    except User.DoesNotExist:
        return Response({'error': 'Пользователь не найден'}, 
                      status=status.HTTP_404_NOT_FOUND)


# ==================== КАЛЬКУЛЯТОР ====================

@api_view(['GET'])
def get_rates(request):
    """Получить текущие курсы и настройки"""
    rate = CurrencyRate.objects.first()
    if not rate:
        rate = CurrencyRate.objects.create()
    return Response(CurrencyRateSerializer(rate).data)

@api_view(['POST'])
def calculate_price(request):
    """Калькулятор цены: юань → сомони + комиссия"""
    serializer = CalculatePriceSerializer(data=request.data)
    if serializer.is_valid():
        rate = CurrencyRate.objects.first()
        if not rate:
            rate = CurrencyRate.objects.create()
        
        price_yuan = Decimal(str(serializer.validated_data['price_yuan']))
        
        price_tmt = price_yuan * rate.yuan_to_tmt
        markup = price_tmt * (rate.markup_percent / Decimal('100'))
        total = price_tmt + markup
        
        result = {
            'price_yuan': float(price_yuan),
            'price_tmt': float(price_tmt),
            'markup_percent': float(rate.markup_percent),
            'markup_tmt': float(markup),
            'total_tmt': float(total)
        }
        
        if serializer.validated_data.get('weight_kg'):
            weight = Decimal(str(serializer.validated_data['weight_kg']))
            shipping = weight * rate.shipping_price_per_kg
            result['weight_kg'] = float(weight)
            result['shipping_cost'] = float(shipping)
            result['total_with_shipping'] = float(total + shipping)
        
        return Response(result)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ==================== ЗАКАЗЫ ====================

@api_view(['POST'])
def create_order(request):
    """Создание нового заказа"""
    serializer = OrderSerializer(data=request.data)
    if serializer.is_valid():
        order = serializer.save()
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def user_orders(request, phone):
    """Получить все заказы пользователя"""
    try:
        user = User.objects.get(phone=phone)
        orders = Order.objects.filter(user=user).order_by('-created_at')
        return Response(OrderSerializer(orders, many=True).data)
    except User.DoesNotExist:
        return Response({'error': 'Пользователь не найден'}, status=status.HTTP_404_NOT_FOUND)


# ==================== КОРЗИНА ====================

@api_view(['POST'])
def add_to_cart(request):
    """Добавить товар в корзину"""
    serializer = CartItemSerializer(data=request.data)
    if serializer.is_valid():
        phone = request.data.get('user')
        try:
            user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            return Response({'error': 'Пользователь не найден'}, status=status.HTTP_404_NOT_FOUND)
        
        cart_item = serializer.save(user=user)
        return Response(CartItemSerializer(cart_item).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def get_cart(request, phone):
    """Получить корзину пользователя"""
    try:
        user = User.objects.get(phone=phone)
        cart_items = CartItem.objects.filter(user=user).order_by('-created_at')
        total = sum(item.get_total_tmt() for item in cart_items)
        return Response({
            'items': CartItemSerializer(cart_items, many=True).data,
            'total': float(total)
        })
    except User.DoesNotExist:
        return Response({'error': 'Пользователь не найден'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['DELETE'])
def remove_from_cart(request, item_id):
    """Удалить товар из корзины"""
    try:
        cart_item = CartItem.objects.get(id=item_id)
        cart_item.delete()
        return Response({'status': 'deleted'})
    except CartItem.DoesNotExist:
        return Response({'error': 'Товар не найден'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
def update_cart_quantity(request, item_id):
    """Обновить количество товара в корзине"""
    try:
        cart_item = CartItem.objects.get(id=item_id)
        quantity = request.data.get('quantity', 1)
        cart_item.quantity = quantity
        cart_item.save()
        return Response(CartItemSerializer(cart_item).data)
    except CartItem.DoesNotExist:
        return Response({'error': 'Товар не найден'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
def checkout(request):
    """Оформить заказ из корзины"""
    phone = request.data.get('phone')
    print(f"[DEBUG] Checkout для телефона: {phone}")  # Отладка
    
    try:
        user = User.objects.get(phone=phone)
        print(f"[DEBUG] Найден пользователь: {user.phone}, SHAMS ID: {user.shams_id}")
        
        cart_items = CartItem.objects.filter(user=user)
        print(f"[DEBUG] Товаров в корзине: {cart_items.count()}")
        
        if not cart_items.exists():
            return Response({'error': 'Корзина пуста'}, status=status.HTTP_400_BAD_REQUEST)
        
        rate = CurrencyRate.objects.first()
        if not rate:
            rate = CurrencyRate.objects.create()
        
        orders = []
        total_amount = 0
        
        for item in cart_items:
            markup = item.price_tmt * (rate.markup_percent / Decimal('100'))
            
            order = Order.objects.create(
                user=user,
                product_name=item.product_name,
                product_url='',
                product_image=item.product_image,
                price_yuan=item.price_yuan,
                price_tmt=item.price_tmt,
                markup_tmt=markup,
                total_tmt=item.get_total_tmt() + markup,
                quantity=item.quantity,
                status='pending'
            )
            orders.append(order)
            total_amount += float(order.total_tmt)
            print(f"[DEBUG] Создан заказ #{order.id} для {order.user.phone}")
        
        # Очищаем корзину
        cart_items.delete()
        print(f"[DEBUG] Корзина очищена, создано {len(orders)} заказов")
        
        return Response({
            'status': 'success',
            'orders': OrderSerializer(orders, many=True).data,
            'total': total_amount
        }, status=status.HTTP_201_CREATED)
        
    except User.DoesNotExist:
        print(f"[DEBUG] Пользователь с телефоном {phone} НЕ НАЙДЕН!")
        return Response({'error': 'Пользователь не найден'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(f"[DEBUG] Ошибка: {e}")
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    # ==================== УПРАВЛЕНИЕ ЗАКАЗАМИ (ДЛЯ АДМИНА) ====================

@api_view(['POST'])
def update_order_status(request, order_id):
    """Обновить статус заказа (вызывается из админки или webhook)"""
    try:
        order = Order.objects.get(id=order_id)
        new_status = request.data.get('status')
        
        if new_status not in dict(Order.STATUS_CHOICES):
            return Response({'error': 'Неверный статус'}, status=status.HTTP_400_BAD_REQUEST)
        
        order.status = new_status
        order.save()
        
        return Response({
            'status': 'success',
            'order': OrderSerializer(order).data
        })
    except Order.DoesNotExist:
        return Response({'error': 'Заказ не найден'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
def update_order_weight(request, order_id):
    """Обновить вес заказа и рассчитать доставку"""
    try:
        order = Order.objects.get(id=order_id)
        weight_kg = Decimal(str(request.data.get('weight_kg', 0)))
        
        if weight_kg <= 0:
            return Response({'error': 'Вес должен быть больше 0'}, status=status.HTTP_400_BAD_REQUEST)
        
        order.weight_kg = weight_kg
        
        rate = CurrencyRate.objects.first()
        if rate:
            shipping = weight_kg * rate.shipping_price_per_kg
            order.shipping_cost = shipping
            
            # Обновляем общую сумму (товар + доставка)
            order.total_tmt = order.total_tmt + shipping
        
        order.save()
        
        return Response({
            'status': 'success',
            'order': OrderSerializer(order).data,
            'shipping_cost': float(order.shipping_cost),
            'total_with_shipping': float(order.total_tmt)
        })
    except Order.DoesNotExist:
        return Response({'error': 'Заказ не найден'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
def add_tracking_number(request, order_id):
    """Добавить трек-номер для заказа"""
    try:
        order = Order.objects.get(id=order_id)
        tracking_number = request.data.get('tracking_number', '')
        
        if tracking_number:
            order.tracking_number = tracking_number
            order.save()
        
        return Response({
            'status': 'success',
            'tracking_number': order.tracking_number
        })
    except Order.DoesNotExist:
        return Response({'error': 'Заказ не найден'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
def get_order_by_shams_id(request, shams_id):
    """Получить заказы по SHAMS ID (для выдачи на складе)"""
    try:
        user = User.objects.get(shams_id=shams_id)
        orders = Order.objects.filter(user=user, status__in=['in_dushanbe', 'delivered']).order_by('-created_at')
        
        total_weight = sum(float(o.weight_kg) if o.weight_kg else 0 for o in orders)
        total_due = sum(float(o.shipping_cost) if o.shipping_cost else 0 for o in orders if o.status == 'in_dushanbe')
        
        return Response({
            'user': {
                'phone': user.phone,
                'shams_id': user.shams_id
            },
            'orders': OrderSerializer(orders, many=True).data,
            'total_weight': total_weight,
            'total_due': total_due
        })
    except User.DoesNotExist:
        return Response({'error': 'Пользователь с таким SHAMS ID не найден'}, status=status.HTTP_404_NOT_FOUND)

def send_push_notification(user_phone, title, body):
    """Отправить push-уведомление пользователю"""
    # Здесь будет интеграция с Firebase Cloud Messaging
    # Пока заглушка
    print(f"Уведомление для {user_phone}: {title} - {body}")