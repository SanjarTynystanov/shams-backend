from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum, Count
from .models import User, CurrencyRate, Order, CartItem, Notification
from decimal import Decimal

# ========== НАСТРОЙКИ АДМИНКИ ==========

admin.site.site_header = 'SHAMS Cargo — Админ-панель'
admin.site.site_title = 'SHAMS Admin'
admin.site.index_title = 'Управление платформой SHAMS'

# ========== ДАШБОРД ==========

class DashboardStats:
    @staticmethod
    def get_stats():
        total_orders = Order.objects.count()
        pending_orders = Order.objects.filter(status='pending').count()
        completed_orders = Order.objects.filter(status='delivered').count()
        
        total_revenue = Order.objects.aggregate(total=Sum('total_tmt'))['total'] or 0
        total_commission = Order.objects.aggregate(total=Sum('markup_tmt'))['total'] or 0
        total_weight = Order.objects.filter(weight_kg__isnull=False).aggregate(total=Sum('weight_kg'))['total'] or 0
        
        return {
            'total_orders': total_orders,
            'pending_orders': pending_orders,
            'completed_orders': completed_orders,
            'total_revenue': float(total_revenue),
            'total_commission': float(total_commission),
            'total_weight': float(total_weight),
        }

# ========== РЕГИСТРАЦИЯ МОДЕЛЕЙ ==========

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['phone', 'name', 'shams_id', 'is_verified', 'created_at']
    list_filter = ['is_verified']
    search_fields = ['phone', 'shams_id', 'name']
    readonly_fields = ['shams_id', 'verification_code', 'fcm_token', 'created_at', 'updated_at']
    fieldsets = (
        ('📱 Основная информация', {
            'fields': ('phone', 'name', 'shams_id', 'is_verified')
        }),
        ('🔐 Безопасность', {
            'fields': ('verification_code', 'fcm_token')
        }),
        ('📅 Даты', {
            'fields': ('created_at', 'updated_at')
        }),
    )

@admin.register(CurrencyRate)
class CurrencyRateAdmin(admin.ModelAdmin):
    list_display = ['yuan_to_tmt', 'markup_percent', 'shipping_price_per_kg', 'updated_at']
    fieldsets = (
        ('💱 Курсы валют', {
            'fields': ('yuan_to_tmt',)
        }),
        ('💰 Настройки комиссии', {
            'fields': ('markup_percent',)
        }),
        ('🚚 Стоимость доставки', {
            'fields': ('shipping_price_per_kg',)
        }),
    )

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'product_name', 'quantity', 'price_tmt', 'created_at']
    list_filter = ['created_at']
    search_fields = ['product_name', 'user__phone', 'user__name']

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'title', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['title', 'body', 'user__phone', 'user__name']
    readonly_fields = ['created_at']
    
    def has_add_permission(self, request):
        return False

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user_phone', 'user_name', 'product_name_short', 'quantity', 'weight_display', 'total_tmt', 'status_badge', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['product_name', 'user__phone', 'user__name', 'user__shams_id', 'tracking_number']
    readonly_fields = ['price_yuan', 'price_tmt', 'markup_tmt', 'total_tmt', 'created_at']
    
    fieldsets = (
        ('👤 Информация о пользователе', {
            'fields': ('user',)
        }),
        ('📦 Информация о товаре', {
            'fields': ('product_name', 'product_url', 'product_image', 'price_yuan', 'price_tmt', 'markup_tmt', 'total_tmt', 'quantity')
        }),
        ('🚚 Логистика', {
            'fields': ('weight_kg', 'shipping_cost', 'tracking_number', 'status')
        }),
    )
    
    actions = ['mark_as_purchased', 'mark_as_in_china', 'mark_as_in_transit', 'mark_as_in_dushanbe', 'mark_as_delivered']
    
    def user_phone(self, obj):
        return obj.user.phone
    user_phone.short_description = '📞 Телефон'
    
    def user_name(self, obj):
        return obj.user.name or '—'
    user_name.short_description = '👤 Имя'
    
    def product_name_short(self, obj):
        return obj.product_name[:40] + '...' if len(obj.product_name) > 40 else obj.product_name
    product_name_short.short_description = '📦 Товар'
    
    def weight_display(self, obj):
        if obj.weight_kg:
            shipping = float(obj.weight_kg) * 15
            return format_html('<span style="color:#FF7A00"><b>{}</b> кг</span><br><span style="color:#666;font-size:11px;">🚚 Доставка: {} TMT</span>', obj.weight_kg, shipping)
        return '—'
    weight_display.short_description = '⚖️ Вес / Доставка'
    
    def status_badge(self, obj):
        colors = {
            'pending': '#FF6B6B',      # красный
            'purchased': '#4ECDC4',    # бирюзовый
            'in_china': '#FFA94D',     # оранжевый
            'in_transit': '#4DABF7',   # синий
            'in_dushanbe': '#FF7A00',  # фирменный оранжевый
            'delivered': '#51CF66',    # зеленый
        }
        texts = {
            'pending': '⏳ Ожидает оплаты',
            'purchased': '🛒 Выкуплено',
            'in_china': '📦 На складе в Китае',
            'in_transit': '🚚 В пути',
            'in_dushanbe': '📍 В Душанбе',
            'delivered': '✅ Выдано',
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 500;">{}</span>',
            colors.get(obj.status, '#6c757d'),
            texts.get(obj.status, obj.status)
        )
    status_badge.short_description = '📌 Статус'
    
    def save_model(self, request, obj, form, change):
        if obj.weight_kg:
            rate = CurrencyRate.objects.first()
            if rate:
                shipping = Decimal(str(obj.weight_kg)) * rate.shipping_price_per_kg
                obj.shipping_cost = shipping
        super().save_model(request, obj, form, change)
    
    def mark_as_purchased(self, request, queryset):
        queryset.update(status='purchased')
    mark_as_purchased.short_description = '🛒 Отметить как "Выкуплено"'
    
    def mark_as_in_china(self, request, queryset):
        queryset.update(status='in_china')
    mark_as_in_china.short_description = '📦 Отметить как "На складе в Китае"'
    
    def mark_as_in_transit(self, request, queryset):
        queryset.update(status='in_transit')
    mark_as_in_transit.short_description = '🚚 Отметить как "В пути"'
    
    def mark_as_in_dushanbe(self, request, queryset):
        queryset.update(status='in_dushanbe')
    mark_as_in_dushanbe.short_description = '📍 Отметить как "Прибыло в Душанбе"'
    
    def mark_as_delivered(self, request, queryset):
        queryset.update(status='delivered')
    mark_as_delivered.short_description = '✅ Отметить как "Выдано"'

from django.contrib.admin import AdminSite
from django.shortcuts import render

class ShamsAdminSite(AdminSite):
    site_header = 'SHAMS Cargo — Админ-панель'
    site_title = 'SHAMS Admin'
    index_template = 'admin/dashboard.html'
    
    def index(self, request, extra_context=None):
        stats = DashboardStats.get_stats()
        extra_context = extra_context or {}
        extra_context['stats'] = stats
        return super().index(request, extra_context)

# Замени стандартный admin_site (в самом конце файла)
# Удали или закомментируй строки, где используется admin.site.register
# И вместо них используй:

# shams_admin_site = ShamsAdminSite(name='shams_admin')

# Но проще оставить как есть, просто добавив кастомный шаблон