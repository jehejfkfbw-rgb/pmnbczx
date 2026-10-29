import os, sqlite3, hashlib, hmac, secrets, time
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

load_dotenv()
ROOT = Path(__file__).parent
DB_PATH = os.getenv("DATABASE_PATH", str(ROOT / "nova.db"))
APP_SECRET = os.getenv("APP_SECRET", "")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "nova-admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

if len(APP_SECRET) < 32:
    raise RuntimeError("APP_SECRET must be at least 32 characters. Set it in .env.")
if len(ADMIN_PASSWORD) < 14 or ADMIN_PASSWORD == "ChangeThisToALongUniquePassword!":
    raise RuntimeError("Set a unique ADMIN_PASSWORD of at least 14 characters in .env.")

app = FastAPI(title="Nova Digital OS")
app.add_middleware(
    SessionMiddleware, secret_key=APP_SECRET, session_cookie="nova_session",
    same_site="lax", https_only=os.getenv("COOKIE_HTTPS_ONLY", "false").lower() == "true",
    max_age=60 * 60 * 8
)
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")
templates = Jinja2Templates(directory=ROOT / "templates")

def hash_password(password: str, salt: Optional[bytes] = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 310_000)
    return salt.hex() + "$" + digest.hex()

def verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, digest_hex = stored.split("$", 1)
        candidate = hash_password(password, bytes.fromhex(salt_hex)).split("$", 1)[1]
        return hmac.compare_digest(candidate, digest_hex)
    except (ValueError, TypeError):
        return False

@contextmanager
def db():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA foreign_keys=ON")
        yield conn
        conn.commit()
    finally:
        conn.close()

def init_db():
    with db() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS admins (
            username TEXT PRIMARY KEY, password_hash TEXT NOT NULL)""")
        conn.execute("""CREATE TABLE IF NOT EXISTS inquiries (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
            email TEXT NOT NULL, service TEXT NOT NULL, details TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'جديد', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)""")
        conn.execute("""CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL,
            action TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)""")
        row = conn.execute("SELECT username FROM admins WHERE username=?", (ADMIN_USERNAME,)).fetchone()
        if not row:
            conn.execute("INSERT INTO admins(username,password_hash) VALUES(?,?)",
                         (ADMIN_USERNAME, hash_password(ADMIN_PASSWORD)))

init_db()

def csrf_token(request: Request) -> str:
    token = request.session.get("csrf")
    if not token:
        token = secrets.token_urlsafe(32)
        request.session["csrf"] = token
    return token

def check_csrf(request: Request, submitted: str):
    expected = request.session.get("csrf", "")
    if not expected or not hmac.compare_digest(expected, submitted or ""):
        raise HTTPException(status_code=403, detail="طلب غير صالح. حدّث الصفحة وحاول مرة أخرى.")

def admin_user(request: Request):
    user = request.session.get("admin")
    if not user:
        return None
    with db() as conn:
        row = conn.execute("SELECT username FROM admins WHERE username=?", (user,)).fetchone()
    return row["username"] if row else None

def require_admin(request: Request):
    user = admin_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="يلزم تسجيل الدخول")
    return user

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "csrf": csrf_token(request)})

@app.post("/contact")
def contact(request: Request, name: str = Form(...), email: str = Form(...),
            service: str = Form(...), details: str = Form(...), csrf: str = Form(...)):
    check_csrf(request, csrf)
    values = [name.strip(), email.strip(), service.strip(), details.strip()]
    if any(not x for x in values) or len(values[0]) > 100 or len(values[1]) > 200 or len(values[2]) > 100 or len(values[3]) > 5000:
        raise HTTPException(status_code=400, detail="تأكد من البيانات وحدود طولها.")
    if "@" not in values[1] or "." not in values[1].split("@")[-1]:
        raise HTTPException(status_code=400, detail="البريد الإلكتروني غير صحيح.")
    with db() as conn:
        conn.execute("INSERT INTO inquiries(name,email,service,details) VALUES(?,?,?,?)", values)
    return RedirectResponse("/?sent=1#contact", status_code=303)

@app.get("/admin", response_class=HTMLResponse)
def admin_login_page(request: Request):
    if admin_user(request):
        return RedirectResponse("/admin/dashboard", status_code=303)
    return templates.TemplateResponse("login.html", {"request": request, "csrf": csrf_token(request), "error": ""})

@app.post("/admin/login", response_class=HTMLResponse)
def admin_login(request: Request, username: str = Form(...), password: str = Form(...), csrf: str = Form(...)):
    check_csrf(request, csrf)
    # Simple per-process delay after invalid login; production should also use a reverse-proxy rate limit.
    with db() as conn:
        row = conn.execute("SELECT username,password_hash FROM admins WHERE username=?", (username.strip(),)).fetchone()
    if not row or not verify_password(password, row["password_hash"]):
        time.sleep(0.7)
        return templates.TemplateResponse("login.html", {"request": request, "csrf": csrf_token(request),
            "error": "بيانات الدخول غير صحيحة."}, status_code=401)
    request.session.clear()
    request.session["admin"] = row["username"]
    request.session["csrf"] = secrets.token_urlsafe(32)
    with db() as conn:
        conn.execute("INSERT INTO audit_log(username,action) VALUES(?,?)", (row["username"], "login"))
    return RedirectResponse("/admin/dashboard", status_code=303)

@app.get("/admin/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    user = require_admin(request)
    with db() as conn:
        inquiries = conn.execute("SELECT * FROM inquiries ORDER BY id DESC LIMIT 100").fetchall()
        total = conn.execute("SELECT COUNT(*) AS n FROM inquiries").fetchone()["n"]
        new_count = conn.execute("SELECT COUNT(*) AS n FROM inquiries WHERE status='جديد'").fetchone()["n"]
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": user,
        "inquiries": inquiries, "total": total, "new_count": new_count, "csrf": csrf_token(request)})

@app.post("/admin/inquiry/{inquiry_id}/status")
def update_status(request: Request, inquiry_id: int, status: str = Form(...), csrf: str = Form(...)):
    user = require_admin(request)
    check_csrf(request, csrf)
    allowed = {"جديد", "قيد التنفيذ", "مكتمل", "مرفوض"}
    if status not in allowed:
        raise HTTPException(status_code=400, detail="حالة غير مسموحة")
    with db() as conn:
        cur = conn.execute("UPDATE inquiries SET status=? WHERE id=?", (status, inquiry_id))
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="الطلب غير موجود")
        conn.execute("INSERT INTO audit_log(username,action) VALUES(?,?)", (user, f"update inquiry {inquiry_id}: {status}"))
    return RedirectResponse("/admin/dashboard", status_code=303)

@app.post("/admin/logout")
def logout(request: Request, csrf: str = Form(...)):
    user = require_admin(request)
    check_csrf(request, csrf)
    with db() as conn:
        conn.execute("INSERT INTO audit_log(username,action) VALUES(?,?)", (user, "logout"))
    request.session.clear()
    return RedirectResponse("/admin", status_code=303)

@app.get("/admin/ai", response_class=HTMLResponse)
def ai_page(request: Request):
    user = require_admin(request)
    return templates.TemplateResponse("ai.html", {"request": request, "user": user, "csrf": csrf_token(request), "answer": "", "prompt": "", "error": ""})

@app.post("/admin/ai", response_class=HTMLResponse)
async def ai_run(request: Request, prompt: str = Form(...), csrf: str = Form(...)):
    user = require_admin(request)
    check_csrf(request, csrf)
    prompt = prompt.strip()
    if not prompt or len(prompt) > 6000:
        raise HTTPException(status_code=400, detail="اكتب طلبًا من 1 إلى 6000 حرف.")
    answer, error = "", ""
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(f"{OLLAMA_URL}/api/generate", json={
                "model": OLLAMA_MODEL,
                "prompt": "أنت مساعد Nova Digital المحلي. أجب بالعربية بوضوح، ولا تدّع تنفيذ أي إجراء لم تنفذه.\n\nطلب المستخدم:\n" + prompt,
                "stream": False
            })
            response.raise_for_status()
            answer = response.json().get("response", "")
    except Exception:
        error = "تعذّر الاتصال بـ Ollama. تأكد أنه يعمل محليًا وأن النموذج المحدد محمّل."
    return templates.TemplateResponse("ai.html", {"request": request, "user": user, "csrf": csrf_token(request),
        "answer": answer, "prompt": prompt, "error": error})
