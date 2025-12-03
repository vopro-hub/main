from urllib.parse import parse_qs
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth import get_user_model
import jwt
from django.conf import settings

User = get_user_model()

@database_sync_to_async
def get_user(user_id):
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        return AnonymousUser()


class JWTAuthMiddleware:
    """
    Custom middleware that authenticates users via JWT in the query string (?token=xxx).
    """

    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        # Default: anonymous
        scope["user"] = AnonymousUser()

        # Extract token from query string
        query_string = scope.get("query_string", b"").decode()
        token = parse_qs(query_string).get("token", [None])[0]

        if token:
            try:
                # Validate the token with SimpleJWT
                UntypedToken(token)
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
                user_id = payload.get("user_id")

                if user_id is not None:
                    scope["user"] = await get_user(user_id)
            except (InvalidToken, TokenError, jwt.DecodeError):
                pass  # leave as AnonymousUser if invalid

        return await self.inner(scope, receive, send)
