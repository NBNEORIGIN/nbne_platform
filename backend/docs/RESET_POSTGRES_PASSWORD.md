# Reset PostgreSQL Password on Windows

## Method 1: Using pg_hba.conf (Recommended)

1. **Find PostgreSQL data directory**:
   - Usually: `C:\Program Files\PostgreSQL\17\data`

2. **Edit pg_hba.conf**:
   - Open `C:\Program Files\PostgreSQL\17\data\pg_hba.conf` in Notepad (as Administrator)
   - Find these lines near the bottom:
     ```
     # IPv4 local connections:
     host    all             all             127.0.0.1/32            scram-sha-256
     # IPv6 local connections:
     host    all             all             ::1/128                 scram-sha-256
     ```
   - Change `scram-sha-256` to `trust`:
     ```
     host    all             all             127.0.0.1/32            trust
     host    all             all             ::1/128                 trust
     ```
   - Save the file

3. **Restart PostgreSQL**:
   - Open Services (Win+R, type `services.msc`)
   - Find "postgresql-x64-17"
   - Right-click → Restart

4. **Connect without password**:
   - Close pgAdmin
   - Reopen pgAdmin
   - Connect to server (no password needed now)

5. **Set new password**:
   - In pgAdmin, right-click **Login/Group Roles** → **postgres** → **Properties**
   - **Definition** tab
   - Password: `postgres123`
   - Click **Save**

6. **Restore security**:
   - Edit `pg_hba.conf` again
   - Change `trust` back to `scram-sha-256`
   - Restart PostgreSQL service
   - Save the file

7. **Test new password**:
   - Disconnect and reconnect in pgAdmin
   - Use password: `postgres123`

## Method 2: Command Line (Simpler)

1. **Open Command Prompt as Administrator**

2. **Navigate to PostgreSQL bin**:
   ```cmd
   cd "C:\Program Files\PostgreSQL\17\bin"
   ```

3. **Connect as postgres**:
   ```cmd
   psql -U postgres
   ```
   (If it asks for password and you don't know it, use Method 1)

4. **Set new password**:
   ```sql
   ALTER USER postgres WITH PASSWORD 'postgres123';
   \q
   ```

## After Reset

Update Django `.env` file:
```
DB_PASSWORD=postgres123
```

Then run:
```bash
cd d:\nbne-booking-django
python manage.py migrate
```
