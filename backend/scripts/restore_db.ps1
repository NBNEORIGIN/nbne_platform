# PostgreSQL Database Restore Script for Windows
# Usage: .\scripts\restore_db.ps1 <backup_file>

param(
    [Parameter(Mandatory=$true)]
    [string]$BackupFile
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $BackupFile)) {
    Write-Host "❌ Error: Backup file not found: $BackupFile" -ForegroundColor Red
    Write-Host ""
    Write-Host "Available backups:" -ForegroundColor Yellow
    Get-ChildItem .\backups\ -Filter "*.zip" | Format-Table Name, Length, LastWriteTime
    exit 1
}

Write-Host "⚠️  WARNING: This will REPLACE the current database!" -ForegroundColor Yellow
Write-Host "Backup file: $BackupFile" -ForegroundColor Cyan
$confirm = Read-Host "Continue? (yes/no)"

if ($confirm -ne "yes") {
    Write-Host "❌ Restore cancelled" -ForegroundColor Red
    exit 0
}

Write-Host "🔄 Starting database restore..." -ForegroundColor Cyan

# Read .env file
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

# Decompress if needed
$tempFile = "$env:TEMP\restore_$(Get-Date -Format 'yyyyMMddHHmmss').sql"

if ($BackupFile -match '\.zip$') {
    Write-Host "📦 Decompressing backup..." -ForegroundColor Yellow
    Expand-Archive -Path $BackupFile -DestinationPath $env:TEMP -Force
    $sqlFile = Get-ChildItem "$env:TEMP\*.sql" | Select-Object -First 1
    Copy-Item $sqlFile.FullName $tempFile
} else {
    $tempFile = $BackupFile
}

# Find psql.exe
$psqlPaths = @(
    "C:\Program Files\PostgreSQL\17\bin\psql.exe",
    "C:\Program Files\PostgreSQL\16\bin\psql.exe",
    "C:\Program Files\PostgreSQL\15\bin\psql.exe"
)

$psql = $null
foreach ($path in $psqlPaths) {
    if (Test-Path $path) {
        $psql = $path
        break
    }
}

if (-not $psql) {
    Write-Host "❌ Error: psql.exe not found" -ForegroundColor Red
    exit 1
}

# Set password environment variable
$env:PGPASSWORD = $dbPassword

try {
    # Restore database
    Write-Host "📥 Restoring database..." -ForegroundColor Yellow
    Get-Content $tempFile | & $psql -h $dbHost -p $dbPort -U $dbUser -d $dbName
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Restore failed!" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "✅ Database restored successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "1. python manage.py migrate"
    Write-Host "2. python manage.py runserver"
    
} finally {
    # Cleanup
    if ($tempFile -ne $BackupFile) {
        Remove-Item $tempFile -ErrorAction SilentlyContinue
    }
    Remove-Item Env:\PGPASSWORD -ErrorAction SilentlyContinue
}
