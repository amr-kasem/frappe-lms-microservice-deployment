"""LMS seeder — provisions users via JIT, then creates courses/batches via REST API.

User creation is intentionally delegated to the gateway-auth JIT flow:
  1. Hit any authenticated endpoint with X-User-Id → frappe-gateway-auth calls
     userprofile, creates the shadow user in Frappe, and assigns roles.
  2. Courses and batches are created via the Frappe resource API as admin.

Run with: python seed.py
Requires: requests  (pip install requests)
"""

import sys
import time

import requests

BACKEND = "http://backend:8000"
SITE_HOST = "lms.test"

ADMIN_UUID = "seeder-admin-uuid-001"
INSTRUCTOR_UUIDS = [f"seeder-instructor-uuid-{i:03d}" for i in range(1, 4)]
STUDENT_UUIDS = [f"seeder-student-uuid-{i:03d}" for i in range(1, 31)]

COURSE_TITLES = [
    "Introduction to Python",
    "Web Development Fundamentals",
    "Data Structures & Algorithms",
    "Machine Learning Basics",
    "DevOps & CI/CD",
    "Database Design",
    "Cloud Computing with AWS",
    "React for Beginners",
    "API Design with REST",
    "Cybersecurity Essentials",
]

# 5 batches, each mapped to 2 courses, 10 students per batch
# 30 students split into 5 groups of 6, then pad to 10 by borrowing from neighbors
BATCH_CONFIG = [
    {"title": "Batch 01 — Python & Web",     "courses": [0, 1], "students": list(range(0, 10))},
    {"title": "Batch 02 — Algorithms & ML",   "courses": [2, 3], "students": list(range(6, 16))},
    {"title": "Batch 03 — DevOps & Databases", "courses": [4, 5], "students": list(range(12, 22))},
    {"title": "Batch 04 — Cloud & React",     "courses": [6, 7], "students": list(range(18, 28))},
    {"title": "Batch 05 — API & Security",    "courses": [8, 9], "students": list(range(20, 30))},
]

# Use a session so headers (especially Expect suppression) persist across requests
session = requests.Session()
session.headers.update({
    "Host": SITE_HOST,
    "Content-Type": "application/json",
    "Expect": "",
})


# ── Helpers ────────────────────────────────────────────────────────────────

def call(method: str, path: str, uuid: str, **kwargs) -> requests.Response:
    """Make an HTTP request to the backend, fail with full error context."""
    r = session.request(
        method,
        f"{BACKEND}{path}",
        headers={"X-User-Id": uuid},
        timeout=30,
        **kwargs,
    )
    if not r.ok:
        print(f"  ERROR {r.status_code} {method} {path}", file=sys.stderr)
        print(f"  Response: {r.text[:500]}", file=sys.stderr)
        r.raise_for_status()
    return r


def provision_and_get_email(uuid: str) -> str:
    """Trigger JIT provisioning for uuid and return the resulting Frappe email."""
    r = call("GET", "/api/method/frappe.auth.get_logged_user", uuid)
    return r.json()["message"]


def api_insert(doctype: str, data: dict, as_uuid: str) -> dict:
    """POST to /api/resource/<doctype>. Returns the created doc dict."""
    r = call("POST", f"/api/resource/{doctype}", as_uuid, json=data)
    return r.json()["data"]


def any_exist(doctype: str, as_uuid: str) -> bool:
    """Return True if any documents of this doctype exist."""
    r = call("GET", f"/api/resource/{doctype}", as_uuid, params={"limit": 1})
    return len(r.json().get("data", [])) > 0


# ── Step 1: Wait for backend ───────────────────────────────────────────────
print("Waiting for backend...")
for _ in range(30):
    try:
        r = session.get(f"{BACKEND}/api/method/ping", timeout=5)
        if r.ok:
            break
    except requests.exceptions.ConnectionError:
        pass
    time.sleep(5)
else:
    print("Backend did not become reachable in time.", file=sys.stderr)
    sys.exit(1)
print("Backend reachable.")

# ── Step 2: Provision all users via JIT ───────────────────────────────────
print("\nProvisioning users via gateway-auth JIT...")

provision_and_get_email(ADMIN_UUID)
print("  ✓ admin provisioned")

instructor_emails = []
for uuid in INSTRUCTOR_UUIDS:
    email = provision_and_get_email(uuid)
    instructor_emails.append(email)
print(f"  ✓ {len(INSTRUCTOR_UUIDS)} instructors provisioned")

student_emails = []
for uuid in STUDENT_UUIDS:
    email = provision_and_get_email(uuid)
    student_emails.append(email)
print(f"  ✓ {len(STUDENT_UUIDS)} students provisioned")

# ── Step 3: Create courses (empty) ────────────────────────────────────────
if any_exist("LMS Course", ADMIN_UUID):
    print("\nCourses already exist, fetching names...")
    r = call("GET", "/api/resource/LMS Course", ADMIN_UUID,
             params={"limit_page_length": 50, "fields": '["name","title"]'})
    courses = [d["name"] for d in r.json()["data"]]
    print(f"  Found {len(courses)} courses")
else:
    print("\nCreating courses...")
    courses = []
    for i, title in enumerate(COURSE_TITLES):
        instructor_email = instructor_emails[i % len(instructor_emails)]
        doc = api_insert(
            "LMS Course",
            {
                "title": title,
                "short_introduction": f"A comprehensive course on {title}.",
                "description": f"<p>This course covers the fundamentals of {title}.</p>",
                "published": 1,
                "paid_course": 0,
                "instructors": [{"instructor": instructor_email}],
            },
            ADMIN_UUID,
        )
        courses.append(doc["name"])
        print(f"  ✓ {title}")

# ── Step 4: Create batches and enroll students ─────────────────────────────
if any_exist("LMS Batch", ADMIN_UUID):
    print("\nBatches already exist, skipping.")
    print("\n✓ Seeding complete!")
    sys.exit(0)

print("\nCreating batches...")
for cfg in BATCH_CONFIG:
    # Each batch is linked to its first course
    primary_course = courses[cfg["courses"][0]]
    instructor_email = instructor_emails[cfg["courses"][0] % len(instructor_emails)]

    batch = api_insert(
        "LMS Batch",
        {
            "title": cfg["title"],
            "course": primary_course,
            "start_date": "2026-03-15",
            "end_date": "2026-06-15",
            "start_time": "09:00",
            "end_time": "17:00",
            "timezone": "UTC",
            "description": f"<p>{cfg['title']}</p>",
            "batch_details": f"<p>Covers: {', '.join(COURSE_TITLES[c] for c in cfg['courses'])}.</p>",
            "medium": "Online",
            "paid_batch": 0,
            "instructors": [{"instructor": instructor_email}],
        },
        ADMIN_UUID,
    )
    batch_name = batch["name"]

    # Enroll students into each course the batch covers
    batch_students = [student_emails[i % 30] for i in cfg["students"]]
    for course_idx in cfg["courses"]:
        course_name = courses[course_idx]
        for email in batch_students:
            api_insert(
                "LMS Enrollment",
                {
                    "batch": batch_name,
                    "course": course_name,
                    "member": email,
                    "member_type": "Student",
                },
                ADMIN_UUID,
            )

    student_names_preview = ", ".join(batch_students[:3]) + "..."
    course_names = ", ".join(COURSE_TITLES[c] for c in cfg["courses"])
    print(f"  ✓ {cfg['title']} → [{course_names}] + {len(batch_students)} students ({student_names_preview})")

print("\n✓ Seeding complete!")
