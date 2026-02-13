# PostgreSQL Database Backup Script for Windows
# Usage: .\scripts\backup_db.ps1 [backup_name]

param(
    [string]$BackupName = "backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
)

$ErrorActionPreference = "Stop"

# Configuration
$BackupDir = ".\backups"
$BackupFile = "$BackupDir\$BackupName.sql"
$CompressedFile = "$BackupFile.zip"

# Ensure backup directory exists
New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null

Write-Host "🔄 Starting database backup..." -ForegroundColor Cyan

# Read .env file for database credentials
$envContent = Get-Content .env -ErrorAction SilentlyContinue
if (-not $envContent) {
    Write-Host "❌ Error: .env file not found" -ForegroundColor Red
    exit 1
}

$dbName = ($envContent | Where-Object { $_ -match '^DB_NAME=' }) -replace 'DB_NAME=', ''
$dbUser = ($envContent | Where-Object { $_ -match '^DB_USER=' }) -replace 'DB_USER=', ''
$dbPassword = ($envContent | Where-Object { $_ -match '^DB_PASSWORD=' }) -replace 'DB_PASSWORD=', ''
$dbHost = ($envContent | Where-Object { $_ -match '^DB_HOST=' }) -replace 'DB_HOST=', '' -replace 'localhost', '127.0.0.1'
$dbPort = ($envContent | Where-Object { $_ -match '^DB_PORT=' }) -replace 'DB_PORT=', ''

if (-not $dbName) {
    Write-Host "❌ Error: Database configuration not found in .env" -ForegroundColor Red
    exit 1
}

Write-Host "📦 Dumping database: $dbName..." -ForegroundColor Yellow

# Find pg_dump.exe
$pgDumpPaths = @(
    "C:\Program Files\PostgreSQL\17\bin\pg_dump.exe",
    "C:\Program Files\PostgreSQL\16\bin\pg_dump.exe",
    "C:\Program Files\PostgreSQL\15\bin\pg_dump.exe"
)

$pgDump = $null
foreach ($path in $pgDumpPaths) {
    if (Test-Path $path) {
        $pgDump = $path
        break
    }
}

if (-not $pgDump) {
    Write-Host "❌ Error: pg_dump.exe not found" -ForegroundColor Red
    Write-Host "Please install PostgreSQL or add it to PATH" -ForegroundColor Yellow
    exit 1
}

# Set password environment variable
$env:PGPASSWORD = $dbPassword

try {
    # Create backup
    & $pgDump -h $dbHost -p $dbPort -U $dbUser -d $dbName --clean --if-exists -f $BackupFile
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Backup failed!" -ForegroundColor Red
        exit 1
    }
    
    # Compress backup
    Write-Host "🗜️  Compressing backup..." -ForegroundColor Yellow
    Compress-Archive -Path $BackupFile -DestinationPath $CompressedFile -Force
    Remove-Item $BackupFile
    
    $size = (Get-Item $CompressedFile).Length / 1MB
    Write-Host "📊 Backup size: $([math]::Round($size, 2)) MB" -ForegroundColor Green
    Write-Host "✅ Backup complete: $CompressedFile" -ForegroundColor Green
    
} finally {
    # Clear password from environment
    Remove-Item Env:\PGPASSWORD -ErrorAction SilentlyContinue
}
