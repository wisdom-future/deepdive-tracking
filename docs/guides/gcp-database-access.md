# GCP Cloud SQL Database Access Guide

## Overview

This guide explains how to configure and access the Cloud SQL database using username/password authentication instead of gcloud CLI.

## Current Setup

Our database is deployed on Google Cloud SQL as a PostgreSQL 15 instance, and the application uses Cloud SQL Connector for secure authentication in Cloud Run environments.

## Database Connection Methods

### Method 1: Cloud Console (Easiest - Web Browser)

The quickest way to view your database in real-time without any installation.

1. **Go to Cloud Console**
   - Visit: https://console.cloud.google.com/
   - Select your GCP project

2. **Navigate to Cloud SQL**
   - Click on the navigation menu (≡) in the top-left
   - Search for "Cloud SQL"
   - Click on "Cloud SQL Instances"

3. **Find Your Instance**
   - Look for your database instance (usually named something like `deepdive-tracking-db`)
   - Click on it to view details

4. **Manage Connections**
   - In the instance details, click "CONNECTIONS" tab
   - Ensure "Public IP" is configured and authorized
   - Check if your IP is in the authorized networks list

5. **View Data with Cloud SQL Editor**
   - In the instance details, click "DATABASES" tab
   - Click on your database name
   - You can now view tables and run SQL queries directly in the browser

---

## Method 2: Database-Specific IAM User (Username/Password)

For programmatic access or desktop clients, create a database user with username and password.

### Step 1: Create a Database User in Cloud Console

1. **Go to Cloud SQL Instance**
   - https://console.cloud.google.com/sql
   - Select your instance

2. **Create a New User**
   - Click on the "USERS" tab
   - Click "+ CREATE ACCOUNT"
   - Fill in the form:
     - **User type**: Choose "Cloud SQL user" (not Cloud IAM)
     - **Username**: Example: `deepdive_viewer` or `deepdive_editor`
     - **Password**: Choose a strong password (20+ characters recommended)
     - Click "CREATE"

3. **Note Down Credentials**
   - Username: (you just created it)
   - Password: (you just set it)
   - Host: Check your instance's "PUBLIC IP" address
   - Port: 5432 (default PostgreSQL)
   - Database: `deepdive_tracking` (or your database name)

### Step 2: Configure Network Access

**Important**: Your Cloud SQL instance must have a public IP and allow connections from your network.

1. **Check Public IP Configuration**
   - Go to your Cloud SQL instance details
   - Click "CONNECTIONS" tab
   - Verify "Public IP" has an address assigned
   - If not: Click "ADD NETWORK" and add your IP

2. **Add Your IP to Authorized Networks**
   - In CONNECTIONS tab, find "Authorized networks"
   - Click "EDIT" (pencil icon)
   - Add your IP address:
     - Find your IP: https://whatismyipaddress.com/
     - Format: `YOUR_IP/32` (example: `203.0.113.42/32`)
     - Or use `0.0.0.0/0` to allow all (less secure)
   - Click "SAVE"

### Step 3: Test Connection with psql CLI

**If you have PostgreSQL client installed:**

```bash
psql -h <PUBLIC_IP> \
     -U <USERNAME> \
     -d deepdive_tracking \
     -W

# When prompted, enter your password
# Example:
# psql -h 34.125.200.50 -U deepdive_viewer -d deepdive_tracking -W
```

**On Windows (PowerShell):**
```powershell
$env:PGPASSWORD = "your_password"
psql -h 34.125.200.50 -U deepdive_viewer -d deepdive_tracking
```

---

## Method 3: DBeaver (Graphical Client)

A popular free database client for browsing and querying.

### Install DBeaver

1. Download from: https://dbeaver.io/download/
2. Install and launch

### Configure Connection

1. **Create New Connection**
   - File → New → Database Connection
   - Select "PostgreSQL" → Next

2. **Enter Credentials**
   - **Server Host**: Your Cloud SQL PUBLIC IP (from Cloud Console)
   - **Port**: 5432
   - **Database**: `deepdive_tracking`
   - **Username**: Your database user (e.g., `deepdive_viewer`)
   - **Password**: Your database password
   - Check "Save password locally"

3. **Test Connection**
   - Click "Test Connection..."
   - If successful, click "Finish"

4. **Browse Database**
   - Expand your connection in the left panel
   - Navigate: Databases → deepdive_tracking → Tables
   - View your tables: `raw_news`, `processed_news`, etc.

---

## Method 4: Cloud SQL Proxy (Secure Local Tunnel)

For maximum security without exposing the database publicly.

### Install Cloud SQL Proxy

**macOS:**
```bash
curl -o cloud-sql-proxy https://dl.google.com/cloudsql/cloud_sql_proxy.macosx.amd64
chmod +x cloud-sql-proxy
./cloud-sql-proxy
```

**Windows:** Download from Google Cloud docs or use:
```powershell
choco install cloud-sql-proxy  # if using Chocolatey
```

**Linux:**
```bash
curl -o cloud-sql-proxy https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64
chmod +x cloud-sql-proxy
```

### Start Proxy

Get your instance connection name from Cloud Console (format: `PROJECT:REGION:INSTANCE`):

```bash
./cloud-sql-proxy instances/PROJECT:REGION:INSTANCE --port=5432
```

This creates a local tunnel. Then connect with:
```bash
psql -h localhost -U deepdive_viewer -d deepdive_tracking -W
```

---

## Common Connection Issues

### "Connection refused"
- Check if Public IP is configured on the instance
- Verify your IP is in the authorized networks list
- Ensure Cloud SQL Admin API is enabled in GCP

### "Authentication failed"
- Double-check username and password
- Confirm you created a "Cloud SQL user", not "Cloud IAM user"

### "Network error"
- Cloud SQL instance might not be running
- Firewall might be blocking port 5432
- Try using Cloud SQL Proxy for more reliable connection

---

## Database Structure

### Key Tables

**raw_news**
- Stores original article data collected from RSS feeds
- Fields: id, title, url, content, published_at, source_name, etc.

**processed_news**
- Stores AI-evaluated articles with scores and summaries
- Fields: raw_news_id, score (0-100), category, summary_pro, summary_sci, keywords, etc.

### Example Queries

View top 10 scoring articles:
```sql
SELECT
    r.title,
    p.score,
    p.category,
    r.source_name
FROM processed_news p
JOIN raw_news r ON p.raw_news_id = r.id
ORDER BY p.score DESC
LIMIT 10;
```

Count articles by category:
```sql
SELECT category, COUNT(*) as count
FROM processed_news
GROUP BY category
ORDER BY count DESC;
```

---

## Environment Variables

If you want to configure these in code:

```bash
export DEEPDIVE_DB_HOST="34.125.200.50"
export DEEPDIVE_DB_PORT="5432"
export DEEPDIVE_DB_USER="deepdive_viewer"
export DEEPDIVE_DB_PASSWORD="your_secure_password"
export DEEPDIVE_DB_NAME="deepdive_tracking"
```

---

## Security Best Practices

1. **Use Strong Passwords**: 20+ characters with mixed case, numbers, and symbols
2. **Limit Network Access**: Only add necessary IPs to authorized networks
3. **Use Different Users for Different Purposes**:
   - `deepdive_viewer`: Read-only access (better for automated tools)
   - `deepdive_editor`: Read-write access (for maintenance)
4. **Enable SSL**: When available, always use encrypted connections
5. **Rotate Passwords**: Change them periodically
6. **Never Commit Passwords**: Use environment variables, not hardcoded credentials

---

## Quick Reference

| Component | Value |
|-----------|-------|
| **Service** | Google Cloud SQL |
| **Database Type** | PostgreSQL 15 |
| **Port** | 5432 |
| **Region** | (Check your GCP project) |
| **Public IP** | (Check Cloud Console) |
| **Database Name** | deepdive_tracking |
| **Default Port** | 5432 |

---

## Need Help?

- Check Cloud SQL documentation: https://cloud.google.com/sql/docs
- View instance logs in Cloud Console
- Contact your GCP administrator for network/permission issues
