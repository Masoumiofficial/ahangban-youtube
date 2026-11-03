import express from 'express';
import session from 'express-session';
import MemoryStoreFactory from 'memorystore';
import helmet from 'helmet';
import { rateLimit } from 'express-rate-limit';
import { randomBytes, createHash, timingSafeEqual } from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { createGoogle, GoogleError, SCOPES } from './google.js';

const random = () => randomBytes(32).toString('base64url');
const equal = (a, b) => typeof a === 'string' && typeof b === 'string' && Buffer.byteLength(a) === Buffer.byteLength(b) && timingSafeEqual(Buffer.from(a), Buffer.from(b));
const save = (req) => new Promise((resolve, reject) => req.session.save(e => e ? reject(e) : resolve()));
const regenerate = (req) => new Promise((resolve, reject) => req.session.regenerate(e => e ? reject(e) : resolve()));
const destroy = (req) => new Promise((resolve, reject) => req.session.destroy(e => e ? reject(e) : resolve()));

export function createApp(config = {}, provider) {
  const app = express();
  const base = config.baseUrl ? new URL(config.baseUrl) : null;
  if (base && (base.pathname !== '/' || base.search || base.hash || base.username || base.password || !['http:', 'https:'].includes(base.protocol))) throw new Error('APP_BASE_URL must be an HTTP(S) origin without a path');
  if (base && base.protocol !== 'https:' && !['localhost', '127.0.0.1'].includes(base.hostname)) throw new Error('Public APP_BASE_URL requires HTTPS');
  const configured = Boolean(base && config.clientId && config.clientSecret && config.sessionSecret?.length >= 32);
  const redirectUri = base ? `${base.origin}/auth/google/callback` : null;
  const google = provider || createGoogle({ ...config, redirectUri });
  const Store = MemoryStoreFactory(session);
  const store = new Store({ checkPeriod: 60_000, max: 500 });
  app.locals.close = () => store.stopInterval();
  app.set('trust proxy', 1);
  app.disable('x-powered-by');
  app.use(helmet({ contentSecurityPolicy: { directives: {
    defaultSrc: ["'self'"], scriptSrc: ["'self'"], styleSrc: ["'self'"],
    imgSrc: ["'self'", 'https://yt3.ggpht.com', 'https://yt3.googleusercontent.com', 'https://i.ytimg.com'],
    connectSrc: ["'self'"], frameAncestors: ["'self'", 'https://arena.ai', 'https://*.arena.ai', 'https://*.e2b.app'], upgradeInsecureRequests: null,
  } }, xFrameOptions: false, strictTransportSecurity: base?.protocol === 'https:' ? undefined : false }));
  app.use(express.json({ limit: '2kb' }));
  app.use(session({
    name: 'ahangban.sid', secret: config.sessionSecret || random(), store,
    resave: false, saveUninitialized: false,
    cookie: { httpOnly: true, secure: base?.protocol === 'https:', sameSite: 'lax', maxAge: 8 * 60 * 60 * 1000 },
  }));
  app.use(['/api', '/auth'], (_req, res, next) => { res.set('Cache-Control', 'no-store'); next(); });
  app.use('/auth', rateLimit({ windowMs: 15 * 60_000, limit: 30, standardHeaders: 'draft-8', legacyHeaders: false }));
  app.use('/api', rateLimit({ windowMs: 60_000, limit: 60, standardHeaders: 'draft-8', legacyHeaders: false }));
  app.get('/api/status', (req, res) => {
    req.session.csrf ||= random();
    res.json({ configured, connected: Boolean(req.session.tokens), csrf: req.session.csrf, redirectUri, channelUrl: 'https://www.youtube.com/@AhangBan' });
  });
  app.get('/auth/google', async (req, res) => {
    if (!configured) return res.redirect('/?notice=setup_required');
    await regenerate(req);
    const state = random(), verifier = random();
    req.session.oauth = { state, verifier, createdAt: Date.now() };
    await save(req);
    const url = new URL('https://accounts.google.com/o/oauth2/v2/auth');
    url.search = new URLSearchParams({ client_id: config.clientId, redirect_uri: redirectUri,
      response_type: 'code', scope: SCOPES.join(' '), state,
      code_challenge: createHash('sha256').update(verifier).digest('base64url'), code_challenge_method: 'S256',
      access_type: 'offline', prompt: 'consent', include_granted_scopes: 'false',
    });
    res.redirect(url.href);
  });
  app.get('/auth/google/callback', async (req, res) => {
    const pending = req.session.oauth;
    delete req.session.oauth;
    await save(req);
    if (!pending || Date.now() - pending.createdAt > 600_000 || !equal(req.query.state, pending.state)) return res.redirect('/?notice=invalid_state');
    if (req.query.error) return res.redirect('/?notice=consent_denied');
    if (typeof req.query.code !== 'string' || !req.query.code) return res.redirect('/?notice=auth_failed');
    try {
      const tokens = await google.exchange(req.query.code, pending.verifier);
      if (!tokens.access_token) throw new Error('Missing access token');
      if (typeof tokens.scope !== 'string' || !SCOPES.every(scope => tokens.scope.split(' ').includes(scope))) {
        if (tokens.refresh_token || tokens.access_token) await google.revoke(tokens.refresh_token || tokens.access_token).catch(() => {});
        return res.redirect('/?notice=missing_scopes');
      }
      await regenerate(req);
      req.session.tokens = { access_token: tokens.access_token, refresh_token: tokens.refresh_token, expires_at: Date.now() + (tokens.expires_in || 3600) * 1000 };
      req.session.csrf = random();
      await save(req);
      res.redirect('/?notice=connected');
    } catch { res.redirect('/?notice=auth_failed'); }
  });
  function csrf(req, res, next) {
    if (!equal(req.get('x-csrf-token'), req.session.csrf)) return res.status(403).json({ error: 'csrf_failed' });
    next();
  }
  app.post('/api/disconnect', csrf, async (req, res) => {
    if (req.session.tokens) {
      try { await google.revoke(req.session.tokens.refresh_token || req.session.tokens.access_token); }
      catch { return res.status(502).json({ error: 'revoke_failed' }); }
    }
    await destroy(req);
    res.clearCookie('ahangban.sid', { path: '/' });
    res.json({ ok: true });
  });
  // Forget the local session even if Google is unreachable. This does not revoke Google's grant.
  app.post('/api/logout', csrf, async (req, res) => {
    await destroy(req);
    res.clearCookie('ahangban.sid', { path: '/' });
    res.json({ ok: true });
  });
  app.use('/api/dashboard', async (req, res, next) => {
    if (!req.session.tokens) return res.status(401).json({ error: 'not_connected' });
    try {
      if (req.session.tokens.expires_at < Date.now() + 60_000) {
        if (!req.session.tokens.refresh_token) throw new GoogleError(401, 'invalid_grant');
        const refreshed = await google.refresh(req.session.tokens.refresh_token);
        if (!refreshed.access_token) throw new GoogleError(401, 'invalid_grant');
        req.session.tokens = { ...req.session.tokens, access_token: refreshed.access_token,
          refresh_token: refreshed.refresh_token || req.session.tokens.refresh_token,
          expires_at: Date.now() + (refreshed.expires_in || 3600) * 1000 };
        await save(req);
      }
      req.accessToken = req.session.tokens.access_token;
      next();
    } catch (err) { next(err); }
  });
  app.get('/api/dashboard', async (req, res) => {
    const get = (path, params, analytics = false) => google.get(path, params, req.accessToken, analytics);
    const channels = await get('channels', { part: 'snippet,statistics,contentDetails', mine: 'true' });
    const channel = channels.items?.[0];
    if (!channel) return res.status(404).json({ error: 'no_channel' });
    // Never silently label a different Google/Brand account as AhangBan.
    const expectedChannel = channel.snippet?.customUrl?.toLowerCase() === '@ahangban';
    const warnings = [];
    let videos = [];
    try {
      const uploads = channel.contentDetails?.relatedPlaylists?.uploads;
      if (uploads) {
        const playlist = await get('playlistItems', { part: 'contentDetails', playlistId: uploads, maxResults: '12' });
        const ids = playlist.items?.map(item => item.contentDetails?.videoId).filter(Boolean) || [];
        if (ids.length) {
          const details = await get('videos', { part: 'snippet,statistics,contentDetails', id: ids.join(',') });
          videos = (details.items || []).map(v => ({ id: v.id, title: v.snippet?.title, publishedAt: v.snippet?.publishedAt, thumbnail: v.snippet?.thumbnails?.medium?.url, statistics: v.statistics }));
        }
      }
    } catch { warnings.push('videos_unavailable'); }
    const end = new Date(); end.setUTCDate(end.getUTCDate() - 3);
    const start = new Date(end); start.setUTCDate(start.getUTCDate() - 27);
    const period = { startDate: start.toISOString().slice(0, 10), endDate: end.toISOString().slice(0, 10) };
    let analytics = null;
    try {
      const params = { ids: 'channel==MINE', ...period, metrics: 'views,estimatedMinutesWatched,subscribersGained,subscribersLost,averageViewDuration' };
      const [totals, daily] = await Promise.all([
        get('reports', params, true), get('reports', { ...params, dimensions: 'day', sort: 'day' }, true),
      ]);
      const objects = report => (report.rows || []).map(row => Object.fromEntries(report.columnHeaders.map((c, i) => [c.name, row[i]])));
      analytics = { totals: objects(totals)[0] || null, daily: objects(daily) };
    } catch { warnings.push('analytics_unavailable'); }
    res.json({ channel: { id: channel.id, title: channel.snippet?.title, handle: channel.snippet?.customUrl,
      thumbnail: channel.snippet?.thumbnails?.medium?.url, statistics: channel.statistics }, expectedChannel, videos, period, analytics, warnings });
  });
  app.use(express.static(fileURLToPath(new URL('../public', import.meta.url))));
  app.use((err, req, res, _next) => {
    // Do not log OAuth codes, credentials, token responses, or full request URLs.
    if (err instanceof GoogleError) {
      if (err.status === 401 || err.reason === 'invalid_grant') {
        delete req.session.tokens;
        return res.status(401).json({ error: 'reconnect_required' });
      }
      return res.status(err.status === 403 ? 403 : 502).json({ error: err.reason === 'google_unreachable' ? 'google_unreachable' : 'google_api_error' });
    }
    res.status(500).json({ error: 'server_error' });
  });
  return app;
}
