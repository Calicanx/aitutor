# Performance Monitoring & Optimization Guide

## Quick Start

### Run Performance Tests
```bash
# Build and analyze bundle size
npm run perf:bundle

# Run Lighthouse CI tests
npm run perf:lighthouse

# Build with analysis mode
npm run build:analyze
```

## Performance Budgets (Enforced in CI)

### Core Web Vitals Targets
- **LCP (Largest Contentful Paint)**: < 3.0s
- **FID (First Input Delay)**: < 100ms
- **CLS (Cumulative Layout Shift)**: < 0.1
- **FCP (First Contentful Paint)**: < 2.0s
- **TBT (Total Blocking Time)**: < 300ms

### Lighthouse Scores
- Performance: ≥ 80
- Accessibility: ≥ 90
- Best Practices: ≥ 90
- SEO: ≥ 90

### Bundle Size Limits
- Main bundle: < 500KB (gzipped)
- Vendor chunk: < 200KB (gzipped)
- Per-route chunks: < 100KB (gzipped)

## Implemented Optimizations

### Phase 1: Observability ✅
- [x] Web Vitals logging enabled (`reportWebVitals(console.log)`)
- [x] Lighthouse CI configuration added
- [ ] Centralized logging (TODO: Add Sentry/LogRocket)
- [ ] Synthetic journeys (TODO: Add Playwright tests)

### Phase 2: Frontend Foundations ✅
- [x] Code splitting (React.lazy for routes and heavy components)
- [x] Manual chunks (vendor, genai, khan libraries)
- [x] Terser minification with console/debugger removal
- [x] Font optimization (dns-prefetch, preconnect, display=swap)
- [x] Performance budgets in Lighthouse CI
- [ ] Image optimization (TODO: Convert to WebP/AVIF)
- [ ] CDN setup (TODO: Configure CloudFlare/AWS CloudFront)

### Phase 3: Backend/API Layer 🔄
- [x] WebSocket compression enabled
- [ ] API payload optimization (TODO: Review and reduce)
- [ ] Timeouts and circuit breakers (TODO: Add)
- [ ] Background job queues (TODO: Implement)

### Phase 4: Database 📋
- [ ] Query indexing audit
- [ ] Pagination standardization
- [ ] Redis caching layer
- [ ] Connection pooling optimization

### Phase 5: Real-time/WebRTC 🔄
- [x] Media processing optimization (direct video refs)
- [x] Volume update throttling (10 FPS)
- [ ] Adaptive bitrate
- [ ] Simulcast/SVC
- [ ] Event throttling/debouncing

### Phase 6: AI Services 📋
- [ ] Centralized AI service
- [ ] Response caching
- [ ] Quality tiers (fast/slow models)
- [ ] Rate limiting and quotas

### Phase 7: Infrastructure 🔄
- [x] Production server with compression
- [x] Cache headers for static assets
- [ ] HTTP/2 or HTTP/3
- [ ] Autoscaling configuration
- [ ] Blue-green deployments

### Phase 8: Testing & Governance 🔄
- [x] Performance test scripts added
- [ ] CI/CD integration
- [ ] Performance checklist
- [ ] Quarterly audit schedule

## Monitoring in Browser

### View Web Vitals
Open browser console and look for:
```
LCP: 2.1s
FID: 12ms
CLS: 0.05
```

### Check Bundle Sizes
```bash
npm run perf:bundle
```
This will generate a visual report of your bundle composition.

### Run Lighthouse
```bash
npm run perf:lighthouse
```

## Next Steps

1. **Immediate**: Test the app and verify optimizations work
2. **Short-term**: Add image optimization and CDN
3. **Medium-term**: Implement API caching and database indexing
4. **Long-term**: Set up full observability stack

## Resources
- [Web Vitals](https://web.dev/vitals/)
- [Lighthouse CI](https://github.com/GoogleChrome/lighthouse-ci)
- [Vite Performance](https://vitejs.dev/guide/performance.html)
