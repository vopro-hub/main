from django.contrib import admin
from django.contrib.auth import get_user_model
from .models import UserWallet, PaystackTransaction, CreditTransaction, AIAssistantTask
User = get_user_model()

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'email',  "first_name", "last_name", "role", 'is_staff', 'is_active', 'date_joined')
    search_fields = ('username', 'email')
    list_filter = ('is_staff', 'is_active', 'date_joined')
    
@admin.register(UserWallet)
class UserWalletAdmin(admin.ModelAdmin):
    list_display = ( "user", "total_credits", "reserved_credits", "updated_at")
    search_fields = ('user',)

@admin.register(PaystackTransaction)
class PaystackTransactionAdmin(admin.ModelAdmin):
    list_display = ( "user", "reference", "amount", "credits_to_add", "verified", "created_at")
    search_fields = ('user', "verify", "reference")

@admin.register(CreditTransaction)
class CreditTransactionAdmin(admin.ModelAdmin):
    list_display = ("wallet", "amount", "type", "status", "task", "AI_staff", "meta", "created_at")
    search_fields = ('wallet', "type", "status")

@admin.register(AIAssistantTask)
class AIAssistantTaskAdmin(admin.ModelAdmin):
    list_display = ("user", "agent", "task_type", "reserved_amount", "status", "result", "failed_reason", "created_at", "updated_at")
    search_fields = ('user', "agent", "status")
