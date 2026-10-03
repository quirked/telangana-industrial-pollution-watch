# Telangana Industrial Pollution Watch

A polished Government of Telangana hackathon prototype for reporting and tracking **visible industrial pollution observations** across Telangana.

> This is a hackathon prototype, not an officially deployed government service. A submitted report is an observation; it does not by itself establish a scientific finding or legal violation. The application is not connected to TGPCB systems.

## What works

- Citizen incident submission with all 33 Telangana districts, locality, address, observation type, optional industry/unit details, optional coordinates, date/time, and image evidence.
- Unique report IDs such as `INC-2026-0005`.
- Public register, Demo Citizen dashboard, evidence-focused detail page, and actual status history.
- Authority dashboard with six status metrics, complete evidence review, public remarks, action taken, and status updates.
- Shared SQLite persistence so authority updates immediately appear in the citizen view and survive restarts.
- Four fictional Telangana demo incidents with local evidence illustrations.
- Responsive layouts, validation, upload limits, health endpoint, and friendly error pages.

## Run locally

All project work uses the existing `sao` Conda environment and tmux session.

```bash
tmux attach -t sao
cd /home/raghav/industrial-pollution-reporting
conda activate sao
python -m pip install -r requirements.txt
python app.py
```

Open <http://127.0.0.1:5050>. The database and four seed reports are created automatically on the first start.

## Test

```bash
cd /home/raghav/industrial-pollution-reporting
/home/raghav/miniconda3/envs/sao/bin/python -m pytest -q
```

The integration suite covers seeded pages, validation, report creation, image serving, authority updates, public timeline visibility, dashboard visibility, 404 handling, and persistence after application recreation.

## Render deployment configuration

The repository is prepared for a Render Python web service but has not been deployed.

- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn app:app`
- Python version: `3.11.16` from `.python-version`
- Health check path: `/health`
- Recommended environment variable: set `SECRET_KEY` to a strong generated value in Render.

The default local paths remain `instance/pollution.db` and `uploads/`. To retain SQLite data and uploaded evidence on Render, attach a paid persistent disk at `/var/data` and set `DATA_DIR=/var/data`. The database will then use `/var/data/pollution.db` and evidence will use `/var/data/uploads/` without changing the application architecture.

Without a persistent disk, Render's filesystem is ephemeral. The application will run, but submitted reports and uploaded evidence can be lost on a deploy, restart, or free-service spin-down.

References: [Render Flask deployment guide](https://render.com/docs/deploy-flask) and [Render persistent disk documentation](https://render.com/docs/disks).

## Demo flow

1. Open `/report` and enter:
   - Observation: `Smoke / Air Emission`
   - Title: `Heavy black smoke from industrial chimney`
   - Description: `Continuous black smoke has been visible for approximately 30 minutes.`
   - District: `Sangareddy`
   - Locality: `Patancheru`
   - Address: `Industrial Area, Sector 4`
   - Factory: `Demo Steel Works`
   - Industry: `Steel / Sponge Iron`
2. Upload a JPG, PNG, or WebP image and submit.
3. Note the generated `INC-2026-XXXX` ID and initial `Reported` status.
4. Open `/authority`, find that ID, and select **Review**.
5. Set status to `Under Review`, remark to `Inspection team has been informed.`, and record an action.
6. Later update it to `Action in Progress`.
7. Open the public tracking page and verify the status, remark, action, evidence, location, and chronological history.

The local database currently includes a verified walkthrough report, `INC-2026-0005`, in `Action in Progress` state.

## Project structure

- `app.py` — routes, validation, uploads, citizen workflow, authority workflow, and errors.
- `db.py` / `schema.sql` — SQLite lifecycle and schema.
- `constants.py` — districts, observations, industries, and statuses.
- `seed.py` — idempotent fictional Telangana demo records and local evidence generation.
- `templates/` — server-rendered citizen and authority interfaces.
- `static/` — responsive civic-tech design, favicon, and image-preview behavior.
- `tests/test_workflow.py` — critical-path integration tests.
- `PROJECT_LOG.md` — chronological implementation record, current state, and manifest.

## Data and operational notes

- SQLite database: `instance/pollution.db` (local runtime file, Git-ignored).
- Uploaded evidence: `uploads/` (local runtime files, Git-ignored).
- Upload limit: 8 MB; accepted formats: JPG, JPEG, PNG, WebP.
- `Assigned jurisdiction` mirrors the selected district for prototype routing only.
- No citizen email, phone number, internal notes, authentication, live government routing, or external pollution-control integration is included.
- Official reference: [Telangana Pollution Control Board](https://tgpcb.cgg.gov.in/).
