# Lumiere Frontend Deployment Guide

## Overview

The Lumiere frontend is a Next.js 15 application deployed on Vercel with automatic deployments from GitHub.

- **Production URL**: https://lumiere.trade
- **Framework**: Next.js 15.2.4 (App Router)
- **Hosting**: Vercel
- **Domain**: lumiere.trade (Namecheap)
- **Repository**: https://github.com/lumiere-trade/lumiere-public
- **Root Directory**: `frontend/`

---

## Architecture
```
lumiere-public/              # Monorepo root
├── frontend/                # Next.js application
│   ├── app/                 # Next.js App Router pages
│   ├── components/          # React components
│   ├── lib/                 # Utilities
│   ├── hooks/               # Custom React hooks
│   ├── public/              # Static assets
│   └── package.json         # Dependencies
├── pourtier/                # Backend API
├── courier/                 # WebSocket service
├── passeur/                 # Blockchain bridge
└── shared/                  # Shared utilities
```

---

## Prerequisites

- **Node.js**: 18.17.0 or higher
- **npm**: 9.0.0 or higher
- **Git**: For version control
- **Vercel CLI**: `npm install -g vercel` (optional)
- **GitHub Account**: For repository access
- **Vercel Account**: For deployments
- **Domain Access**: Namecheap for DNS configuration

---

## Initial Setup (Already Completed)

### 1. Project Structure

The frontend code is located in the `frontend/` subdirectory of the monorepo:
```bash
cd ~/lumiere/lumiere-public/frontend
```

### 2. Dependencies Installation

React 19 compatibility requires legacy peer deps:
```bash
# Install with legacy peer deps
npm install --legacy-peer-deps

# Or use the .npmrc configuration (already present)
# cat .npmrc
# legacy-peer-deps=true
```

### 3. Local Development
```bash
# Start development server
npm run dev

# Access at http://localhost:3000
```

### 4. Production Build (Local)
```bash
# Build for production
npm run build

# Start production server
npm run start

# Access at http://localhost:3000
```

---

## Vercel Deployment

### GitHub Integration

The project is connected to GitHub for automatic deployments:

- **Repository**: `lumiere-trade/lumiere-public`
- **Branch**: `main`
- **Auto-deploy**: Enabled on push to main

### Vercel Project Configuration

**Project Settings** (https://vercel.com/mitevvladimir-4333s-projects/lumiere/settings):

- **Root Directory**: `frontend`
- **Framework**: Next.js (auto-detected)
- **Build Command**: `npm run build` (auto-detected)
- **Install Command**: `npm install` (auto-detected)
- **Output Directory**: `.next` (auto-detected)
- **Node.js Version**: 18.x (default)

**Include files outside root directory**: Enabled ✓

This allows the build to access files from parent directories if needed.

### Environment Variables

Currently no environment variables are configured in production.

**To add environment variables:**

1. Go to: https://vercel.com/mitevvladimir-4333s-projects/lumiere/settings/environment-variables
2. Add variables prefixed with `NEXT_PUBLIC_` for client-side access
3. Redeploy for changes to take effect

**Planned environment variables:**
```bash
NEXT_PUBLIC_API_URL=https://api.lumiere.trade
NEXT_PUBLIC_WS_URL=wss://ws.lumiere.trade
NEXT_PUBLIC_BRIDGE_URL=https://bridge.lumiere.trade
NEXT_PUBLIC_SOLANA_NETWORK=mainnet-beta
NEXT_PUBLIC_SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
```

---

## Deployment Workflow

### Automatic Deployment (Recommended)

Every push to `main` branch triggers automatic deployment:
```bash
# 1. Make changes
cd ~/lumiere/lumiere-public/frontend
# Edit files...

# 2. Commit changes
git add .
git commit -m "feat: add new feature"

# 3. Push to GitHub
git push origin main

# 4. Vercel automatically:
#    - Detects the push
#    - Runs build in Vercel infrastructure
#    - Deploys to production if successful
#    - Updates lumiere.trade DNS
```

**Timeline:**
- Push detected: ~5 seconds
- Build starts: ~10 seconds
- Build completes: ~1-2 minutes
- Deployment live: ~30 seconds after build
- **Total time**: ~2-3 minutes from push to live

**Build logs available at:**
https://vercel.com/mitevvladimir-4333s-projects/lumiere

### Manual Deployment via CLI
```bash
cd ~/lumiere/lumiere-public/frontend

# Deploy to production
vercel --prod

# Follow prompts if first time:
# - Link to existing project: Yes
# - Select project: lumiere
```

### Preview Deployments

Every branch and pull request gets a unique preview URL:
```bash
# Create feature branch
git checkout -b feature/new-component

# Make changes and push
git push origin feature/new-component

# Vercel creates preview URL:
# https://lumiere-git-feature-new-component-[hash].vercel.app
```

---

## Custom Domain Configuration

### Domain: lumiere.trade

**DNS Records (Namecheap):**
```
Type    Host    Value                   TTL
----    ----    -----                   ---
A       @       76.76.21.21             Automatic
CNAME   www     cname.vercel-dns.com    Automatic
```

**SSL Certificate:**
- Automatically provisioned by Vercel (Let's Encrypt)
- Auto-renewal enabled
- HTTPS enforced

**Configuration steps (already completed):**

1. In Vercel Dashboard → Domains
2. Add domain: `lumiere.trade`
3. Vercel provides DNS records
4. Configure records in Namecheap
5. Wait for DNS propagation (5-30 minutes)
6. SSL certificate auto-provisioned

**Verification:**
```bash
# Check DNS resolution
dig lumiere.trade +short
# Should return: 76.76.21.21

# Check HTTPS
curl -I https://lumiere.trade
# Should return: HTTP/2 200
```

---

## Important Configuration Files

### `.npmrc`

Forces npm to use legacy peer deps (required for React 19):
```
legacy-peer-deps=true
```

**Location**: `frontend/.npmrc`

### Root `.gitignore`

Important exception for frontend:
```gitignore
# Python lib/ directories are ignored
lib/
lib64/

# BUT frontend/lib/ must be included
!frontend/lib/
```

This ensures `frontend/lib/utils.ts` is committed to git.

### `tsconfig.json`

Path aliases configuration:
```json
{
  "compilerOptions": {
    "paths": {
      "@/*": ["./*"]
    }
  }
}
```

Allows imports like: `import { cn } from "@/lib/utils"`

---

## Troubleshooting

### Build Fails: "Module not found: Can't resolve '@/lib/utils'"

**Cause**: `frontend/lib/` directory not committed to git

**Fix**:
```bash
# Check if lib/ is ignored
git check-ignore frontend/lib

# If ignored, add exception to root .gitignore
echo "!frontend/lib/" >> .gitignore

# Force add the directory
git add -f frontend/lib/
git commit -m "fix: include frontend/lib in git"
git push origin main
```

### Build Fails: "ERESOLVE unable to resolve dependency tree"

**Cause**: React 19 peer dependency conflicts

**Fix**:
```bash
# Ensure .npmrc exists in frontend/
cat > frontend/.npmrc << 'EOF'
legacy-peer-deps=true
