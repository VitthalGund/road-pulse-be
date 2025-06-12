from django.contrib import admin
from .models import Trip, DutyStatus, ELDLog


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ["id", "driver", "status", "start_time"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(DutyStatus)
class DutyStatusAdmin(admin.ModelAdmin):
    list_display = ["id", "trip", "status", "start_time"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(ELDLog)
class ELDLogAdmin(admin.ModelAdmin):
    list_display = ["id", "trip", "date", "total_miles"]
    readonly_fields = ["created_at", "updated_at"]
