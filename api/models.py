from django.db import models
from django.core.validators import RegexValidator
import random

class User(models.Model):
    """Модель пользователя SHAMS"""
    phone_regex = RegexValidator(
        regex=r'^\+?992?\d{9}$',
        message="Номер телефона должен быть в формате: +992XXXXXXXXX (9 цифр после кода страны)"
    )
    phone = models.CharField(
        validators=[phone_regex],
        max_length=15,
        unique=True,
        verbose_name="Номер телефона"
    )
    name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Имя пользователя"
    )
    shams_id = models.CharField(
        max_length=10,
        unique=True,
        blank=True,
        null=True,
        verbose_name="SHAMS ID"
    )
    is_verified = models.BooleanField(
        default=False,
        verbose_name="Подтвержден"
    )
    verification_code = models.CharField(
        max_length=6,
        blank=True,
        null=True,
        verbose_name="Код подтверждения"
    )
    fcm_token = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name="FCM токен для уведомлений"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return f"{self.name or self.phone} - SHAMS-{self.shams_id or 'не присвоен'}"

    def generate_shams_id(self):
        while True:
            new_id = str(random.randint(1000, 9999))
            if not User.objects.filter(shams_id=new_id).exists():
                self.shams_id = new_id
                break
        return self.shams_id

    def generate_verification_code(self):
        code = str(random.randint(100000, 999999))
        self.verification_code = code
        return code


class CurrencyRate(models.Model):
    """Курс валют и настройки"""
    yuan_to_tmt = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=0.65,
        verbose_name="Курс юаня к сомони"
    )
    markup_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=3.0,
        verbose_name="Комиссия платформы (%)"
    )
    shipping_price_per_kg = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=15.0,
        verbose_name="Цена доставки за 1 кг"
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Настройка курса"
        verbose_name_plural = "Настройки курсов"

    def __str__(self):
        return f"1¥ = {self.yuan_to_tmt} TMT | Комиссия: {self.markup_percent}%"


class Order(models.Model):
    """Модель заказа"""
    STATUS_CHOICES = [
        ('pending', 'Ожидает оплаты'),
        ('purchased', 'Выкуплено'),
        ('in_china', 'На складе в Китае'),
        ('in_transit', 'В пути'),
        ('in_dushanbe', 'Прибыло в Душанбе'),
        ('delivered', 'Выдано'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    product_name = models.CharField(max_length=500, verbose_name="Название товара")
    product_url = models.URLField(verbose_name="Ссылка на товар", blank=True)
    product_image = models.URLField(verbose_name="Изображение товара", blank=True)
    price_yuan = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена в юанях")
    price_tmt = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена в сомони")
    markup_tmt = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Комиссия")
    total_tmt = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Итого к оплате")
    quantity = models.IntegerField(default=1, verbose_name="Количество")
    
    weight_kg = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Вес (кг)")
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Стоимость доставки")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    tracking_number = models.CharField(max_length=100, blank=True, verbose_name="Трек-номер")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"

    def __str__(self):
        return f"Заказ #{self.id} - {self.user.phone}"

    def get_china_label(self):
        return {
            'recipient_name': f'Shams Cargo SHAMS-{self.user.shams_id}',
            'address_line': f'Урумчи, склад SHAMS, ID: {self.user.shams_id}',
            'order_id': self.id,
            'shams_id': self.user.shams_id
        }


class Notification(models.Model):
    """Модель уведомлений"""
    NOTIFICATION_TYPES = [
        ('order_created', 'Заказ создан'),
        ('purchased', 'Выкуплено'),
        ('in_china', 'На складе в Китае'),
        ('weight_confirmed', 'Вес подтвержден'),
        ('in_transit', 'В пути'),
        ('in_dushanbe', 'Прибыло в Душанбе'),
        ('delivered', 'Выдано'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    order = models.ForeignKey(Order, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    title = models.CharField(max_length=200, verbose_name="Заголовок")
    body = models.TextField(verbose_name="Текст уведомления")
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    is_read = models.BooleanField(default=False, verbose_name="Прочитано")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Уведомление"
        verbose_name_plural = "Уведомления"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.user.phone}"


class CartItem(models.Model):
    """Модель корзины"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cart_items')
    product_id = models.CharField(max_length=100, verbose_name="ID товара")
    product_name = models.CharField(max_length=500, verbose_name="Название товара")
    product_image = models.URLField(verbose_name="Изображение", blank=True)
    price_yuan = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена в юанях")
    price_tmt = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена в сомони")
    quantity = models.IntegerField(default=1, verbose_name="Количество")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Товар в корзине"
        verbose_name_plural = "Товары в корзине"

    def get_total_tmt(self):
        return self.price_tmt * self.quantity

    def __str__(self):
        return f"{self.product_name} x{self.quantity} - {self.user.phone}"