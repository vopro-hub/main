from urllib.parse import parse_qs
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.authentication import JWTAuthentication

class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        query = parse_qs(scope.get("query_string", b"").decode())
        token = (query.get("token") or [None])[0]
        scope["user"] = AnonymousUser()
        if token:
            try:
                UntypedToken(token)
                validated = JWTAuthentication().get_validated_token(token)
                user = JWTAuthentication().get_user(validated)
                scope["user"] = user
            except Exception:
                pass
        return await super().__call__(scope, receive, send)
