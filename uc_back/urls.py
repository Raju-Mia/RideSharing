from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from django.conf.urls import include
from django.urls import re_path


from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Swagger schema configuration
schema_view = get_schema_view(
    openapi.Info(
        title="Your Project API",
        default_version='v1',
        description="API documentation grouped by apps",
        terms_of_service="https://example.com/terms/",
        contact=openapi.Contact(email="support@example.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)


urlpatterns = [
    
    # Swagger and Redoc
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    # path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    # path('', include('broadcast.urls')),
    path("default-admin/", admin.site.urls), # Default Admin Panel
    path("api/", include("organization_manager.urls")),
    path("api/", include("third_party_org_manager.urls")),
    path("api/", include("accounts.urls")), # Accounts Managment
    path("api/", include("client_app.urls")),
    path("api/", include("driver_app.urls")), # Driver App
    # path("api/", include("trip.urls")),
    path("api/", include("trip_management.urls")),
    path("api/", include("complaint_box.urls")),
    path("api/", include("uc_admin.urls")),
    
    
    path("api/subscription/", include("subscription_management.urls")),
    path("api/payments/", include("payment.urls")),
    path("log/api/", include("log.urls")),
    # path("api/", include("contact.urls")),

    path("api/", include("notification_manager.urls")),
    path("api-mail/", include("mail_management.urls")), # Mail Managment App
    
    
    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
