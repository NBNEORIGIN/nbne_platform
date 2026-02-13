# Database Setup Instructions

## PostgreSQL 17 Setup for Django Booking Platform

### Step 1: Create Database and User

You need to create the database and user in PostgreSQL. Choose one of these methods:

#### Method A: Using pgAdmin (Recommended for Windows)

1. **Open pgAdmin** (should be installed with PostgreSQL 17)

2. **Connect to PostgreSQL 17 server**
   - Default connection should work
   - Password: your postgres password

3. **Create Database**
   - Right-click "Databases" → Create → Database
   - Database name: `booking_db`
   - Owner: postgres (for now)
   - Click "Save"

4. **Create User**
   - Expand "Login/Group Roles"
   - Right-click → Create → Login/Group Role
   - General tab:
     - Name: `booking_user`
   - Definition tab:
     - Password: `booking_dev_pass`
   - Privileges tab:
     - ✓ Can login
     - ✓ Superuser (or just for dev simplicity)
   - Click "Save"

5. **Grant Permissions**
   - Right-click `booking_db` → Properties
   - Security tab → Add
   - Grantee: `booking_user`
   - Privileges: ALL
   - Click "Save"

#### Method B: Using SQL Shell (psql)

1. **Find psql.exe**
   - Likely at: `C:\Program Files\PostgreSQL\17\bin\psql.exe`
   - Or search Windows for "SQL Shell (psql)"

2. **Run these commands**:
   ```sql
   CREATE DATABASE booking_db;
   CREATE USER booking_user WITH PASSWORD 'booking_dev_pass';
   GRANT ALL PRIVILEGES ON DATABASE booking_db TO booking_user;
   \c booking_db
   GRANT ALL ON SCHEMA public TO booking_user;
   ALTER DATABASE booking_db OWNER TO booking_user;
   ```

#### Method C: Use Default Postgres User (Quickest)

1. **Update `.env` file** in `d:\nbne-booking-django\.env`:
   ```env
   DB_NAME=booking_db
   DB_USER=postgres
   DB_PASSWORD=YOUR_POSTGRES_PASSWORD_HERE
   DB_HOST=localhost
   DB_PORT=5432
   ```

2. **Create database only** (using pgAdmin or psql):
   ```sql
   CREATE DATABASE booking_db;
   ```

### Step 2: Run Django Migrations

Once database is set up:

```bash
cd d:\nbne-booking-django
python manage.py migrate
python manage.py seed_config
python manage.py createsuperuser
python manage.py runserver
```

### Step 3: Verify

- Visit: http://localhost:8000
- Health check: http://localhost:8000/health/
- Admin: http://localhost:8000/admin/

## Troubleshooting

### "password authentication failed"
- Check `.env` file has correct password
- Verify user exists in PostgreSQL
- Try using `postgres` superuser instead

### "psql: command not found"
- Add PostgreSQL bin to PATH: `C:\Program Files\PostgreSQL\17\bin`
- Or use pgAdmin instead

### "database does not exist"
- Create database first using pgAdmin or psql
- Database name must match `.env` DB_NAME

## Current Configuration

From `.env` file:
- Database: `booking_db`
- User: `booking_user`
- Password: `booking_dev_pass`
- Host: `localhost`
- Port: `5432`

Change these if needed to match your PostgreSQL setup.
