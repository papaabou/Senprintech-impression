from django.contrib import admin
from .models import Category, ContactRequest, Product, ProductOption, ProductOptionChoice


class ProductOptionChoiceInline(admin.TabularInline):
    model = ProductOptionChoice
    extra = 1


class ProductOptionInline(admin.TabularInline):
    model = ProductOption
    extra = 1

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]
    prepopulated_fields = {'slug':('name',)}
    
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", "price", "available", "created", "updated", "category"]
    list_filter = ["available", "category", "created", "updated"]
    list_editable = ["price", "available"]
    search_fields = ["name", "description"]
    prepopulated_fields = {'slug':('name',)}
    inlines = [ProductOptionInline]


@admin.register(ProductOption)
class ProductOptionAdmin(admin.ModelAdmin):
    list_display = ["name", "product", "code", "input_type", "required", "sort_order"]
    list_filter = ["input_type", "required", "product__category"]
    search_fields = ["name", "code", "product__name"]
    inlines = [ProductOptionChoiceInline]


@admin.register(ContactRequest)
class ContactRequestAdmin(admin.ModelAdmin):
    list_display = ["name", "email", "phone", "project_type", "email_sent", "created_at"]
    list_filter = ["project_type", "email_sent", "created_at"]
    search_fields = ["name", "email", "phone", "message"]
    readonly_fields = ["created_at"]
