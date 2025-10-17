# Private PyPI Registry

## Overview

Lumiere uses a private PyPI registry for internal packages like `shared`.

**Registry URL:** `http://localhost:9001/simple/`

## Architecture
```
Nginx (port 9001)
  └─ /var/www/pypi/simple/
      ├─ index.html (package list)
      └─ shared/
          ├─ index.html (version list)
          ├─ shared-0.1.0.tar.gz
          └─ shared-0.1.0-py3-none-any.whl
```

## Publishing a New Version of Shared

### 1. Update Version

Edit `shared/pyproject.toml`:
```toml
version = "0.1.1"  # Increment version
```

### 2. Build Package
```bash
cd ~/lumiere/lumiere-public/shared
rm -rf dist/ build/ *.egg-info
python -m build
```

### 3. Publish to Registry
```bash
# Copy built packages
cp dist/* /var/www/pypi/simple/shared/

# Update index.html
cat > /var/www/pypi/simple/shared/index.html << 'HTML'
<!DOCTYPE html>
<html>
<head>
    <title>Links for shared</title>
</head>
<body>
    <h1>Links for shared</h1>
    <a href="shared-0.1.0-py3-none-any.whl">shared-0.1.0-py3-none-any.whl</a><br/>
    <a href="shared-0.1.0.tar.gz">shared-0.1.0.tar.gz</a><br/>
    <a href="shared-0.1.1-py3-none-any.whl">shared-0.1.1-py3-none-any.whl</a><br/>
    <a href="shared-0.1.1.tar.gz">shared-0.1.1.tar.gz</a><br/>
</body>
</html>
HTML
```

### 4. Update Components

Update `pyproject.toml` in components:
```toml
dependencies = [
    "shared==0.1.1",  # Update version
    ...
]
```

### 5. Rebuild Docker Images
```bash
cd courier/
make build-dev
make build-prod
```

## Using Registry in Development

### Local Development (editable install)
```bash
# Install shared locally
cd shared/
pip install -e .

# Install component
cd ../courier/
pip install -e .
```

### Docker Build

Docker automatically uses registry via `--extra-index-url`:
```dockerfile
RUN pip install --extra-index-url http://host.docker.internal:9001/simple/ \
    --trusted-host host.docker.internal .
```

## Registry Management

### Check Available Packages
```bash
pip index versions shared --index-url http://localhost:9001/simple/
```

### View Registry in Browser
```bash
# Open in browser
xdg-open http://localhost:9001/simple/
```

### Nginx Configuration

Location: `/etc/nginx/sites-available/pypi`
```nginx
server {
    listen 9001;
    server_name localhost;
    root /var/www/pypi;
    autoindex on;
}
```

### Restart Nginx
```bash
sudo systemctl restart nginx
```

## Troubleshooting

### Docker can't reach registry

Add to docker build:
```bash
--add-host host.docker.internal:host-gateway
```

### Package not found

1. Check registry is running: `curl http://localhost:9001/simple/`
2. Check package exists: `ls /var/www/pypi/simple/shared/`
3. Check index.html is updated
4. Rebuild Docker without cache: `--no-cache`

### Version conflict
```bash
# Clear pip cache
pip cache purge

# Rebuild package
cd shared/ && python -m build
```

## Security Notes

- Registry is on localhost only (not exposed externally)
- No authentication (internal use only)
- For production: add Nginx basic auth or VPN

## Port Allocation

See [PORTS.md](PORTS.md) for complete port list.

- **9001**: PyPI Registry (Nginx)
