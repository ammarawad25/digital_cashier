# Deployment & Startup Guide

## Quick Start

### Prerequisites
- Node.js 16+ and npm 8+
- Backend API running on `http://localhost:8000`

### Setup & Run

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The application will be available at `http://localhost:3000`

## Development Workflow

### Standard Development Setup

```bash
# Terminal 1: Start backend API
cd src
python -m uvicorn main:app --reload --port 8000

# Terminal 2: Start frontend
cd frontend
npm run dev
```

Visit `http://localhost:3000` in your browser

### Testing During Development

```bash
# Run tests in watch mode (auto-rerun on file changes)
npm test

# Run E2E tests (requires backend API running)
npm run test:e2e

# Run with UI for better visibility
npm test:ui
npm run test:e2e:ui
```

## Building for Production

### Production Build

```bash
# Build optimized production bundle
npm run build

# Preview the production build locally
npm run preview
```

The optimized build will be in the `dist/` folder

### Build Output

```
dist/
├── index.html          # Main HTML entry point
├── assets/
│   ├── index-*.js      # JavaScript bundle (minified)
│   ├── index-*.css     # Styles (minified)
│   └── *.woff2         # Font files
└── vite.svg           # Favicon
```

## Deployment Options

### Option 1: Docker Deployment

Create `Dockerfile`:

```dockerfile
# Build stage
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Runtime stage
FROM node:18-alpine
WORKDIR /app
RUN npm install -g serve
COPY --from=builder /app/dist ./dist
EXPOSE 3000
CMD ["serve", "-s", "dist", "-l", "3000"]
```

Build and run:

```bash
# Build image
docker build -t customer-service-agent-frontend:latest .

# Run container
docker run -p 3000:3000 \
  -e VITE_API_URL=http://api.example.com \
  customer-service-agent-frontend:latest
```

### Option 2: Vercel Deployment

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
vercel

# Deploy to production
vercel --prod
```

Create `vercel.json`:

```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "env": {
    "VITE_API_URL": "@api_url"
  }
}
```

### Option 3: Netlify Deployment

```bash
# Install Netlify CLI
npm install -g netlify-cli

# Deploy
netlify deploy
```

Create `netlify.toml`:

```toml
[build]
  command = "npm run build"
  publish = "dist"

[dev]
  command = "npm run dev"
  port = 3000

[[redirects]]
  from = "/api/*"
  to = "http://api.example.com/:splat"
  status = 200
```

### Option 4: AWS S3 + CloudFront

```bash
# Build
npm run build

# Deploy to S3
aws s3 sync dist/ s3://my-bucket/

# Invalidate CloudFront cache
aws cloudfront create-invalidation \
  --distribution-id E1234567890ABC \
  --paths "/*"
```

### Option 5: Traditional Server (Nginx)

Create `nginx.conf`:

```nginx
server {
  listen 80;
  server_name example.com;
  root /var/www/customer-service-agent-frontend/dist;
  
  # Serve dist files
  location / {
    try_files $uri $uri/ /index.html;
  }
  
  # Proxy API requests
  location /api {
    proxy_pass http://backend-api:8000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection 'upgrade';
    proxy_set_header Host $host;
    proxy_cache_bypass $http_upgrade;
  }
  
  # Cache static assets
  location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
  }
}
```

## Environment Configuration

### Development

```bash
# .env.local (not committed to git)
VITE_API_URL=http://localhost:8000
```

### Production

Set environment variables in your deployment platform:

```
VITE_API_URL=https://api.example.com
```

## Performance Optimization

### Bundle Analysis

```bash
# Install bundle analyzer
npm install --save-dev @vitejs/plugin-inspect

# Analyze bundle
npm run build -- --analyze
```

### Enable Compression

For Nginx:

```nginx
gzip on;
gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
gzip_min_length 1000;
```

### Lazy Loading

The app already implements code splitting:
- Components are imported directly
- Only necesSARy code is loaded

### Caching Strategy

```nginx
# Cache busting for versioned assets
location ~* \.(js|css)$ {
  expires 1y;
  add_header Cache-Control "public, immutable";
}

# HTML should not be cached
location / {
  add_header Cache-Control "no-cache, no-store, must-revalidate";
}
```

## Monitoring & Troubleshooting

### Application Health Check

```bash
# Check if frontend is running
curl http://localhost:3000/

# Check if API is accessible
curl http://localhost:3000/api/conversation/health
```

### Common Issues

**Issue**: API requests return 404
- **Solution**: Ensure `VITE_API_URL` is correctly set
- Check that backend API is running on the configured port

**Issue**: Voice recording not working in production
- **Solution**: Use HTTPS (Web Audio API requires secure context)
- Check browser permissions for microphone access

**Issue**: High memory usage
- **Solution**: Rebuild with `npm run build`
- Check browser DevTools for memory leaks
- Clear browser cache

**Issue**: Slow page load
- **Solution**: Check bundle size: `npm run build`
- Use DevTools Lighthouse
- Enable gzip compression on server
- Configure CDN for static assets

### Logging & Analytics

Add to `src/main.jsx`:

```javascript
// Error tracking
if (import.meta.env.PROD) {
  window.addEventListener('error', (event) => {
    console.error('Runtime error:', event.error);
    // Send to error tracking service
  });
}

// Performance monitoring
if (window.performance && window.performance.timing) {
  window.addEventListener('load', () => {
    const perfData = window.performance.timing;
    const pageLoadTime = perfData.loadEventEnd - perfData.navigationStart;
    console.log('Page load time:', pageLoadTime, 'ms');
  });
}
```

## Scaling Considerations

### Load Balancing

```nginx
upstream frontend_servers {
  server frontend1:3000;
  server frontend2:3000;
  server frontend3:3000;
}

server {
  listen 80;
  location / {
    proxy_pass http://frontend_servers;
  }
}
```

### CDN Configuration

Use a CDN like Cloudflare or CloudFront for:
- Static asset caching
- Global distribution
- DDoS protection
- SSL/TLS termination

### Session Management

Sessions are stored in localStorage per browser:
- No server-side session needed
- Scales horizontally with no backend session management required

## Post-Deployment Checklist

- [ ] Frontend accessible at configured domain
- [ ] API URL correctly configured
- [ ] Voice recording works with HTTPS
- [ ] All tests passing
- [ ] Performance acceptable (<3s first paint)
- [ ] Error tracking configured
- [ ] Monitoring alerts set up
- [ ] Backup strategy in place
- [ ] Security headers configured
- [ ] CORS properly configured for API

## Rollback Procedure

### Docker

```bash
# Rollback to previous image
docker ps -a  # Find container ID
docker run -p 3000:3000 <previous-image-id>
```

### Traditional Server

```bash
# Keep backup of previous build
sudo cp -r dist dist.backup

# Rollback if needed
sudo rm -rf dist
sudo cp -r dist.backup dist
sudo systemctl restart nginx
```

## Support & Documentation

- Frontend README: `frontend/README.md`
- Testing Guide: `frontend/TESTING.md`
- API Documentation: Backend docs
- Issue Tracker: GitHub Issues

## Questions?

Refer to the main documentation or contact the development team.
