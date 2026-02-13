# pgAdmin 4 Setup Guide

## Step-by-Step Database Setup

### Step 1: Connect to PostgreSQL Server

1. In pgAdmin's **Object Explorer** (left panel), expand **Servers**
2. You should see your PostgreSQL 17 server
3. If prompted for password, enter your postgres password
4. The server should now be connected (green icon)

### Step 2: Create Database

1. **Right-click** on **Databases** (under your server)
2. Select **Create** → **Database...**
3. In the dialog:
   - **General** tab:
     - Database: `booking_db`
     - Owner: `postgres` (we'll change this later)
   - Click **Save**

### Step 3: Create User

1. **Right-click** on **Login/Group Roles** (under your server)
2. Select **Create** → **Login/Group Role...**
3. In the dialog:
   - **General** tab:
     - Name: `booking_user`
   - **Definition** tab:
     - Password: `booking_dev_pass`
     - Password expiration: (leave blank)
   - **Privileges** tab:
     - ✓ Can login? **YES**
     - ✓ Superuser? **NO** (not needed)
     - ✓ Create roles? **NO**
     - ✓ Create databases? **NO**
     - ✓ Inherit rights from parent roles? **YES**
   - Click **Save**

### Step 4: Grant Permissions

1. **Right-click** on the `booking_db` database
2. Select **Properties**
3. Go to **Security** tab
4. Click the **+** button to add a privilege
5. In the dialog:
   - Grantee: `booking_user`
   - Privileges:
     - ✓ Connect
     - ✓ Create
     - ✓ Temporary
   - Click **Save**

### Step 5: Grant Schema Permissions

1. Expand `booking_db` → **Schemas**
2. **Right-click** on **public** schema
3. Select **Properties**
4. Go to **Security** tab
5. Click **+** to add privilege
6. In the dialog:
   - Grantee: `booking_user`
   - Privileges:
     - ✓ Usage
     - ✓ Create
   - Click **Save**

### Step 6: Make booking_user the Owner (Optional but Recommended)

1. **Right-click** on `booking_db` database
2. Select **Properties**
3. **General** tab:
   - Owner: Change from `postgres` to `booking_user`
4. Click **Save**

## Verify Setup

### Using pgAdmin Query Tool

1. **Right-click** on `booking_db`
2. Select **Query Tool**
3. Run this query to verify:
```sql
SELECT current_database(), current_user;
```

Should show: `booking_db` and `postgres` (or `booking_user` if you switched)

### Test Connection from Django

Open PowerShell in `d:\nbne-booking-django` and run:

```powershell
python -c "import psycopg2; conn = psycopg2.connect('dbname=booking_db user=booking_user password=booking_dev_pass host=localhost'); print('✅ Connection successful!'); conn.close()"
```

If successful, proceed with Django migrations:

```powershell
python manage.py migrate
python manage.py seed_config
python manage.py createsuperuser
python manage.py runserver
```

## Troubleshooting

### "password authentication failed"

**Solution 1**: Check pg_hba.conf
1. In pgAdmin, go to **File** → **Preferences** → **Paths** → **Binary paths**
2. Note the PostgreSQL bin path
3. Navigate to PostgreSQL data directory (usually `C:\Program Files\PostgreSQL\17\data`)
4. Edit `pg_hba.conf`
5. Find lines with `127.0.0.1/32` and `::1/128`
6. Change method from `scram-sha-256` to `md5` or `trust` (for local dev only)
7. Restart PostgreSQL service

**Solution 2**: Use postgres superuser
1. Update `.env` file:
   ```
   DB_USER=postgres
   DB_PASSWORD=your_postgres_password
   ```
2. Just create the database, no need for separate user

### "database does not exist"

Make sure you created `booking_db` in Step 2

### "permission denied for schema public"

Make sure you completed Step 5 (grant schema permissions)

## Quick Summary

**What you created**:
- Database: `booking_db`
- User: `booking_user`
- Password: `booking_dev_pass`
- Permissions: Full access to `booking_db`

**Next**: Run Django migrations to create tables!
