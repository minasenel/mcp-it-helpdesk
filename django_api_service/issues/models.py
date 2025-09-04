from django.db import models


class Issue(models.Model):
    issue_id = models.CharField(max_length=16, unique=True, blank=True)
    employee_id = models.CharField(max_length=64, blank=True, default="")
    description = models.TextField()
    category = models.CharField(max_length=32)
    subcategory = models.CharField(max_length=32)
    priority = models.CharField(max_length=16, default="low")
    status = models.CharField(max_length=16, default="open")
    assigned_expert_id = models.CharField(max_length=64, blank=True, default="")
    ai_solution = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.issue_id or f"Issue-{self.pk}"
