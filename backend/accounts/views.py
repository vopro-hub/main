from rest_framework.response import Response
from rest_framework import status, generics, permissions
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.views import TokenObtainPairView
from decimal import Decimal
from django.conf import settings
from django.db import transaction
import requests
from rest_framework.views import APIView
from .models import UserWallet, AIAssistantTask, CreditTransaction, InsufficientCredits, PaystackTransaction
from .serializers import (
    RegisterSerializer, 
    UserSerializer, 
    MyTokenObtainPairSerializer,
    UserWalletSerializer,
    CreditTransactionSerializer,
    AIAssistantTaskSerializer,
)
from workspace.models import Office, Membership, Room, OfficeCity, cityLobby

User = get_user_model()

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        username = request.data.get("username", "").strip()
        office_name = request.data.get("office_name", "").strip()
        
        # ---- USERNAME EXISTS CHECK ----
        if User.objects.filter(username=username).exists():
            return Response(
                {"error": "Username is already taken"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 1. Create the user first
        response = super().create(request, *args, **kwargs)
        user = User.objects.get(username=request.data["username"])

        # 2. Get city from request
        city_id = request.data.get("city")
        if not city_id:
            return Response({"error": "City is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            city = OfficeCity.objects.get(id=city_id)
        except OfficeCity.DoesNotExist:
            return Response({"error": "Invalid city_id"}, status=status.HTTP_400_BAD_REQUEST)

        cityLobby.objects.get_or_create(user=user, city=city)

        # ---------------------------
        # USER'S PRIVATE OFFICE
        # ---------------------------
        office = Office.objects.create(
            city=city,
            owner=user,
            name=office_name,
        )

        # Private office default rooms
        Room.objects.create(office=office, name="Office Lobby")
        #Room.objects.create(office=office, name="Meeting Room")

        # User is always OWNER of their private office
        Membership.objects.create(user=user, office=office, role="OWNER")

        return Response(
            {"message": "User created successfully"},
            status=status.HTTP_201_CREATED
        )


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


class MeView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    def get_object(self): 
        return self.request.user

class WalletDetailView(generics.RetrieveAPIView):
    """Get current user's wallet + recent transactions"""
    serializer_class = UserWalletSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        wallet, _ = UserWallet.objects.get_or_create(user=self.request.user)
        return wallet


  
class PurchaseCreditsView(APIView):
    """Prepay credits (e.g., buy 100 = $10)."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        amount = int(request.data.get("amount", 0))
        if amount <= 0:
            return Response({"detail": "Invalid amount"}, status=400)
        
        credits_to_add = amount * 10  # example: $1 = 10 credits
        
        purchase, _ = PaystackTransaction.objects.get_or_create(
            user=request.user,
            amount = amount,
            credits_to_add = credits_to_add,
        )
        purchase.save()
        
        return Response({"credits_added": credits_to_add, "reference": purchase.reference})

class VerifyPaymentView(APIView):
    """Verify Paystack transaction and credit user's wallet."""
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        reference = request.data.get("reference")
        if not reference:
            return Response({"detail": "Missing transaction reference"}, status=400)

        # Fetch the transaction
        try:
            pay_tx = PaystackTransaction.objects.get(reference=reference)
        except PaystackTransaction.DoesNotExist:
            return Response({"error": "Transaction not found"}, status=status.HTTP_404_NOT_FOUND)

        if pay_tx.verified:
            return Response({"detail": "Transaction already verified."}, status=200)

        # Verify with Paystack API
        headers = {"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"}
        url = f"https://api.paystack.co/transaction/verify/{reference}"
        r = requests.get(url, headers=headers)
        res_data = r.json()

        if not res_data.get("status"):
            return Response({"error": "Verification failed"}, status=400)

        data = res_data.get("data", {})
        if data.get("status") != "success":
            return Response({"error": "Transaction not successful"}, status=400)

        user = pay_tx.user
        credits_to_add = pay_tx.credits_to_add

        # Credit the wallet
        wallet, _ = UserWallet.objects.get_or_create(user=user)
        old_balance = wallet.total_credits
        new_balance = old_balance + credits_to_add
        
        wallet.total_credits = new_balance
        wallet.save()

        # Log the transaction
        CreditTransaction.objects.create(
            wallet=wallet,
            amount=credits_to_add,
            type="purchase",
            status="confirmed",
            meta={
                "reference": reference,
                "old_balance": str(old_balance),
                "new_balance": str(new_balance)
            },
        )

        # Mark as verified
        pay_tx.verified = True
        pay_tx.save(update_fields=["verified"])

        return Response({
            "status": "success",
            "credits_added": float(credits_to_add),
            "new_balance": float(wallet.total_credits),
        }, status=200)


#class AIAssistantTaskResultView(generics.RetrieveAPIView):
#    serializer_class = AIAssistantTaskSerializer
#    permission_classes = [permissions.IsAuthenticated]
#
#    def get_object(self):
#        AIAssistantTasks = AIAssistantTask.objects.get(user=self.request.user)
#        return AIAssistantTasks

    


class TransactionHistoryView(generics.ListAPIView):
    """List all credit transactions for user."""
    serializer_class = CreditTransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        logs = CreditTransaction.objects.filter(wallet__user=self.request.user).order_by("-created_at")[:1]
        return logs



