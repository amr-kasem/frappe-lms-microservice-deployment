"""Mock /userprofile service for integration testing.

Returns consistent user data keyed by UUID. The primary test user
(test-user-uuid-001) matches what nginx injects as X-User-Id.

Seeded users (created by the seeder service) are also registered here so that
frappe-gateway-auth can look them up via JIT provisioning when they log in
through the gateway.

UUID conventions:
  test-user-uuid-001          → admin/student (original dev user)
  test-user-uuid-002          → instructor (original dev user)
  test-user-uuid-003          → student (original dev user)
  seeder-admin-uuid-001       → lms-admin@lms.test
  seeder-instructor-uuid-NNN  → instructorNN@lms.test
  seeder-student-uuid-NNN     → studentNN@lms.test
"""

from fastapi import FastAPI, HTTPException

app = FastAPI()

# ── Original hand-crafted test users ──────────────────────────────────────
USERS: dict[str, dict] = {
    "test-user-uuid-001": {
        "email": "testuser@example.com",
        "full_name": "Test User",
        "first_name": "Test",
        "last_name": "User",
        "roles": ["admin", "student"],
    },
    "test-user-uuid-002": {
        "email": "instructor@example.com",
        "full_name": "Test Instructor",
        "first_name": "Test",
        "last_name": "Instructor",
        "roles": ["instructor"],
    },
    "test-user-uuid-003": {
        "email": "student@example.com",
        "full_name": "Test Student",
        "first_name": "Test",
        "last_name": "Student",
        "roles": ["student"],
    },
}

# ── Seeder: admin ──────────────────────────────────────────────────────────
USERS["seeder-admin-uuid-001"] = {
    "email": "lms-admin@lms.test",
    "full_name": "Sarah Chen",
    "first_name": "Sarah",
    "last_name": "Chen",
    "roles": ["admin", "student"],
}

# ── Seeder: instructors (3) ────────────────────────────────────────────────
INSTRUCTOR_NAMES = [
    ("James", "Mitchell"),
    ("Priya", "Sharma"),
    ("Carlos", "Reyes"),
]
for _i, (_first, _last) in enumerate(INSTRUCTOR_NAMES, start=1):
    USERS[f"seeder-instructor-uuid-{_i:03d}"] = {
        "email": f"instructor{_i:02d}@lms.test",
        "full_name": f"{_first} {_last}",
        "first_name": _first,
        "last_name": _last,
        "roles": ["instructor"],
    }

# ── Seeder: students (30) ─────────────────────────────────────────────────
STUDENT_NAMES = [
    ("Alice", "Johnson"),
    ("Ben", "Okafor"),
    ("Clara", "Müller"),
    ("David", "Kim"),
    ("Elena", "Rossi"),
    ("Fatima", "Al-Rashid"),
    ("George", "Tanaka"),
    ("Hannah", "Bergström"),
    ("Ibrahim", "Diallo"),
    ("Julia", "Kowalski"),
    ("Kevin", "Nguyen"),
    ("Lily", "Patel"),
    ("Marco", "Santos"),
    ("Nadia", "Petrov"),
    ("Oscar", "Lindgren"),
    ("Paula", "Fischer"),
    ("Ravi", "Mehta"),
    ("Sofia", "Hernandez"),
    ("Thomas", "O'Brien"),
    ("Uma", "Krishnan"),
    ("Victor", "Dubois"),
    ("Wanda", "Johansson"),
    ("Xavier", "Costa"),
    ("Yuki", "Nakamura"),
    ("Zara", "Williams"),
    ("Amir", "Hassan"),
    ("Bianca", "Torres"),
    ("Chen", "Wei"),
    ("Diana", "Volkov"),
    ("Erik", "Andersen"),
]
for _i, (_first, _last) in enumerate(STUDENT_NAMES, start=1):
    USERS[f"seeder-student-uuid-{_i:03d}"] = {
        "email": f"student{_i:02d}@lms.test",
        "full_name": f"{_first} {_last}",
        "first_name": _first,
        "last_name": _last,
        "roles": ["student"],
    }


@app.get("/userprofile/{uuid}")
def get_userprofile(uuid: str):
    if uuid not in USERS:
        raise HTTPException(status_code=404, detail=f"User {uuid} not found")
    return USERS[uuid]


@app.get("/health")
def health():
    return {"status": "ok"}
