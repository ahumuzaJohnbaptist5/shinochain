# Shinochain

A TikTok-like short video web app built with Next.js (frontend) and Django (backend).

## Tech Stack

- **Frontend**: Next.js 14, TypeScript, Tailwind CSS, hls.js
- **Backend**: Django 4.2, Django REST Framework, SimpleJWT
- **Database**: PostgreSQL 16
- **Cache / Queue broker**: Redis 7
- **Background workers**: Celery + FFmpeg (HLS transcoding + thumbnails)
- **Object storage**: Cloudflare R2 (S3-compatible; MinIO for local dev)
- **Search**: Meilisearch
- **Analytics**: Postgres-backed event table

## Project Structure

```
shinochain/
├── backend/               # Django project
│   ├── accounts/          # User model, auth endpoints
│   ├── videos/            # Video model, feed, upload
│   ├── social/            # Follow, Like, Comment
│   ├── analytics/         # Event ingestion
│   ├── worker/            # Celery tasks
│   ├── shinochain/        # Django settings/URLs/celery
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/              # Next.js app
│   ├── src/
│   │   ├── app/           # App Router pages
│   │   ├── components/    # VideoPlayer, FeedItem
│   │   └── lib/           # API client, auth helpers
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml     # Local dev stack
└── README.md
```

## Local Development Setup

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (or Docker + Docker Compose)
- OR: Python 3.12+, Node.js 20+, FFmpeg, PostgreSQL, Redis

---

### Option A: Docker Compose (recommended)

1. **Clone the repository**
   ```bash
   git clone https://github.com/ahumuzaJohnbaptist5/shinochain.git
   cd shinochain
   ```

2. **Configure backend environment**
   ```bash
   cp backend/.env.example backend/.env
   # Edit backend/.env — at minimum set SECRET_KEY
   ```

3. **Configure frontend environment**
   ```bash
   cp frontend/.env.local.example frontend/.env.local
   ```

4. **Start all services**
   ```bash
   docker compose up --build
   ```

5. **Run database migrations** (in a new terminal)
   ```bash
   docker compose exec backend python manage.py migrate
   ```

6. **Create a superuser** (optional)
   ```bash
   docker compose exec backend python manage.py createsuperuser
   ```

7. **Open the app**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000/api/
   - MinIO console: http://localhost:9001 (user: `minioadmin`, pass: `minioadmin`)
   - Meilisearch: http://localhost:7700

---

### Option B: Manual setup

#### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # Edit .env with your values
python manage.py migrate
python manage.py runserver
```

Start the Celery worker (separate terminal):
```bash
celery -A shinochain worker -l info
```

#### Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

---

## Environment Variables

### Backend (`backend/.env`)

| Variable | Description | Example |
|---|---|---|
| `SECRET_KEY` | Django secret key | `django-insecure-...` |
| `DEBUG` | Debug mode | `True` |
| `DATABASE_URL` | Postgres connection | `postgres://postgres:postgres@localhost:5432/shinochain` |
| `REDIS_URL` | Redis connection | `redis://localhost:6379/0` |
| `AWS_ACCESS_KEY_ID` | R2 / MinIO access key | |
| `AWS_SECRET_ACCESS_KEY` | R2 / MinIO secret key | |
| `AWS_STORAGE_BUCKET_NAME` | Bucket name | `shinochain-videos` |
| `AWS_S3_ENDPOINT_URL` | R2 or MinIO endpoint | `http://localhost:9000` |
| `MEILISEARCH_URL` | Meilisearch URL | `http://localhost:7700` |
| `MEILISEARCH_MASTER_KEY` | Meilisearch master key | `masterKey` |
| `FRONTEND_URL` | CORS allowed origin | `http://localhost:3000` |

### Frontend (`frontend/.env.local`)

| Variable | Description | Example |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | Backend API base URL | `http://localhost:8000` |

---

## API Reference

### Auth
| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/auth/register` | — | Register new user |
| POST | `/api/auth/login` | — | Login, returns JWT |
| GET | `/api/me` | JWT | Current user profile |

### Videos
| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/uploads/video` | JWT | Get presigned PUT URL for R2 |
| POST | `/api/videos` | JWT | Publish video + enqueue processing |
| GET | `/api/feed?cursor=...` | — | Cursor-based video feed |
| GET | `/api/search?q=...` | — | Search videos & users |

### Social
| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/videos/{id}/like` | JWT | Like a video |
| DELETE | `/api/videos/{id}/like` | JWT | Unlike a video |
| GET | `/api/videos/{id}/comments` | — | List comments |
| POST | `/api/videos/{id}/comments` | JWT | Post a comment |
| POST | `/api/users/{id}/follow` | JWT | Follow a user |
| DELETE | `/api/users/{id}/follow` | JWT | Unfollow a user |

### Analytics
| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/analytics/events` | — | Batch ingest analytics events |

---

## Video Processing Pipeline

1. Frontend requests a **presigned PUT URL** (`POST /api/uploads/video`)
2. Browser uploads raw video **directly to R2/MinIO** (no backend bandwidth used)
3. Frontend calls `POST /api/videos` with `upload_key`, caption, hashtags
4. Django creates the Video record (`status=pending`) and enqueues `process_video` Celery task
5. Worker:
   - Downloads raw file from storage
   - Runs FFmpeg → HLS master + 360p / 720p / 1080p variants
   - Generates thumbnail (screenshot at 1 s)
   - Uploads all segments + thumbnail to storage
   - Updates Video record (`status=ready`, `hls_manifest_url`, `thumbnail_url`)
   - Indexes video in Meilisearch

---

## Production Notes

- Replace MinIO with **Cloudflare R2** (set `AWS_S3_ENDPOINT_URL` to your R2 endpoint)
- Host Django on **Railway / Render / Fly.io**
- Deploy Next.js to **Vercel** (set `NEXT_PUBLIC_API_URL` to your production Django URL)
- Move JWT storage from `localStorage` to **HttpOnly cookies** with CSRF protection
- Add a CDN in front of R2 for video segment delivery
- Scale Celery workers horizontally for high upload volume

---

## License

MIT
