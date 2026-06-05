from django.contrib import admin
from django.utils.html import format_html
from .models import User, CurrencyRate, Order, CartItem
from decimal import Decimal
from django.db.models import Sum, Count
from django.contrib.admin import AdminSite
from django.shortcuts import render

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['phone', 'shams_id', 'is_verified', 'created_at']
    list_filter = ['is_verified']
    search_fields = ['phone', 'shams_id']
    readonly_fields = ['shams_id', 'verification_code', 'created_at', 'updated_at']

@admin.register(CurrencyRate)
class CurrencyRateAdmin(admin.ModelAdmin):
    list_display = ['yuan_to_tmt', 'markup_percent', 'shipping_price_per_kg', 'updated_at']
    fieldsets = (
        ('Курсы валют', {
            'fields': ('yuan_to_tmt',)
        }),
        ('Настройки комиссии', {
            'fields': ('markup_percent',)
        }),
        ('Стоимость доставки за кг', {
            'fields': ('shipping_price_per_kg',)
        }),
    )

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'product_name', 'quantity', 'price_tmt', 'created_at']
    list_filter = ['created_at']
    search_fields = ['product_name', 'user__phone']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user_phone', 'product_name_short', 'quantity', 'weight_display', 'total_tmt', 'status_tag', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['product_name', 'user__phone', 'user__shams_id', 'tracking_number']
    readonly_fields = ['price_yuan', 'price_tmt', 'markup_tmt', 'total_tmt', 'created_at']
    
    fieldsets = (
        ('Информация о пользователе', {
            'fields': ('user',)
        }),
        ('Информация о товаре', {
            'fields': ('product_name', 'product_url', 'product_image', 'price_yuan', 'price_tmt', 'markup_tmt', 'total_tmt', 'quantity')
        }),
        ('Логистика', {
            'fields': ('weight_kg', 'shipping_cost', 'tracking_number', 'status')
        }),
    )
    
    actions = ['mark_as_purchased', 'mark_as_in_china', 'mark_as_in_transit', 'mark_as_in_dushanbe', 'mark_as_delivered']
    
    def user_phone(self, obj):
        return obj.user.phone
    user_phone.short_description = 'Телефон'
    user_phone.admin_order_field = 'user__phone'
    
    def product_name_short(self, obj):
        return obj.product_name[:50] + '...' if len(obj.product_name) > 50 else obj.product_name
    product_name_short.short_description = 'Товар'
    
    def weight_display(self, obj):
        if obj.weight_kg:
            shipping = float(obj.weight_kg) * 15
            return format_html('<b>{}</b> кг<br>(доставка: {} TMT)', obj.weight_kg, shipping)
        return '-'
    weight_display.short_description = 'Вес / Доставка'
    
    def status_tag(self, obj):
        colors = {
            'pending': 'gray',
            'purchased': 'blue',
            'in_china': 'orange',
            'in_transit': 'purple',
            'in_dushanbe': 'green',
            'delivered': 'darkgreen',
        }
        texts = {
            'pending': '⏳ Ожидает',
            'purchased': '🛒 Выкуплено',
            'in_china': '📦 В Китае',
            'in_transit': '🚚 В пути',
            'in_dushanbe': '📍 В Душанбе',
            'delivered': '✅ Выдано',
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 8px; border-radius: 12px; font-size: 11px;">{}</span>',
            colors.get(obj.status, 'gray'),
            texts.get(obj.status, obj.status)
        )
    status_tag.short_description = 'Статус'
    
    def save_model(self, request, obj, form, change):
        # При сохранении веса автоматически рассчитываем доставку
        if obj.weight_kg:
            rate = CurrencyRate.objects.first()
            if rate:
                shipping = Decimal(str(obj.weight_kg)) * rate.shipping_price_per_kg
                obj.shipping_cost = shipping
        super().save_model(request, obj, form, change)
    
    def mark_as_purchased(self, request, queryset):
        queryset.update(status='purchased')
    mark_as_purchased.short_description = 'Отметить как "Выкуплено"'
    
    def mark_as_in_china(self, request, queryset):
        queryset.update(status='in_china')
    mark_as_in_china.short_description = 'Отметить как "На складе в Китае"'
    
    def mark_as_in_transit(self, request, queryset):
        queryset.update(status='in_transit')
    mark_as_in_transit.short_description = 'Отметить как "В пути"'
    
    def mark_as_in_dushanbe(self, request, queryset):
        queryset.update(status='in_dushanbe')
    mark_as_in_dushanbe.short_description = 'Отметить как "Прибыло в Душанбе"'
    
    def mark_as_delivered(self, request, queryset):
        queryset.update(status='delivered')
    mark_as_delivered.short_description = 'Отметить как "Выдано"'

class DashboardStats:
    @staticmethod
    def get_stats():
        total_orders = Order.objects.count()
        completed_orders = Order.objects.filter(status='delivered').count()
        pending_orders = Order.objects.filter(status='pending').count()
        
        # Общая выручка
        total_revenue = Order.objects.aggregate(total=Sum('total_tmt'))['total'] or 0
        
        # Прибыль от комиссии (3%)
        total_commission = Order.objects.aggregate(total=Sum('markup_tmt'))['total'] or 0
        
        # Общий вес отправленных грузов
        total_weight = Order.objects.filter(weight_kg__isnull=False).aggregate(total=Sum('weight_kg'))['total'] or 0
        
        return {
            'total_orders': total_orders,
            'completed_orders': completed_orders,
            'pending_orders': pending_orders,
            'total_revenue': float(total_revenue),
            'total_commission': float(total_commission),
            'total_weight': float(total_weight),
        }


class ShamsAdminSite(AdminSite):
    site_header = 'SHAMS Admin Panel'
    site_title = 'SHAMS Admin'
    
    def index(self, request, extra_context=None):
        stats = DashboardStats.get_stats()
        extra_context = extra_context or {}
        extra_context['stats'] = stats
        return super().index(request, extra_context)
