from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, JournalEntry

# Register your custom User with Django's UserAdmin
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    pass

# Register JournalEntry normally
@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display = ("user", "created_at")
    search_fields = ("user__username", "content")
