# Hotel Channel Manager MVP

A FastAPI-based channel manager for synchronizing hotel inventory across OTA channels.

## Quick Start

```bash
# Install backend dependencies
pip install -r requirements.txt

# Start PostgreSQL and Redis
docker-compose up -d

# Run database migrations
alembic upgrade head

# Start the backend server
uvicorn app.main:app --reload

# Start the frontend
npm run dev
```

## API Endpoints

- `POST /webhook/booking-received` - Ingest OTA reservations
- `POST /webhook/airbnb/ical-sync` - Sync Airbnb iCal
- `GET /api/v1/inventory/{room_type_id}` - Query inventory
- `POST /api/v1/rates/{room_type_id}/parity` - Push rate parity

## Environment Variables

```
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/channel_manager
REDIS_URL=redis://localhost:6379/0
```
