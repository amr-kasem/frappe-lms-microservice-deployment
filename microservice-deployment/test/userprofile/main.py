"""Mock /userprofile service for integration testing.

Returns consistent user data keyed by UUID. The primary test user
(test-user-uuid-001) matches what nginx injects as X-User-Id.
"""

from fastapi import FastAPI, HTTPException

app = FastAPI()

# Mocked users — add more as needed for testing
USERS = {
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


@app.get("/userprofile/{uuid}")
def get_userprofile(uuid: str):
    if uuid not in USERS:
        raise HTTPException(status_code=404, detail=f"User {uuid} not found")
    return USERS[uuid]


@app.get("/health")
def health():
    return {"status": "ok"}
