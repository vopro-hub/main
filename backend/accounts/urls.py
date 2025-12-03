from django.urls import path
from rest_framework_simplejwt.views import  TokenRefreshView

from .views import (
    RegisterView, 
    MeView, 
    MyTokenObtainPairView,
    WalletDetailView,
    PurchaseCreditsView,
    VerifyPaymentView,
    TransactionHistoryView,
)
urlpatterns = [
  path("accounts/register/", RegisterView.as_view(), name="register"),
  path("accounts/login/", MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
  path("token/refresh/", TokenRefreshView.as_view()),
  path("accounts/me/", MeView.as_view(), name="me"),
  path("wallet/", WalletDetailView.as_view(), name="wallet-detail"),
  path("wallet/purchase/", PurchaseCreditsView.as_view(), name="wallet-purchase"),
  path("wallet/verify/", VerifyPaymentView.as_view(), name="paystack_verify"),
  #path("wallet/tasks/<uuid:task_id>/result/", AIAssistantTaskResultView.as_view(), name="task-result"),
  path("wallet/logs/", TransactionHistoryView.as_view(), name="wallet-transactions"),
]
