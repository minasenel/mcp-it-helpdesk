from django.contrib import admin
from .models import Issue, Expert


@admin.register(Expert)
class ExpertAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "availability", "current_load")
    search_fields = ("id", "name")
    list_filter = ("availability",)


@admin.register(Issue)
class IssueAdmin(admin.ModelAdmin):
    list_display = ("issue_id", "employee_id", "category", "subcategory", "priority", "status", "assigned_expert_id", "created_at")
    search_fields = ("issue_id", "employee_id", "description")
    list_filter = ("status", "priority", "category")
