from django.contrib import admin
from django.utils.html import format_html

from .models import ContactRequest, QuoteRequest


@admin.register(QuoteRequest)
class QuoteRequestAdmin(admin.ModelAdmin):
    list_display = ["id", "company_name", "contact_name", "product_type", "status", "created_at"]
    list_filter = ["status", "product_type", "created_at"]
    list_editable = ["status"]
    search_fields = ["company_name", "contact_name", "email", "phone", "product_type"]
    readonly_fields = ["created_at", "updated_at", "uploaded_file_link"]
    fieldsets = [
        ("Client", {"fields": ["user", "company_name", "contact_name", "email", "phone"]}),
        ("Projet", {"fields": ["product_type", "desired_quantity", "desired_deadline", "estimated_budget", "message"]}),
        ("Fichier", {"fields": ["uploaded_file", "uploaded_file_link"]}),
        ("Suivi", {"fields": ["status", "created_at", "updated_at"]}),
    ]

    def uploaded_file_link(self, obj):
        if not obj.uploaded_file:
            return "-"
        return format_html(
            "<a href='{}' target='_blank' rel='noopener'>{}</a>",
            obj.uploaded_file.url,
            obj.uploaded_file.name.split("/")[-1],
        )

    uploaded_file_link.short_description = "Fichier client"


@admin.register(ContactRequest)
class ContactRequestAdmin(admin.ModelAdmin):
    list_display = ["name", "email", "phone", "project_type", "email_sent", "created_at"]
    list_filter = ["project_type", "email_sent", "created_at"]
    search_fields = ["name", "email", "phone", "message"]
    readonly_fields = ["created_at"]
