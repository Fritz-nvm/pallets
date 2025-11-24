from django.contrib import admin
from .models import Category, Item, ItemImage


class ItemImageInline(admin.TabularInline):
    model = ItemImage
    extra = 1
    fields = ["image", "alt_text", "is_primary", "order"]


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "vendor",
        "current_price",
        "quantity",
        "category",
        "is_active",
    ]
    list_filter = ["vendor", "category", "is_active"]
    search_fields = ["title", "vendor"]
    readonly_fields = ["created_at", "updated_at"]
    inlines = [ItemImageInline]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]


@admin.register(ItemImage)
class ItemImageAdmin(admin.ModelAdmin):
    list_display = ["item", "image", "is_primary", "order"]
    list_editable = ["is_primary", "order"]
