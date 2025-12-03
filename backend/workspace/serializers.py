from rest_framework import serializers
from .models import (
    Office, 
    Room, 
    Membership, 
    Presence, 
    OfficeCity, 
    Worker, 
    WorkerPresence,
    VisitorAccessSubmission
    )
from django.contrib.auth import get_user_model

User = get_user_model()

class RoomSerializer(serializers.ModelSerializer):
    class Meta: 
        model = Room; 
        fields = ["id", "name", "office", "x", "y", "width", "height", "config", "access_policy", "access_config"]

class WorkerSerializer(serializers.ModelSerializer):
    rooms = serializers.PrimaryKeyRelatedField(
        many=True, 
        queryset=Room.objects.all(),
    )

    class Meta:
        model = Worker
        fields = ["id", "worker_id", "name", "office", "rooms"]
        read_only_fields = [ "worker_id", "created_by"]

    def create(self, validated_data):
        rooms = validated_data.pop("rooms", [])
        worker = Worker.objects.create(
            created_by=self.context["request"].user, **validated_data
        )
        worker.rooms.set(rooms)
        return worker

    def update(self, instance, validated_data):
        try:
            validated_data.pop("office", None)
            validated_data.pop("created_by", None)
            rooms = validated_data.pop("rooms", None)
    
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
    
            if rooms is not None:
                instance.rooms.set(rooms)
    
            return instance
        except Exception as e:
            print("Update error:", e)
            raise

class WorkerPresenceSerializer(serializers.ModelSerializer):
    worker = WorkerSerializer(read_only=True)

    class Meta:
        model = WorkerPresence
        fields = ["id", "worker", "is_presence", "last_login_time", "last_logout_at"]



class VisitorAccessSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = VisitorAccessSubmission
        fields = ["id", "room", "visitor_id", "data", "name", "email", "phone", "approved", "revoked", "created_at"]
        read_only_fields = ["id", "created_at", "name", "email", "phone"]

class OfficeSerializer(serializers.ModelSerializer):
    rooms = RoomSerializer(many=True, read_only=True, source="room_set")
    preview_url = serializers.SerializerMethodField()
    workers = WorkerSerializer(many=True, read_only=True)
    visitor_access = VisitorAccessSubmissionSerializer(read_only=True)
    visitorRooms = serializers.SerializerMethodField()  # 👈 new

    class Meta:
        model = Office
        fields = [
            "id", "name", "city", "owner", "public",
            "public_slug", "services", "coordinates",
            "created_at", "preview_url",
            "rooms", "workers", "visitor_access", "visitorRooms"  # 👈 new
        ]
        read_only_fields = ["public_slug", "preview_url", "owner", "created_at"]

    def get_preview_url(self, obj):
        if obj.public_slug:
            return f"/public/offices/{obj.public_slug}/"
        return None

    def get_visitorRooms(self, obj):
        visitor_access = getattr(obj, "visitor_access", None)
        if visitor_access:
            return list(visitor_access.rooms.values_list("id", flat=True))
        return []


class MembershipSerializer(serializers.ModelSerializer):
    class Meta: model = Membership; fields = ["id","user","office","role","joined_at"]; read_only_fields = ["joined_at"]

class PresenceSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    class Meta: model = Presence; fields = ["id","office","user","status","updated_at"]; read_only_fields = ["updated_at","user"]



class CitySerializer(serializers.ModelSerializer):
    offices_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = OfficeCity
        fields = ["id", "country", "city", "slug", "lat", "lng", "offices_count"]
        
        def get_offices_count(self, obj):
           return obj.offices.filter(public=True).count()
       
       
class PublicOfficeSerializer(serializers.ModelSerializer):
    rooms = RoomSerializer(many=True,  read_only=True)
    city = serializers.StringRelatedField()

    class Meta:
        model = Office
        fields = ("id", "name", "city", "public_slug", "services", "coordinates", "rooms")


