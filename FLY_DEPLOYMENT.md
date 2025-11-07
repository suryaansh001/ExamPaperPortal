# Fly.io Deployment Guide (Free Tier Available)

## Why Fly.io?
- ✅ Generous free tier (3 shared-cpu VMs)
- ✅ Global edge network
- ✅ No spin-down (always running)
- ✅ Free PostgreSQL database
- ✅ Fast deployments

## Step-by-Step Deployment

### 1. Install Fly CLI
```bash
# Windows (PowerShell)
iwr https://fly.io/install.ps1 -useb | iex

# Mac/Linux
curl -L https://fly.io/install.sh | sh
```

### 2. Sign Up & Login
```bash
fly auth signup
# Or if you have an account:
fly auth login
```

### 3. Create Fly App
```bash
cd ExamSystemBackend
fly launch
```

Follow prompts:
- App name: `paper-portal-backend` (or choose your own)
- Region: Choose closest to you
- PostgreSQL: Yes (creates free database)
- Redis: No (not needed)

### 4. Configure fly.toml
The `fly.toml` file will be created. Update it:

```toml
app = "your-app-name"
primary_region = "iad"  # Change to your region

[build]
  builder = "paketobuildpacks/builder:base"

[env]
  PORT = "8080"

[http_service]
  internal_port = 8080
  force_https = true
  auto_stop_machines = false
  auto_start_machines = true
  min_machines_running = 1
  processes = ["app"]

[[vm]]
  memory_mb = 256
  cpu_kind = "shared"
  cpus = 1
```

### 5. Set Secrets (Environment Variables)
```bash
# Generate secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Set secrets
fly secrets set SECRET_KEY="your-generated-secret-key"
fly secrets set RESEND_API_KEY="your-resend-key"
fly secrets set RESEND_FROM_EMAIL="your-email@domain.com"

# Database URL is automatically set as DATABASE_URL
```

### 6. Create Dockerfile (if needed)
Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create uploads directory
RUN mkdir -p uploads

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### 7. Deploy
```bash
fly deploy
```

### 8. Get Your URL
```bash
fly status
# Your app will be at: https://your-app-name.fly.dev
```

## Fly.io Free Tier
- ✅ 3 shared-cpu VMs (256MB RAM each)
- ✅ 3GB persistent volume storage
- ✅ 160GB outbound data transfer
- ✅ Free PostgreSQL (256MB)
- ✅ Always running (no spin-down)

## Upgrade Options
- **Hobby Plan**: For more resources
- **Production Plans**: For scaling

## Troubleshooting

### View Logs
```bash
fly logs
```

### SSH into VM
```bash
fly ssh console
```

### Check Status
```bash
fly status
fly apps list
```

### Restart App
```bash
fly apps restart your-app-name
```

## Database Access
```bash
# Connect to PostgreSQL
fly postgres connect -a your-db-name
```

