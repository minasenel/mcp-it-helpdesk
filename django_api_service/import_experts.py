#!/usr/bin/env python3
import os
import sys
import json


def main():
    here = os.path.dirname(__file__)
    repo_root = os.path.abspath(os.path.join(here, os.pardir))

    # Ensure Django settings and path
    if here not in sys.path:
        sys.path.insert(0, here)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "api.settings")

    import django  # type: ignore
    django.setup()

    from issues.models import Expert  # type: ignore

    # Default JSON path at repo root
    json_path = os.path.join(repo_root, "tech_experts.json")
    if not os.path.exists(json_path):
        print(f"No tech_experts.json found at {json_path}. Nothing to import.")
        return

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    imported = 0
    for e in data:
        Expert.objects.update_or_create(
            id=e.get("id"),
            defaults={
                "name": e.get("name", ""),
                "expertise": e.get("expertise", []),
                "contact": e.get("contact", ""),
                "availability": bool(e.get("availability", True)),
                "current_load": int(e.get("current_load", 0)),
            },
        )
        imported += 1

    print(f"Imported/updated {imported} experts from tech_experts.json into Django DB.")


if __name__ == "__main__":
    main()


