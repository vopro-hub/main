from rest_framework_simplejwt.authentication import JWTAuthentication

class CookieJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        access = request.COOKIES.get("access")
        if not access:
            return None

        # inject cookie into header for SimpleJWT to process
        request.META["HTTP_AUTHORIZATION"] = f"Bearer {access}"
        return super().authenticate(request)
