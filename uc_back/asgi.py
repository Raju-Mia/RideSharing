import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter

django_asgi_app = get_asgi_application()


import accounts.routing as accounts_router
# import chat.routing as chat_router
import trip_management.routing as trip_management
from .custom_auth_middleware import TokenMiddleware
# , TokenAuthMiddlewareStack

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "uc_back.settings")


application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": TokenMiddleware(
            URLRouter(
                accounts_router.websocket_urlpatterns
                # + chat_router.websocket_urlpatterns
                + trip_management.websocket_urlpatterns
            )
        ),
    }
)
