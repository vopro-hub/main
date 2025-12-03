from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import UserWallet, CreditTransaction, AIAssistantTask

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "role"]


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
   
    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "password"]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        user = User(
            username=validated_data["username"],
             email=validated_data["email"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
        )
        validate_password(validated_data["password"], user)
        user.set_password(validated_data["password"])
        user.save()
        return user


# 🔑 Custom login serializer
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token['username'] = user.username
        token['email'] = user.email
        token['id'] = user.id

        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        # Add the serialized user to the response
        data['user'] = UserSerializer(self.user).data
        return data



class CreditTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditTransaction
        fields = [
            "id", "type", "status", "amount", "meta", "created_at",
        ]


class UserWalletSerializer(serializers.ModelSerializer):
    available = serializers.SerializerMethodField()
    transactions = CreditTransactionSerializer(many=True, read_only=True)

    class Meta:
        model = UserWallet
        fields = [
            "id", "total_credits", "reserved_credits", "available", "transactions",
        ]

    def get_available(self, obj):
        return obj.available()


class AIAssistantTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIAssistantTask
        fields = [
            "id", "task_type", "agent", "reserved_amount", "status", "result", "created_at", "updated_at",
        ]
        read_only_fields = ["status", "result", "created_at", "updated_at"]
