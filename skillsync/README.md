# SkillSync

A free, gamified web app that helps first-year tech students from non-tech backgrounds:

- understand basic tech terms through everyday analogies (Git, GitHub, LeetCode, APIs...)
- check their current skills with a 13-question quiz
- get a rule-based 4-week roadmap (prerequisites first)
- earn XP, badges and streaks
- find peers who are strong where they are weak

**Stack:** Python 3 + Flask, SQLite, HTML + Tailwind CSS (CDN) + vanilla JavaScript.

## Project structure

```
skillsync/
├── app.py              # Flask app: routes, auth, gap analysis, roadmap, peer matching
├── content.py          # All learning content: skills, tasks, glossary, quotes, weekly pulse
├── test_app.py         # Smoke tests
├── requirements.txt
├── Procfile            # For Render / Railway / Heroku-style hosting
├── .env.example
├── .gitignore
├── instance/           # SQLite database lives here (not committed)
├── templates/
│   ├── index.html      # Landing page + sign up / log in
│   └── dashboard.html  # Dashboard shell (JS renders each tab)
└── static/
    ├── css/style.css
    └── js/script.js
```

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000. Run tests with `python -m unittest test_app.py`.

## How the logic works

- **Gap analysis:** `priority = (skill weight + number of skills that depend on it) x (3 - your level)`.
- **Roadmap:** skills sorted by priority, prerequisites pulled in first, split into 3 skills per week.
- **Peer matching:** +3 x weight for skills they are strong in and you are weak in, +2 x weight for the reverse, +1 x weight when both are starting out, plus small bonuses for same college, course and year.
- **Privacy:** emails are never shown. Contact details appear only after both students connect.

## Add your own content

Open `content.py`. Add a skill, a glossary term or a weekly pulse card, restart the server, done.

## Deploy free on Render

1. Push this repo to GitHub.
2. On render.com: New > Web Service > connect the repo.
3. Build command: `pip install -r requirements.txt`. Start command: `gunicorn app:app`.
4. Environment variables: `SECRET_KEY` (long random string), `COOKIE_SECURE=1`, `FLASK_ENV=production`.
5. Note: free hosts wipe local files on redeploy, so SQLite data can reset. For real users, add a persistent disk or move to PostgreSQL.

## Known limits (be honest in interviews)

- SQLite is fine for a college-sized pilot, not for thousands of users.
- Rate limiting is in memory and per process.
- No email verification or password reset yet.
