#!/bin/bash
# Initial server setup for Hetzner CX41
# Run as root on a fresh Ubuntu 24.04 LTS server
# Usage: curl -sSL <raw-github-url> | bash

set -euo pipefail

echo "═══════════════════════════════════════════════"
echo "  NBNE Platform — Server Setup"
echo "═══════════════════════════════════════════════"

# --- System updates ---
echo "📦 Updating system packages..."
apt-get update && apt-get upgrade -y

# --- Install Docker ---
echo "🐳 Installing Docker..."
if ! command -v docker &>/dev/null; then
  curl -fsSL https://get.docker.com | sh
  systemctl enable docker
  systemctl start docker
fi
docker --version

# --- Install Docker Compose (plugin) ---
echo "🐳 Verifying Docker Compose..."
docker compose version

# --- Install Nginx ---
echo "🌐 Installing Nginx..."
apt-get install -y nginx
systemctl enable nginx

# --- Install UFW firewall ---
echo "🔒 Configuring firewall..."
apt-get install -y ufw
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP (redirect to HTTPS)
ufw allow 443/tcp   # HTTPS
echo "y" | ufw enable
ufw status

# --- Create directory structure ---
echo "📁 Creating directory structure..."
mkdir -p /opt/nbne/{shared,instances,backups}
mkdir -p /opt/nbne/scripts
mkdir -p /etc/ssl/cloudflare
mkdir -p /etc/nginx/sites-enabled

# --- Configure Nginx base ---
cat > /etc/nginx/nginx.conf <<'NGINX'
user www-data;
worker_processes auto;
pid /run/nginx.pid;
include /etc/nginx/modules-enabled/*.conf;

events {
    worker_connections 1024;
}

http {
    sendfile on;
    tcp_nopush on;
    types_hash_max_size 2048;
    client_max_body_size 50M;

    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging
    access_log /var/log/nginx/access.log;
    error_log /var/log/nginx/error.log;

    # Gzip
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml text/javascript;

    # Timeouts
    proxy_connect_timeout 60s;
    proxy_send_timeout 120s;
    proxy_read_timeout 120s;

    # Per-client site configs
    include /etc/nginx/sites-enabled/*.conf;
}
NGINX

# --- Clone repo ---
echo "📥 Cloning repository..."
if [ ! -d /opt/nbne/shared/.git ]; then
  git clone https://github.com/NBNEORIGIN/nbne_platform.git /opt/nbne/shared
else
  cd /opt/nbne/shared && git pull origin main
fi

# --- Copy scripts ---
echo "📋 Installing management scripts..."
cp /opt/nbne/shared/docker/scripts/*.sh /opt/nbne/scripts/
chmod +x /opt/nbne/scripts/*.sh

# --- Set up daily backup cron ---
echo "⏰ Setting up daily backup cron..."
(crontab -l 2>/dev/null | grep -v nbne-backup; echo "0 3 * * * /opt/nbne/scripts/backup.sh >> /var/log/nbne-backup.log 2>&1") | crontab -

# --- Reminder for manual steps ---
echo ""
echo "═══════════════════════════════════════════════"
echo "✅ Server setup complete!"
echo ""
echo "  Manual steps remaining:"
echo "  1. Upload Cloudflare Origin Certificate:"
echo "     /etc/ssl/cloudflare/origin.pem"
echo "     /etc/ssl/cloudflare/origin-key.pem"
echo ""
echo "  2. Create first client:"
echo "     /opt/nbne/scripts/new-client.sh salon-x salon-x.nbne.uk 3001 8001"
echo ""
echo "  3. Point DNS (Cloudflare) A record → $(curl -s ifconfig.me)"
echo ""
echo "  Available commands:"
echo "    /opt/nbne/scripts/new-client.sh <slug> <domain> <fe-port> <be-port>"
echo "    /opt/nbne/scripts/deploy.sh [slug]"
echo "    /opt/nbne/scripts/backup.sh"
echo "    /opt/nbne/scripts/status.sh"
echo "═══════════════════════════════════════════════"
