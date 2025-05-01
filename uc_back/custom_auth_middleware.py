from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from jwt import decode as jwt_decode
from django.conf import settings
from django.contrib.auth import get_user_model
from urllib.parse import parse_qs
import jwt
User = get_user_model()


@database_sync_to_async
def get_user(token):
    try:
        decoded_data = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return AnonymousUser()
    except jwt.InvalidTokenError:
        return AnonymousUser()
    
    token_type = decoded_data.get("token_type")
    if token_type != "websocket":
        return AnonymousUser()
    
    try:
        user_id = decoded_data["user_id"]
        user = User.objects.get(id=user_id)
        return user
    except User.DoesNotExist:
        return AnonymousUser()

class TokenMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        query_params = parse_qs(scope.get("query_string", b"").decode("utf8"))
        token = query_params.get("token", [None])[0]
        
        if token:
            scope["user"] = await get_user(token)
        else:
            scope["user"] = AnonymousUser()
        
        return await self.app(scope, receive, send)

# class TokenMiddleware:
#     def __init__(self, app):
#         self.app = app

#     async def __call__(self, scope, receive, send):
#         try:
#             token = parse_qs(scope["query_string"].decode("utf8"))["token"][0]
#             scope["user"] = await get_user(token)
#         except KeyError:
#             scope["user"] = AnonymousUser()
#             print("anonymous user keyerror $$$$$$$$$$")
#         except Exception:
#             scope["user"] = AnonymousUser()
#             print("anonymous user Exception #############")


#         return await self.app(scope, receive, send)