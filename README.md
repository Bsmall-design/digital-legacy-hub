# Digital Legacy Hub

**Learn. Practice. Build. Understand.**

Digital Legacy Hub is an open, student-first computer science learning platform designed to reduce the gap between *watching tutorials* and *actually being able to compute, code, analyze data and build software*.

It combines structured learning paths, hands-on practice, challenges with explanations, datasets, a SQL playground, browser Python lab, project portfolios, progress analytics, certificates, an admin CMS, and an AI learning guide.

## Product vision

> **Don't just teach students what code is. Help them understand how computation works, practice it, debug it, explain it, and build with it.**

## Core learning paths

- Computer Science Foundations
- Programming & Python
- Algorithms & Problem Solving
- Data Structures
- Databases & SQL
- Data Analytics
- Web Development
- Cybersecurity & Networks
- Cloud & DevOps Foundations
- Digital Productivity & Career Skills

## Learning loop

**Learn → See → Try → Fail → Understand → Practice → Challenge → Build → Reflect → Publish**

The product deliberately makes practice and understanding first-class features rather than treating certificates as the final goal.

## Technology

- Backend: Python + Flask
- Database: SQLite for development, PostgreSQL-ready architecture
- Frontend: responsive HTML/CSS/JavaScript
- Browser Python execution: Pyodide-ready code lab
- SQL: isolated read-only playground
- AI: provider-agnostic tutor endpoint with OpenAI Responses API integration option
- PWA: installable web-app shell for Android/iOS browsers
- Mobile: Capacitor-ready wrapper structure
- Deployment: Docker + Gunicorn + GitHub Actions ready

## Run locally

```bash
cd app
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000`.

### AI tutor

Copy `.env.example` to `.env` and set your provider key when you are ready. **Never commit API keys.**

## Mobile app path

The web application is designed as a PWA and the `mobile/` folder contains a Capacitor wrapper plan. This means the same product can become an Android/iOS app without creating a second learning system.

```text
Browser/PWA → Capacitor → Android APK/AAB + iOS app
```

App-store publishing still requires developer accounts, signing, store metadata, privacy documentation and review by Google/Apple.

## Repository structure

```text
Digital-Legacy-Hub/
├── app/                 # Flask application
├── web/                 # templates, CSS, JS, PWA assets
├── mobile/              # Capacitor mobile wrapper setup
├── docs/                # architecture, product and CV documentation
├── .github/workflows/   # CI
├── Dockerfile
├── .env.example
└── README.md
```

## CV-ready project entry

**Digital Legacy Hub — Founder & Lead Developer**  
Built a student-first computer science learning platform combining structured CS curricula, interactive Python and SQL practice, data-analysis datasets, challenge-based assessment, progress analytics, project portfolios, certificates, admin content management, and an AI learning guide; architected a Flask/SQLite system with a PWA/mobile-app path and deployment-ready engineering practices.

## Long-term roadmap

1. PostgreSQL + production authentication
2. Real-time collaborative coding rooms
3. AI tutor with curriculum-aware retrieval and learner memory
4. Auto-grading for Python/SQL challenges in isolated sandboxes
5. Accessibility + multilingual learning content
6. Offline-first lessons for low-connectivity environments
7. University/teacher dashboards
8. Android/iOS store release
9. Public project showcase and global student community
10. Open curriculum contributions and international cohorts
