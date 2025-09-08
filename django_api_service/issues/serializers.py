from rest_framework import serializers
from .models import Issue, Expert
import google.generativeai as genai
import os
from django.conf import settings


class IssueSerializer(serializers.ModelSerializer): # serializer for the Issue model #
    class Meta:
        model = Issue
        fields = "__all__"
        read_only_fields = ("issue_id", "created_at", "updated_at")
        extra_kwargs = {
            "category": {"required": False, "allow_blank": True},
            "subcategory": {"required": False, "allow_blank": True},
            "priority": {"required": False, "allow_blank": True},
            "status": {"required": False, "allow_blank": True},
            "assigned_expert_id": {"required": False, "allow_blank": True},
            "ai_solution": {"required": False, "allow_blank": True},
            "employee_id": {"required": False, "allow_blank": True},
        }

    # Allowed enums to keep data clean
    ALLOWED_CATEGORIES = {
        "hardware",
        "software", 
        "network",
        "access",
        "printing",
        "peripheral",
        "mobile",
        "security",
        "storage",
    }

    ALLOWED_PRIORITIES = {"low", "medium", "high", "urgent"}
    ALLOWED_STATUSES = {"open", "in_progress", "resolved", "closed"}

    # Centralized model name for Gemini
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

    @staticmethod
    def _local_it_check(description: str) -> bool:
        d = description.lower()
        pos = [
            "computer", "pc", "laptop", "mac", "windows", "linux", "software", "program",
            "login", "password", "account", "vpn", "email", "outlook",
            "network", "internet", "wifi", "ethernet", "router", "dns",
            "printer", "keyboard", "mouse", "monitor", "screen", "battery", "charger",
            "iphone", "android", "tablet", "mobile",
            "bilgisayar", "ekran", "klavye", "fare", "yazıcı", "ağ", "şifre",
        ]
        neg = [
            "musluk", "lavabo", "plumbing", "sink", "araba", "car", "bike", "bicycle", "sofa", "garden",
        ]
        if any(n in d for n in neg):
            return False
        return any(p in d for p in pos)

    @staticmethod
    def _local_infer_category(description: str) -> str:
        d = description.lower()
        if any(k in d for k in ["vpn", "network", "wifi", "ethernet", "router", "dns"]):
            return "network"
        if any(k in d for k in ["login", "password", "şifre", "account", "access"]):
            return "access"
        if any(k in d for k in ["outlook", "software", "program", "install", "update", "app"]):
            return "software"
        if any(k in d for k in ["printer", "print"]):
            return "printing"
        if any(k in d for k in ["webcam", "camera", "microphone", "speaker", "headset", "dock", "hub"]):
            return "peripheral"
        if any(k in d for k in ["iphone", "android", "tablet", "mobile", "ipad"]):
            return "mobile"
        if any(k in d for k in ["antivirus", "certificate", "bitlocker", "encryption"]):
            return "security"
        if any(k in d for k in ["ssd", "hdd", "disk", "storage"]):
            return "storage"
        return "hardware"

    @staticmethod
    def classify_with_gemini(description):
        """Use Gemini AI to classify if the description is an IT-related issue.
        Returns a tuple: (status, detail)
        status in {"VALID_IT_ISSUE", "NOT_IT_ISSUE", "INSUFFICIENT_DETAIL", "AI_UNAVAILABLE"}
        detail is a short string for logging/explanation.
        """
        try:
            # Configure Gemini API (accept either env var name)
            api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
            if not api_key:
                return "AI_UNAVAILABLE", "Missing API key"
            
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(IssueSerializer.GEMINI_MODEL)
            
            # Create classification prompt
            prompt = f"""
            Analyze this user message and determine if it describes an IT/computer/device-related technical issue that should be logged in an IT support system.

            Message: "{description}"

            Consider it a valid IT issue if it involves:
            - Computer hardware problems (laptop, desktop, keyboard, mouse, monitor, etc.)
            - Software issues (applications, operating systems, updates, installations)
            - Network connectivity problems (WiFi, VPN, internet, email)
            - Access/authentication issues (login, passwords, accounts)
            - Peripheral devices (printers, scanners, webcams, etc.)
            - Mobile devices (phones, tablets)
            - Security concerns (antivirus, encryption, certificates)

            Do NOT consider it an IT issue if it involves:
            - Household problems (plumbing, appliances, furniture)
            - Vehicle issues (cars, bikes, motorcycles)
            - General greetings or small talk
            - Non-technical, personal problems
            - Facility maintenance (doors, windows, painting)

            Respond with ONLY one of these exact responses:
            - "VALID_IT_ISSUE"
            - "NOT_IT_ISSUE"
            - "INSUFFICIENT_DETAIL"

            Response:"""
            
            response = model.generate_content(prompt)
            result = (response.text or "").strip().upper()
            if result in {"VALID_IT_ISSUE", "NOT_IT_ISSUE", "INSUFFICIENT_DETAIL"}:
                return result, "ok"
            return "AI_UNAVAILABLE", f"Unexpected model response: {result!r}"
            
        except Exception as e:
            msg = str(e)
            if "429" in msg or "quota" in msg.lower():
                return "AI_UNAVAILABLE", "rate_limited"
            return "AI_UNAVAILABLE", msg

    @staticmethod
    def categorize_with_gemini(description):
        """Use Gemini AI to categorize the IT issue"""
        try:
            api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
            if not api_key:
                return IssueSerializer._local_infer_category(description)
            
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(IssueSerializer.GEMINI_MODEL)
            
            prompt = f"""
            Categorize this IT issue description into one of these categories:

            Categories: hardware, software, network, access, printing, peripheral, mobile, security, storage

            Issue description: "{description}"

            Respond with ONLY the category name (lowercase, one word).

            Response:"""
            
            response = model.generate_content(prompt)
            category = (response.text or "").strip().lower()
            if category in IssueSerializer.ALLOWED_CATEGORIES:
                return category
            else:
                return IssueSerializer._local_infer_category(description)
                
        except Exception:
            return IssueSerializer._local_infer_category(description)

    def validate(self, attrs):
        description = attrs.get("description", "").strip()
        
        # Basic validation - require some content (relaxed to allow short valid phrases)
        if len(description) < 10 or len(description.split()) < 2:
            raise serializers.ValidationError({
                "description": "Please provide more detail about the IT/device issue (at least 2 words).",
            })

        # Try AI classification first
        status, detail = self.classify_with_gemini(description)

        if status == "AI_UNAVAILABLE":
            # Fallback to local heuristic
            if not self._local_it_check(description):
                raise serializers.ValidationError({
                    "description": "Please describe a computer/device/network issue.",
                })
            # Accept and infer locally
            if not (attrs.get("category") or "").strip():
                attrs["category"] = self._local_infer_category(description)
        elif status == "INSUFFICIENT_DETAIL":
            raise serializers.ValidationError({
                "description": "Please provide a bit more detail so we can understand the IT issue.",
            })
        elif status == "NOT_IT_ISSUE":
            raise serializers.ValidationError({
                "description": "This doesn't appear to be an IT/computer/device-related issue.",
            })
        else:
            # VALID_IT_ISSUE → use AI category if not provided
            if not (attrs.get("category") or "").strip():
                attrs["category"] = self.categorize_with_gemini(description)

        # Optionally infer a simple subcategory if missing
        subcategory = (attrs.get("subcategory") or "").strip().lower()
        if not subcategory and attrs.get("category") == "printing":
            attrs["subcategory"] = "printer"

        # Validate provided enums
        category = (attrs.get("category") or "").strip().lower()
        if category and category not in self.ALLOWED_CATEGORIES:
            raise serializers.ValidationError({
                "category": f"Invalid category. Allowed: {sorted(self.ALLOWED_CATEGORIES)}",
            })

        priority = (attrs.get("priority") or "").strip().lower()
        if priority and priority not in self.ALLOWED_PRIORITIES:
            raise serializers.ValidationError({
                "priority": f"Invalid priority. Allowed: {sorted(self.ALLOWED_PRIORITIES)}",
            })

        status_val = (attrs.get("status") or "").strip().lower()
        if status_val and status_val not in self.ALLOWED_STATUSES:
            raise serializers.ValidationError({
                "status": f"Invalid status. Allowed: {sorted(self.ALLOWED_STATUSES)}",
            })

        return attrs


class ExpertSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expert
        fields = "__all__"

