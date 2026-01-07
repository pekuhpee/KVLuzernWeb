# AGENTS.md
Context: This repo is based on Rocket Django. Reuse existing structure, settings, templates, and conventions.

Rules:
- Only work via PRs. Never push to main.
- PR size <= 300 changed lines. One feature per PR.
- Do NOT refactor unrelated code. Do NOT change dependencies unless requested.
- Keep existing folder structure (notably apps/, config/, templates/ if present).
- Public users have NO accounts. Admin users only.
- MVP order: (1) archive model+admin, (2) archive browse page, (3) archive upload, (4) memes, (5) ranking.
- UI: clean, minimal. Primary #0F3D32, accent #C6A15B, white base. Black and grey if needed Font: Bahnschrift. Orient at Polestar design language
- Always keep `python manage.py migrate` and `python manage.py runserver` working.
