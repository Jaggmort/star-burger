import requests
from django.conf import settings
from django.contrib import admin
from django.shortcuts import reverse
from django.shortcuts import redirect
from django.templatetags.static import static
from django.urls.exceptions import NoReverseMatch
from django.utils.encoding import iri_to_uri
from django.utils.html import format_html
from django.utils.http import url_has_allowed_host_and_scheme

from .models import Product
from .models import Restaurant
from .models import RestaurantMenuItem
from .models import Order
from .models import OrderItem

from .coordinates import fetch_coordinates


class RestaurantMenuItemInline(admin.TabularInline):
    model = RestaurantMenuItem
    extra = 0


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    search_fields = [
        'name',
        'address',
        'contact_phone',
    ]
    list_display = [
        'name',
        'address',
        'contact_phone',
    ]
    readonly_fields = (
        'latitude',
        'longitude',
    )
    inlines = [
        RestaurantMenuItemInline
    ]

    actions = ['get_coordinates']

    def get_coordinates(self, request, queryset):
        api_key = settings.YANDEX_GEO_APIKEY
        for query in queryset:
            try:
                query.latitude, query.longitude = fetch_coordinates(
                    api_key,
                    query.address,
                )
            except requests.exceptions.HTTPError:
                query.latitude = None
                query.longitude = None
            query.save()

    get_coordinates.short_description = 'get coordinates'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'get_image_list_preview',
        'name',
        'category',
        'price',
    ]
    list_display_links = [
        'name',
    ]
    list_filter = [
        'category',
    ]
    search_fields = [
        'name',
        'category__name',
    ]

    inlines = [
        RestaurantMenuItemInline
    ]
    fieldsets = (
        ('Общее', {
            'fields': [
                'name',
                'category',
                'image',
                'get_image_preview',
                'price',
            ]
        }),
        ('Подробно', {
            'fields': [
                'special_status',
                'description',
            ],
            'classes': [
                'wide'
            ],
        }),
    )

    readonly_fields = [
        'get_image_preview',
    ]

    class Media:
        css = {
            "all": (
                static("admin/foodcartapp.css")
            )
        }

    def get_image_preview(self, obj):
        if not obj.image:
            return 'выберите картинку'
        return format_html('<img src="{url}" style="max-height: 200px;"/>', url=obj.image.url)
    get_image_preview.short_description = 'превью'

    def get_image_list_preview(self, obj):
        if not obj.image or not obj.id:
            return 'нет картинки'
        edit_url = reverse('admin:foodcartapp_product_change', args=(obj.id,))
        return format_html('<a href="{edit_url}"><img src="{src}" style="max-height: 50px;"/></a>', edit_url=edit_url, src=obj.image.url)
    get_image_list_preview.short_description = 'превью'


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    search_fields = [
        'address',
        'firstname',
        'lastname',
        'phonenumber',
    ]
    list_display = [
        'address',
        'firstname',
        'lastname',
        'phonenumber',
    ]
    readonly_fields = (
        'latitude',
        'longitude',
    )
    inlines = [
        OrderItemInline
    ]

    def response_post_save_change(self, request, obj):
        res = super().response_post_save_change(request, obj)
        try:
            if 'next' in request.GET and url_has_allowed_host_and_scheme(request.GET['next'], None):
                url = iri_to_uri(request.GET['next'])
                return redirect(url)
            else:
                return res
        except NoReverseMatch:
            return res
