from base64 import urlsafe_b64decode, urlsafe_b64encode
from datetime import datetime, timedelta, timezone
from hashlib import pbkdf2_hmac
from hmac import compare_digest, new as hmac_new
from http.server import BaseHTTPRequestHandler, HTTPServer
from json import JSONDecodeError, dumps, loads
from pathlib import Path
from secrets import token_hex
from time import time
from urllib.parse import urlparse


BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
DATA_DIR = BASE_DIR / "data"
USERS_FILE = DATA_DIR / "users.json"
STUDENTS_FILE = DATA_DIR / "students.json"
HOST = "127.0.0.1"
PORT = 8000
JWT_SECRET = "change-this-secret-for-production"
PASS_MARK = 40


def ensure_data_files():
    DATA_DIR.mkdir(exist_ok=True)
    if not USERS_FILE.exists():
        write_json(USERS_FILE, [])
    if not STUDENTS_FILE.exists():
        write_json(
            STUDENTS_FILE,
            [
                {
                    "id": 1,
                    "name": "Aarav Sharma",
                    "rollNo": "STU001",
                    "className": "10-A",
                    "marks": 92,
                    "attendance": 96,
                    "joinedMonth": "2026-01",
                },
                {
                    "id": 2,
                    "name": "Isha Verma",
                    "rollNo": "STU002",
                    "className": "10-A",
                    "marks": 87,
                    "attendance": 91,
                    "joinedMonth": "2026-01",
                },
                {
                    "id": 3,
                    "name": "Kabir Khan",
                    "rollNo": "STU003",
                    "className": "10-B",
                    "marks": 76,
                    "attendance": 88,
                    "joinedMonth": "2026-02",
                },
                {
                    "id": 4,
                    "name": "Meera Nair",
                    "rollNo": "STU004",
                    "className": "10-C",
                    "marks": 95,
                    "attendance": 98,
                    "joinedMonth": "2026-03",
                },
                {
                    "id": 5,
                    "name": "Rohan Das",
                    "rollNo": "STU005",
                    "className": "10-B",
                    "marks": 39,
                    "attendance": 74,
                    "joinedMonth": "2026-03",
                },
                {
                    "id": 6,
                    "name": "Ananya Rao",
                    "rollNo": "STU006",
                    "className": "10-C",
                    "marks": 68,
                    "attendance": 82,
                    "joinedMonth": "2026-04",
                },
            ],
        )


def read_json(path):
    try:
        return loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, JSONDecodeError):
        return []


def write_json(path, data):
    path.write_text(dumps(data, indent=2), encoding="utf-8")


def b64_encode(raw_bytes):
    return urlsafe_b64encode(raw_bytes).rstrip(b"=").decode("utf-8")


def b64_decode(text):
    padding = "=" * (-len(text) % 4)
    return urlsafe_b64decode((text + padding).encode("utf-8"))


def hash_password(password, salt=None):
    salt = salt or token_hex(16)
    digest = pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120000)
    return f"{salt}${digest.hex()}"


def verify_password(password, stored_hash):
    try:
        salt, expected = stored_hash.split("$", 1)
    except ValueError:
        return False
    return compare_digest(hash_password(password, salt), f"{salt}${expected}")


def create_token(user):
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": user["id"],
        "name": user["name"],
        "email": user["email"],
        "exp": int((datetime.now(timezone.utc) + timedelta(hours=8)).timestamp()),
    }
    unsigned = ".".join(
        [
            b64_encode(dumps(header, separators=(",", ":")).encode("utf-8")),
            b64_encode(dumps(payload, separators=(",", ":")).encode("utf-8")),
        ]
    )
    signature = hmac_new(JWT_SECRET.encode("utf-8"), unsigned.encode("utf-8"), "sha256").digest()
    return f"{unsigned}.{b64_encode(signature)}"


def verify_token(token):
    try:
        header_part, payload_part, signature_part = token.split(".")
        unsigned = f"{header_part}.{payload_part}"
        expected_signature = hmac_new(
            JWT_SECRET.encode("utf-8"), unsigned.encode("utf-8"), "sha256"
        ).digest()
        if not compare_digest(b64_encode(expected_signature), signature_part):
            return None
        payload = loads(b64_decode(payload_part).decode("utf-8"))
        if payload.get("exp", 0) < time():
            return None
        return payload
    except Exception:
        return None


def public_user(user):
    return {"id": user["id"], "name": user["name"], "email": user["email"]}


def next_id(items):
    return max([item.get("id", 0) for item in items], default=0) + 1


def as_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def clean_student(payload, existing_id=None):
    name = str(payload.get("name", "")).strip()
    roll_no = str(payload.get("rollNo", "")).strip().upper()
    class_name = str(payload.get("className", "")).strip().upper()
    marks = max(0, min(100, as_int(payload.get("marks"))))
    attendance = max(0, min(100, as_int(payload.get("attendance"))))
    joined_month = str(payload.get("joinedMonth", "")).strip()

    if not name or not roll_no or not class_name:
        raise ValueError("Name, roll number, and class are required.")

    if not joined_month:
        joined_month = datetime.now().strftime("%Y-%m")

    student = {
        "name": name,
        "rollNo": roll_no,
        "className": class_name,
        "marks": marks,
        "attendance": attendance,
        "joinedMonth": joined_month,
    }
    if existing_id is not None:
        student["id"] = existing_id
    return student


def group_average(students, key):
    grouped = {}
    for student in students:
        label = student[key]
        grouped.setdefault(label, []).append(student["marks"])
    return [
        {"label": label, "value": round(sum(values) / len(values), 1)}
        for label, values in sorted(grouped.items())
    ]


def monthly_students(students):
    grouped = {}
    for student in students:
        month = student.get("joinedMonth") or "Unknown"
        grouped[month] = grouped.get(month, 0) + 1
    return [{"label": label, "value": value} for label, value in sorted(grouped.items())]


def build_dashboard():
    students = read_json(STUDENTS_FILE)
    total = len(students)
    average_marks = round(sum(student["marks"] for student in students) / total, 1) if total else 0
    passed = len([student for student in students if student["marks"] >= PASS_MARK])
    pass_percentage = round((passed / total) * 100, 1) if total else 0
    top_students = sorted(students, key=lambda student: student["marks"], reverse=True)[:5]
    top_performer = top_students[0]["name"] if top_students else "No students"

    return {
        "summary": {
            "totalStudents": total,
            "averageMarks": average_marks,
            "passPercentage": pass_percentage,
            "topPerformer": top_performer,
        },
        "charts": {
            "averageMarksByClass": group_average(students, "className"),
            "passFail": [
                {"label": "Pass", "value": passed},
                {"label": "Fail", "value": total - passed},
            ],
            "monthlyAdmissions": monthly_students(students),
        },
        "topPerformers": top_students,
        "students": sorted(students, key=lambda student: student["id"], reverse=True),
    }


def content_type_for(path):
    suffix = path.suffix.lower()
    return {
        ".html": "text/html; charset=utf-8",
        ".css": "text/css; charset=utf-8",
        ".js": "text/javascript; charset=utf-8",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".svg": "image/svg+xml",
    }.get(suffix, "application/octet-stream")


def send_json(handler, payload, status=200):
    body = dumps(payload).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def send_file(handler, path):
    if not path.exists() or not path.is_file():
        send_json(handler, {"error": "File not found."}, 404)
        return
    body = path.read_bytes()
    handler.send_response(200)
    handler.send_header("Content-Type", content_type_for(path))
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


class StudentAnalyticsHandler(BaseHTTPRequestHandler):
    def read_body(self):
        content_length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(content_length).decode("utf-8")
        return loads(raw_body) if raw_body else {}

    def current_user(self):
        auth_header = self.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return None
        payload = verify_token(auth_header.replace("Bearer ", "", 1))
        if not payload:
            return None
        users = read_json(USERS_FILE)
        return next((user for user in users if user["id"] == payload["sub"]), None)

    def require_user(self):
        user = self.current_user()
        if not user:
            send_json(self, {"error": "Login required or token expired."}, 401)
            return None
        return user

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path in {"/", "/index.html"}:
            send_file(self, FRONTEND_DIR / "index.html")
            return
        if path in {"/styles.css", "/app.js"}:
            send_file(self, FRONTEND_DIR / path.lstrip("/"))
            return

        if path == "/api/me":
            user = self.require_user()
            if user:
                send_json(self, {"user": public_user(user)})
            return

        if path == "/api/dashboard":
            if self.require_user():
                send_json(self, build_dashboard())
            return

        if path == "/api/students":
            if self.require_user():
                send_json(self, {"students": read_json(STUDENTS_FILE)})
            return

        send_json(self, {"error": "Route not found."}, 404)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        try:
            payload = self.read_body()
        except JSONDecodeError:
            send_json(self, {"error": "Invalid JSON body."}, 400)
            return

        if path == "/api/auth/register":
            users = read_json(USERS_FILE)
            name = str(payload.get("name", "")).strip()
            email = str(payload.get("email", "")).strip().lower()
            password = str(payload.get("password", ""))

            if not name or not email or len(password) < 6:
                send_json(self, {"error": "Name, email, and 6 character password are required."}, 400)
                return
            if any(user["email"] == email for user in users):
                send_json(self, {"error": "Email already registered. Please login."}, 409)
                return

            user = {
                "id": next_id(users),
                "name": name,
                "email": email,
                "passwordHash": hash_password(password),
            }
            users.append(user)
            write_json(USERS_FILE, users)
            send_json(self, {"token": create_token(user), "user": public_user(user)}, 201)
            return

        if path == "/api/auth/login":
            email = str(payload.get("email", "")).strip().lower()
            password = str(payload.get("password", ""))
            users = read_json(USERS_FILE)
            user = next((item for item in users if item["email"] == email), None)

            if not user or not verify_password(password, user["passwordHash"]):
                send_json(self, {"error": "Invalid email or password."}, 401)
                return
            send_json(self, {"token": create_token(user), "user": public_user(user)})
            return

        if path == "/api/students":
            if not self.require_user():
                return
            students = read_json(STUDENTS_FILE)
            try:
                student = clean_student(payload)
            except ValueError as error:
                send_json(self, {"error": str(error)}, 400)
                return
            if any(item["rollNo"] == student["rollNo"] for item in students):
                send_json(self, {"error": "Roll number already exists."}, 409)
                return
            student["id"] = next_id(students)
            students.append(student)
            write_json(STUDENTS_FILE, students)
            send_json(self, {"student": student, "dashboard": build_dashboard()}, 201)
            return

        send_json(self, {"error": "Route not found."}, 404)

    def do_PUT(self):
        parsed = urlparse(self.path)
        path_parts = parsed.path.strip("/").split("/")

        if len(path_parts) != 3 or path_parts[:2] != ["api", "students"]:
            send_json(self, {"error": "Route not found."}, 404)
            return
        if not self.require_user():
            return

        try:
            student_id = int(path_parts[2])
            payload = self.read_body()
        except (ValueError, JSONDecodeError):
            send_json(self, {"error": "Invalid request."}, 400)
            return

        students = read_json(STUDENTS_FILE)
        index = next((idx for idx, item in enumerate(students) if item["id"] == student_id), None)
        if index is None:
            send_json(self, {"error": "Student not found."}, 404)
            return

        try:
            updated = clean_student(payload, existing_id=student_id)
        except ValueError as error:
            send_json(self, {"error": str(error)}, 400)
            return

        if any(item["id"] != student_id and item["rollNo"] == updated["rollNo"] for item in students):
            send_json(self, {"error": "Roll number already exists."}, 409)
            return

        students[index] = updated
        write_json(STUDENTS_FILE, students)
        send_json(self, {"student": updated, "dashboard": build_dashboard()})

    def do_DELETE(self):
        parsed = urlparse(self.path)
        path_parts = parsed.path.strip("/").split("/")

        if len(path_parts) != 3 or path_parts[:2] != ["api", "students"]:
            send_json(self, {"error": "Route not found."}, 404)
            return
        if not self.require_user():
            return

        try:
            student_id = int(path_parts[2])
        except ValueError:
            send_json(self, {"error": "Invalid student id."}, 400)
            return

        students = read_json(STUDENTS_FILE)
        remaining = [student for student in students if student["id"] != student_id]
        if len(remaining) == len(students):
            send_json(self, {"error": "Student not found."}, 404)
            return

        write_json(STUDENTS_FILE, remaining)
        send_json(self, {"message": "Student deleted.", "dashboard": build_dashboard()})

    def log_message(self, format, *args):
        return


if __name__ == "__main__":
    ensure_data_files()
    server = HTTPServer((HOST, PORT), StudentAnalyticsHandler)
    print(f"Student analytics app running at http://{HOST}:{PORT}")
    server.serve_forever()
