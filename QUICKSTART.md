# AI Tutor - Quick Start Guide

## Prerequisites
- Node.js 18+
- Python 3.9+
- Docker & Docker Compose (optional, for Redis)
- GEMINI_API_KEY environment variable

## Local Development

### 1. Install Dependencies

```bash
# Frontend
cd frontend
npm install

# Backend services
pip install -r requirements.txt
```

### 2. Start Redis (Optional - for caching)

```bash
# Using Docker Compose
docker-compose up redis -d

# Or install Redis locally
brew install redis  # macOS
redis-server
```

### 3. Start Services

```bash
# Terminal 1: Frontend (Development)
cd frontend
npm run dev

# Terminal 2: Teaching Assistant API
cd services/TeachingAssistant
python api.py

# Terminal 3: Tutor WebSocket Service
cd services/Tutor
npm install
node server.js
```

### 4. Access Application

- **Frontend**: http://localhost:5173
- **Teaching Assistant API**: http://localhost:8002
- **Tutor WebSocket**: ws://localhost:8767

## Production Build

### Build Frontend
```bash
cd frontend
npm run build
npm run preview  # Test production build
```

### Run Production Server
```bash
cd frontend
npm install compression express
node server.js
```

## Performance Testing

### Run Lighthouse CI
```bash
cd frontend
npm run perf:lighthouse
```

### Analyze Bundle Size
```bash
cd frontend
npm run perf:bundle
```

### Check Web Vitals
Open browser console at http://localhost:4173 and look for:
```
LCP: X.Xs
FID: XXms
CLS: 0.XX
```

## Docker Deployment

### Build and Run All Services
```bash
docker-compose up --build
```

### Run Specific Services
```bash
# Just Redis and Frontend
docker-compose up redis frontend

# All services
docker-compose up
```

## Environment Variables

Create a `.env` file in the root directory:

```bash
# Required
GEMINI_API_KEY=your_api_key_here

# Optional
REDIS_HOST=localhost
REDIS_PORT=6379
PORT=3000
TEACHING_ASSISTANT_PORT=8002
TUTOR_PORT=8767
```

## Troubleshooting

### Redis Connection Issues
```bash
# Check if Redis is running
redis-cli ping

# Should return: PONG
```

### Frontend Build Errors
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

### TypeScript Errors
The Perseus library has pre-existing type errors. These don't affect the build:
```bash
# Build still works
npm run build
```

## Performance Optimizations Enabled

✅ Code splitting & lazy loading
✅ Bundle optimization (vendor/genai/khan chunks)
✅ Gzip/Brotli compression
✅ Smart caching headers
✅ WebSocket compression
✅ API response caching (with Redis)
✅ Request timeouts & circuit breakers
✅ Web Vitals monitoring

## Next Steps

1. **Test the application** at http://localhost:4173
2. **Check performance metrics** in browser console
3. **Run Lighthouse tests** with `npm run perf:lighthouse`
4. **Review** `OPTIMIZATION_SUMMARY.md` for details

## Support

For issues or questions, check:
- `PERFORMANCE.md` - Performance monitoring guide
- `OPTIMIZATION_SUMMARY.md` - Detailed optimization breakdown
- `.github/workflows/performance.yml` - CI/CD configuration
