"""
URL configuration for ecommercesite project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path, re_path
from ecommercesite.admin_dashboard import install_admin_dashboard
from ecommercesite import views

install_admin_dashboard(admin.site)

urlpatterns = [
    path('admin/', admin.site.urls),
    path("compte/", include("accounts.urls")),
    path("", include("quotes.urls")),
    path("confidentialite/", views.legal_page, {"page": "privacy"}, name="privacy_policy"),
    path("conditions-utilisation/", views.legal_page, {"page": "terms"}, name="terms"),
    path("conditions-vente/", views.legal_page, {"page": "sales"}, name="sales_terms"),
    path("livraison/", views.legal_page, {"page": "delivery"}, name="delivery_policy"),
    path("retours-remboursements/", views.legal_page, {"page": "returns"}, name="returns_policy"),
    path("mentions-legales/", views.legal_page, {"page": "legal_notice"}, name="legal_notice"),
    path("faq/", views.legal_page, {"page": "faq"}, name="faq"),
    path("cart/", include('cart.urls')),
    path("orders/", include("orders.urls")),
    path('', include('products.urls', namespace='products')),
   
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.SERVE_MEDIA_FILES:
    urlpatterns += [
        re_path(r"^media/(?P<path>.*)$", views.media_file),
    ]

