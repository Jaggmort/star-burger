from django.db import models
from django.db.models import F, Sum
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.core.validators import MinValueValidator
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField
import requests

from .coordinates import fetch_coordinates


class Restaurant(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    address = models.CharField(
        'адрес',
        max_length=100,
        blank=True,
    )
    contact_phone = models.CharField(
        'контактный телефон',
        max_length=50,
        blank=True,
    )
    longitude = models.FloatField(
        'Долгота',
        null=True,
        blank=True,
    )
    latitude = models.FloatField(
        'Широта',
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = 'ресторан'
        verbose_name_plural = 'рестораны'

    def __str__(self):
        return self.name


class ProductQuerySet(models.QuerySet):
    def available(self):
        products = (
            RestaurantMenuItem.objects
            .filter(availability=True)
            .values_list('product')
        )
        return self.filter(pk__in=products)


class ProductCategory(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'категории'

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    category = models.ForeignKey(
        ProductCategory,
        verbose_name='категория',
        related_name='products',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    price = models.DecimalField(
        'цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    image = models.ImageField(
        'картинка'
    )
    special_status = models.BooleanField(
        'спец.предложение',
        default=False,
        db_index=True,
    )
    description = models.TextField(
        'описание',
        max_length=200,
        blank=True,
    )

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = 'товар'
        verbose_name_plural = 'товары'

    def __str__(self):
        return self.name


class RestaurantMenuItem(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        related_name='menu_items',
        verbose_name="ресторан",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='menu_items',
        verbose_name='продукт',
    )
    availability = models.BooleanField(
        'в продаже',
        default=True,
        db_index=True
    )

    class Meta:
        verbose_name = 'пункт меню ресторана'
        verbose_name_plural = 'пункты меню ресторана'
        unique_together = [
            ['restaurant', 'product']
        ]

    def __str__(self):
        return f"{self.restaurant.name} - {self.product.name}"


class OrderQuerySet(models.QuerySet):
    def total_price(self):
        price = (Sum(F('items__price')*F('items__quantity')))
        return self.annotate(price=price).prefetch_related('items')\
            .select_related('restaurant')


class Order(models.Model):
    ORDER_STATUS_CHOICES = [
        ('created', 'Создан'),
        ('cooking', 'Готовится'),
        ('delivering', 'Доставляется'),
        ('completed', 'Выполнен')
    ]
    PAYMENT_METHOD = [
        ('cash', 'Наличностью'),
        ('online', 'Электронно'),
        ('not_set', 'Не указанно'),
    ]
    address = models.CharField(
        'адрес',
        max_length=100,
        db_index=True,
    )
    longitude = models.FloatField(
        'Долгота',
        null=True,
        blank=True,
    )
    latitude = models.FloatField(
        'Широта',
        null=True,
        blank=True,
    )
    firstname = models.CharField(
        'имя',
        max_length=30,
        db_index=True,
    )
    lastname = models.CharField(
        'фамилия',
        max_length=30,
        db_index=True,
    )
    phonenumber = PhoneNumberField(
        'мобильный номер:',
        max_length=15,
        db_index=True,
    )
    status = models.CharField(
        'Статус заказа',
        max_length=20,
        choices=ORDER_STATUS_CHOICES,
        default='created',
        db_index=True,
    )
    comment = models.TextField(
        'Комментарий',
        blank=True,
    )
    registered_at = models.DateTimeField(
        'Дата регистрации',
        default=timezone.now,
        db_index=True,
    )
    called_at = models.DateTimeField(
        'Дата звонка',
        null=True,
        blank=True,
        db_index=True,
    )
    delivered_at = models.DateTimeField(
        'Дата доставки',
        null=True,
        blank=True,
        db_index=True,
    )
    payment = models.CharField(
        'Способ оплаты',
        max_length=20,
        choices=PAYMENT_METHOD,
        db_index=True,
        default='not_set'
    )
    restaurant = models.ForeignKey(
        'Restaurant',
        related_name='orders',
        verbose_name="Ресторан",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    objects = OrderQuerySet.as_manager()

    class Meta:
        verbose_name = 'заказ'
        verbose_name_plural = 'заказы'

    def __str__(self):
        return f'{self.lastname} {self.firstname}, {self.address}'


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        related_name='items',
        verbose_name="заказ",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='orders',
        verbose_name='товар',
    )
    quantity = models.IntegerField(
        'количество',
        db_index=True,
        validators=[MinValueValidator(1)]
    )
    price = models.DecimalField(
        'цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    class Meta:
        verbose_name = 'позиция заказа'
        verbose_name_plural = 'позиции заказа'

    def __str__(self):
        return f'{self.product.name} {self.order.lastname} {self.order.firstname}, {self.order.address}'


@receiver(post_save, sender=Restaurant)
def create_restaurant(sender, instance, created, **kwargs):
    api_key = settings.YANDEX_GEO_APIKEY
    if created:
        try:
            instance.latitude, instance.longitude = fetch_coordinates(
                api_key,
                instance.address,
            )
        except requests.exceptions.HTTPError:
            instance.latitude = None
            instance.longitude = None
        instance.save()


@receiver(post_save, sender=Restaurant)
def update_restaurant(sender, instance, **kwargs):
    api_key = settings.YANDEX_GEO_APIKEY
    try:
        instance.latitude, instance.longitude = fetch_coordinates(
            api_key,
            instance.address,
        )
    except requests.exceptions.HTTPError:
        instance.latitude = None
        instance.longitude = None
    post_save.disconnect(update_restaurant, sender=Restaurant)
    instance.save()
    post_save.connect(update_restaurant, sender=Restaurant)
