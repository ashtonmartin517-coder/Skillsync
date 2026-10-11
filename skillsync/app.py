"""
SkillSync backend (Flask + SQLite).

Run locally:   python app.py
Production:    gunicorn app:app
"""
import datetime as dt
import os
import re
import secrets
import sqlite3
import time
from collections import defaultdict, deque
from functools import wraps

from flask import Flask, g, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

import content

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("SKILLSYNC_DB", os.path.join(BASE_DIR, "instance", "skillsync.db"))

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get("SECRET_KEY") or "dev-only-change-me",
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE", "0") == "1",
    PERMANENT_SESSION_LIFETIME=dt.timedelta(days=30),
    MAX_CONTENT_LENGTH=64 * 1024,
)
if app.config["SECRET_KEY"] == "dev-only-change-me" and os.environ.get("FLASK_ENV") == "production":
    raise RuntimeError("Set the SECRET_KEY environment variable in production.")

SKILL_BY_ID = {s["id"]: s for s in content.SKILLS}
SKILL_IDS = [s["id"] for s in content.SKILLS]
TASK_XP = 20
ASSESS_XP = 50
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# --------------------------------------------------------------------------
# Database
# --------------------------------------------------------------------------
SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL,
    email         TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    college       TEXT NOT NULL,
    course        TEXT NOT NULL,
    year          INTEGER NOT NULL,
    contact       TEXT NOT NULL DEFAULT '',
    streak        INTEGER NOT NULL DEFAULT 0,
    last_active   TEXT,
    assessed      INTEGER NOT NULL DEFAULT 0,
    created_at    TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS answers (
    user_id  INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    skill_id TEXT NOT NULL,
    level    INTEGER NOT NULL CHECK (level BETWEEN 0 AND 3),
    PRIMARY KEY (user_id, skill_id)
);
CREATE TABLE IF NOT EXISTS tasks_done (
    user_id  INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    task_id  TEXT NOT NULL,
    done_at  TEXT NOT NULL,
    PRIMARY KEY (user_id, task_id)
);
CREATE TABLE IF NOT EXISTS connections (
    from_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    to_id      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TEXT NOT NULL,
    PRIMARY KEY (from_id, to_id)
);
"""


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()


# --------------------------------------------------------------------------
# Helpers: dates, auth, rate limiting, validation
# --------------------------------------------------------------------------
def now_iso():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def today():
    return dt.date.today().isoformat()


def yesterday():
    return (dt.date.today() - dt.timedelta(days=1)).isoformat()


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if "uid" not in session:
            if request.path.startswith("/api/"):
                return jsonify(error="Please log in first."), 401
            return redirect(url_for("index"))
        return fn(*args, **kwargs)
    return wrapper


_attempts = defaultdict(deque)


def rate_limited(key, limit=10, window=300):
    now = time.time()
    q = _attempts[key]
    while q and now - q[0] > window:
        q.popleft()
    if len(q) >= limit:
        return True
    q.append(now)
    return False


def json_body():
    if not request.is_json:
        return None
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else None


def clean(text, max_len):
    return re.sub(r"\s+", " ", str(text or "")).strip()[:max_len]


@app.after_request
def security_headers(resp):
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["Referrer-Policy"] = "same-origin"
    if request.path.startswith("/api/"):
        resp.headers["Cache-Control"] = "no-store"
    return resp


# --------------------------------------------------------------------------
# Core logic: levels, XP, streak, badges
# --------------------------------------------------------------------------
def get_levels(db, user_id):
    rows = db.execute("SELECT skill_id, level FROM answers WHERE user_id = ?", (user_id,)).fetchall()
    levels = {sid: 0 for sid in SKILL_IDS}
    for r in rows:
        if r["skill_id"] in levels:
            levels[r["skill_id"]] = r["level"]
    return levels


def get_done(db, user_id):
    rows = db.execute("SELECT task_id FROM tasks_done WHERE user_id = ?", (user_id,)).fetchall()
    return {r["task_id"] for r in rows}


def compute_xp(assessed, done_count):
    return ASSESS_XP * int(bool(assessed)) + TASK_XP * done_count


def level_info(xp):
    idx = 0
    for i, (need, _name) in enumerate(content.LEVELS):
        if xp >= need:
            idx = i
    cur_need, name = content.LEVELS[idx]
    if idx + 1 < len(content.LEVELS):
        nxt_need = content.LEVELS[idx + 1][0]
        pct = round((xp - cur_need) / (nxt_need - cur_need) * 100)
    else:
        nxt_need, pct = None, 100
    return {"number": idx + 1, "name": name, "next_xp": nxt_need, "progress": pct}


def live_streak(user):
    """Streak only counts if the student was active today or yesterday."""
    if user["last_active"] in (today(), yesterday()):
        return user["streak"]
    return 0


def touch_streak(db, user):
    """Call whenever the student does something worth keeping a streak for."""
    t = today()
    if user["last_active"] == t:
        return
    new = user["streak"] + 1 if user["last_active"] == yesterday() else 1
    db.execute("UPDATE users SET streak = ?, last_active = ? WHERE id = ?", (new, t, user["id"]))


def skill_task_ids(skill_id):
    return [f"{skill_id}:{i}" for i in range(len(SKILL_BY_ID[skill_id]["tasks"]))]


def compute_badges(user, levels, done, streak):
    done_by_skill = {sid: sum(1 for t in skill_task_ids(sid) if t in done) for sid in SKILL_IDS}

    def finished(sid):
        return done_by_skill[sid] == len(SKILL_BY_ID[sid]["tasks"])

    defs = [
        ("assessed", "Mapped", "Completed the skill check", bool(user["assessed"])),
        ("first_task", "First Move", "Finished your first task", len(done) >= 1),
        ("five_tasks", "On a Roll", "Finished 5 tasks", len(done) >= 5),
        ("streak3", "3-Day Streak", "Showed up 3 days in a row", streak >= 3),
        ("streak7", "Week Warrior", "Showed up 7 days in a row", streak >= 7),
        ("terminal", "Terminal Tamer", "Finished every Terminal task", finished("terminal")),
        ("git", "Save Pointer", "Finished every Git task", finished("git")),
        ("project", "Shipper", "Finished every Project task", finished("project")),
        ("allrounder", "All-rounder", "Rated yourself 2+ in every skill", user["assessed"] and all(v >= 2 for v in levels.values())),
    ]
    return [{"id": i, "name": n, "desc": d, "earned": bool(e)} for i, n, d, e in defs]


# --------------------------------------------------------------------------
# Rule-based gap analysis and roadmap
# --------------------------------------------------------------------------
def gap_analysis(levels):
    """
    priority = weight x gap, where gap = 3 - level.
    Foundations are boosted: a skill that other skills depend on gets +1 per dependant,
    so Terminal and Git rise to the top for beginners.
    """
    dependants = {sid: 0 for sid in SKILL_IDS}
    for s in content.SKILLS:
        for p in s["prereq"]:
            dependants[p] += 1

    skills = []
    for idx, s in enumerate(content.SKILLS):
        lvl = levels[s["id"]]
        gap = 3 - lvl
        priority = (s["weight"] + dependants[s["id"]]) * gap
        skills.append({"id": s["id"], "name": s["name"], "area": s["area"], "level": lvl,
                       "label": content.LEVEL_LABELS[lvl], "gap": gap, "priority": priority, "_idx": idx})

    total = sum(levels.values())
    readiness = round(total / (3 * len(SKILL_IDS)) * 100)

    areas = {}
    for s in skills:
        a = areas.setdefault(s["area"], {"area": s["area"], "score": 0, "max": 0})
        a["score"] += s["level"]
        a["max"] += 3
    area_list = [{"area": a["area"], "percent": round(a["score"] / a["max"] * 100)} for a in areas.values()]

    if readiness < 20:
        stage = "Starter"
    elif readiness < 45:
        stage = "Explorer"
    elif readiness < 70:
        stage = "Builder"
    else:
        stage = "Hire-ready"

    ranked = sorted(skills, key=lambda s: (-s["priority"], s["_idx"]))
    for s in ranked:
        s.pop("_idx")
    top_gaps = [s["id"] for s in ranked if s["gap"] > 0][:3]
    return {"readiness": readiness, "stage": stage, "areas": area_list,
            "skills": ranked, "top_gaps": top_gaps}


def build_roadmap(levels, done, weeks=4, per_week=3):
    """Order skills by priority, pull in prerequisites first, then split into weeks."""
    ranked = [s for s in gap_analysis(levels)["skills"] if s["gap"] > 0]
    order, seen = [], set()

    def add(sid):
        if sid in seen:
            return
        for p in SKILL_BY_ID[sid]["prereq"]:
            if levels[p] < 2:
                add(p)
        seen.add(sid)
        order.append(sid)

    for s in ranked:
        add(s["id"])

    roadmap = []
    for w in range(weeks):
        chunk = order[w * per_week:(w + 1) * per_week]
        if not chunk:
            break
        items = []
        for sid in chunk:
            skill = SKILL_BY_ID[sid]
            start = 0 if levels[sid] <= 1 else 2  # level 0/1 -> all tasks, level 2 -> last task only
            tasks = []
            for i, t in enumerate(skill["tasks"]):
                if i < start:
                    continue
                tid = f"{sid}:{i}"
                tasks.append({"id": tid, "title": t["title"], "detail": t["detail"],
                              "minutes": t["minutes"], "xp": TASK_XP, "done": tid in done})
            items.append({"id": sid, "name": skill["name"], "area": skill["area"],
                          "analogy": skill["analogy"], "why": skill["why"], "tasks": tasks})
        roadmap.append({"week": w + 1, "focus": ", ".join(s["name"] for s in items), "skills": items})
    return roadmap


# --------------------------------------------------------------------------
# Peer matching
# --------------------------------------------------------------------------
def match_peers(me, my_levels, db, limit=6):
    """
    Score every assessed student against me:
      +3 x weight  for each skill they are strong in (>=2) and I am weak in (<=1)   -> they can help me
      +2 x weight  for each skill I am strong in and they are weak in               -> I can help them
      +1 x weight  for each skill we are both weak in                               -> study buddies
      +15 same college, +5 same course, +3 same year
    """
    others = db.execute("SELECT * FROM users WHERE id != ? AND assessed = 1", (me["id"],)).fetchall()
    sent = {r["to_id"] for r in db.execute("SELECT to_id FROM connections WHERE from_id = ?", (me["id"],))}
    got = {r["from_id"] for r in db.execute("SELECT from_id FROM connections WHERE to_id = ?", (me["id"],))}

    results = []
    for o in others:
        theirs = get_levels(db, o["id"])
        helps_me, i_help, buddies = [], [], []
        score = 0
        for s in content.SKILLS:
            sid, w = s["id"], s["weight"]
            mine, them = my_levels[sid], theirs[sid]
            if them >= 2 and mine <= 1:
                helps_me.append(s["name"]); score += 3 * w
            elif mine >= 2 and them <= 1:
                i_help.append(s["name"]); score += 2 * w
            elif mine <= 1 and them <= 1:
                buddies.append(s["name"]); score += w
        if o["college"].strip().lower() == me["college"].strip().lower():
            score += 15
        if o["course"] == me["course"]:
            score += 5
        if o["year"] == me["year"]:
            score += 3
        if score <= 0:
            continue

        reasons = []
        if helps_me:
            reasons.append("Can help you with " + ", ".join(helps_me[:2]))
        if i_help:
            reasons.append("You can help with " + ", ".join(i_help[:2]))
        if buddies and not (helps_me or i_help):
            reasons.append("Both starting out in " + ", ".join(buddies[:2]))
        if o["college"].strip().lower() == me["college"].strip().lower():
            reasons.append("Same college")

        mutual = o["id"] in sent and o["id"] in got
        status = "mutual" if mutual else "sent" if o["id"] in sent else "incoming" if o["id"] in got else "none"
        results.append({
            "id": o["id"], "name": o["name"], "college": o["college"], "course": o["course"],
            "year": o["year"], "score": score, "reasons": reasons, "status": status,
            "contact": o["contact"] if mutual else "",
        })
    results.sort(key=lambda r: -r["score"])
    return results[:limit]


# --------------------------------------------------------------------------
# Pages
# --------------------------------------------------------------------------
@app.route("/")
def index():
    if "uid" in session:
        return redirect(url_for("dashboard"))
    return render_template("index.html", courses=content.COURSES)


@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")


@app.route("/healthz")
def healthz():
    return jsonify(ok=True)


# --------------------------------------------------------------------------
# Auth API
# --------------------------------------------------------------------------
@app.post("/api/register")
def api_register():
    data = json_body()
    if data is None:
        return jsonify(error="Send JSON."), 400
    if rate_limited("reg:" + (request.remote_addr or "?"), limit=8):
        return jsonify(error="Too many attempts. Try again in a few minutes."), 429

    name = clean(data.get("name"), 60)
    email = clean(data.get("email"), 120).lower()
    password = str(data.get("password") or "")
    college = clean(data.get("college"), 100)
    course = clean(data.get("course"), 30)
    contact = clean(data.get("contact"), 80)
    try:
        year = int(data.get("year"))
    except (TypeError, ValueError):
        year = 0

    if len(name) < 2:
        return jsonify(error="Please enter your name."), 400
    if not EMAIL_RE.match(email):
        return jsonify(error="Please enter a valid email."), 400
    if len(password) < 8:
        return jsonify(error="Password must be at least 8 characters."), 400
    if len(college) < 2:
        return jsonify(error="Please enter your college."), 400
    if course not in content.COURSES:
        return jsonify(error="Please choose your course."), 400
    if not 1 <= year <= 5:
        return jsonify(error="Year must be between 1 and 5."), 400

    db = get_db()
    try:
        cur = db.execute(
            "INSERT INTO users (name, email, password_hash, college, course, year, contact, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (name, email, generate_password_hash(password), college, course, year, contact,
             now_iso()),
        )
        db.commit()
    except sqlite3.IntegrityError:
        return jsonify(error="That email is already registered. Try logging in."), 409
    session.clear()
    session.permanent = True
    session["uid"] = cur.lastrowid
    return jsonify(ok=True), 201


@app.post("/api/login")
def api_login():
    data = json_body()
    if data is None:
        return jsonify(error="Send JSON."), 400
    if rate_limited("login:" + (request.remote_addr or "?")):
        return jsonify(error="Too many attempts. Try again in a few minutes."), 429
    email = clean(data.get("email"), 120).lower()
    password = str(data.get("password") or "")
    user = get_db().execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify(error="Wrong email or password."), 401
    session.clear()
    session.permanent = True
    session["uid"] = user["id"]
    return jsonify(ok=True)


@app.post("/api/logout")
def api_logout():
    session.clear()
    return jsonify(ok=True)


# --------------------------------------------------------------------------
# App API
# --------------------------------------------------------------------------
def current_user(db):
    return db.execute("SELECT * FROM users WHERE id = ?", (session["uid"],)).fetchone()


@app.get("/api/questions")
@login_required
def api_questions():
    return jsonify(
        levels=[{"value": k, "label": v} for k, v in content.LEVEL_LABELS.items()],
        questions=[{"id": s["id"], "area": s["area"], "text": s["question"], "analogy": s["analogy"]}
                   for s in content.SKILLS],
    )


@app.post("/api/assessment")
@login_required
def api_assessment():
    data = json_body()
    if data is None or not isinstance(data.get("answers"), dict):
        return jsonify(error="Send answers as JSON."), 400
    answers = data["answers"]
    clean_answers = {}
    for sid in SKILL_IDS:
        try:
            lvl = int(answers.get(sid))
        except (TypeError, ValueError):
            return jsonify(error="Please answer every question."), 400
        if lvl not in (0, 1, 2, 3):
            return jsonify(error="Invalid answer."), 400
        clean_answers[sid] = lvl

    db = get_db()
    user = current_user(db)
    db.execute("DELETE FROM answers WHERE user_id = ?", (user["id"],))
    db.executemany("INSERT INTO answers (user_id, skill_id, level) VALUES (?, ?, ?)",
                   [(user["id"], sid, lvl) for sid, lvl in clean_answers.items()])
    db.execute("UPDATE users SET assessed = 1 WHERE id = ?", (user["id"],))
    touch_streak(db, user)
    db.commit()
    return jsonify(ok=True)


@app.get("/api/me")
@login_required
def api_me():
    db = get_db()
    user = current_user(db)
    if user is None:
        session.clear()
        return jsonify(error="Please log in first."), 401
    levels = get_levels(db, user["id"])
    done = get_done(db, user["id"])
    streak = live_streak(user)
    xp = compute_xp(user["assessed"], len(done))
    quote = content.QUOTES[dt.date.today().toordinal() % len(content.QUOTES)]

    payload = {
        "user": {"name": user["name"], "college": user["college"], "course": user["course"],
                 "year": user["year"], "contact": user["contact"], "assessed": bool(user["assessed"])},
        "xp": xp, "streak": streak, "level": level_info(xp), "quote": quote,
        "badges": compute_badges(user, levels, done, streak),
        "analysis": None, "roadmap": [], "mission": None,
    }
    if user["assessed"]:
        payload["analysis"] = gap_analysis(levels)
        payload["roadmap"] = build_roadmap(levels, done)
        for week in payload["roadmap"]:
            for skill in week["skills"]:
                for t in skill["tasks"]:
                    if not t["done"] and payload["mission"] is None:
                        payload["mission"] = {**t, "skill": skill["name"], "analogy": skill["analogy"]}
    return jsonify(payload)


@app.post("/api/tasks/<task_id>/toggle")
@login_required
def api_toggle_task(task_id):
    sid, _, idx = task_id.partition(":")
    if sid not in SKILL_BY_ID or not idx.isdigit() or int(idx) >= len(SKILL_BY_ID[sid]["tasks"]):
        return jsonify(error="Unknown task."), 404
    db = get_db()
    user = current_user(db)
    exists = db.execute("SELECT 1 FROM tasks_done WHERE user_id = ? AND task_id = ?",
                        (user["id"], task_id)).fetchone()
    if exists:
        db.execute("DELETE FROM tasks_done WHERE user_id = ? AND task_id = ?", (user["id"], task_id))
        now_done = False
    else:
        db.execute("INSERT INTO tasks_done (user_id, task_id, done_at) VALUES (?, ?, ?)",
                   (user["id"], task_id, now_iso()))
        touch_streak(db, user)
        now_done = True
    db.commit()
    return jsonify(ok=True, done=now_done)


@app.post("/api/profile")
@login_required
def api_profile():
    data = json_body()
    if data is None:
        return jsonify(error="Send JSON."), 400
    contact = clean(data.get("contact"), 80)
    db = get_db()
    db.execute("UPDATE users SET contact = ? WHERE id = ?", (contact, session["uid"]))
    db.commit()
    return jsonify(ok=True)


@app.get("/api/glossary")
@login_required
def api_glossary():
    q = clean(request.args.get("q"), 40).lower()
    items = content.GLOSSARY
    if q:
        items = [g_ for g_ in items if q in g_["term"].lower() or q in g_["analogy"].lower()]
    return jsonify(items=items)


@app.get("/api/pulse")
@login_required
def api_pulse():
    return jsonify(items=content.PULSE)


@app.get("/api/peers")
@login_required
def api_peers():
    db = get_db()
    user = current_user(db)
    if not user["assessed"]:
        return jsonify(error="Finish the skill check first so we can match you."), 409
    return jsonify(items=match_peers(user, get_levels(db, user["id"]), db))


@app.post("/api/connect/<int:other_id>")
@login_required
def api_connect(other_id):
    db = get_db()
    me = session["uid"]
    if other_id == me:
        return jsonify(error="That is you."), 400
    if not db.execute("SELECT 1 FROM users WHERE id = ?", (other_id,)).fetchone():
        return jsonify(error="Student not found."), 404
    db.execute("INSERT OR IGNORE INTO connections (from_id, to_id, created_at) VALUES (?, ?, ?)",
               (me, other_id, now_iso()))
    db.commit()
    back = db.execute("SELECT 1 FROM connections WHERE from_id = ? AND to_id = ?", (other_id, me)).fetchone()
    return jsonify(ok=True, status="mutual" if back else "sent")


@app.get("/api/leaderboard")
@login_required
def api_leaderboard():
    db = get_db()
    me = current_user(db)
    scope = request.args.get("scope", "all")
    where, params = "", []
    if scope == "college":
        where, params = "WHERE lower(u.college) = lower(?)", [me["college"]]
    rows = db.execute(
        f"""SELECT u.id, u.name, u.college,
                   (u.assessed * {ASSESS_XP}) + {TASK_XP} * (SELECT COUNT(*) FROM tasks_done t WHERE t.user_id = u.id) AS xp
            FROM users u {where}
            ORDER BY xp DESC, u.id ASC""", params).fetchall()
    board = [{"rank": i + 1, "name": r["name"], "college": r["college"], "xp": r["xp"], "me": r["id"] == me["id"]}
             for i, r in enumerate(rows)]
    my_rank = next((b["rank"] for b in board if b["me"]), None)
    return jsonify(items=board[:20], my_rank=my_rank, total=len(board), scope=scope)


init_db()

if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG", "1") == "1", port=int(os.environ.get("PORT", 5000)))
