export const SCOPES = [
  'https://www.googleapis.com/auth/youtube.readonly',
  'https://www.googleapis.com/auth/yt-analytics.readonly',
];

export class GoogleError extends Error {
  constructor(status, reason = 'google_error') {
    super(reason);
    this.status = status;
    this.reason = reason;
  }
}

export function createGoogle({ clientId, clientSecret, redirectUri, fetchImpl = fetch }) {
  async function request(url, options = {}) {
    let response;
    try {
      response = await fetchImpl(url, { ...options, signal: AbortSignal.timeout(20_000) });
    } catch {
      throw new GoogleError(503, 'google_unreachable');
    }
    let body;
    try { body = await response.json(); } catch { throw new GoogleError(502, 'invalid_google_response'); }
    if (!response.ok) {
      const reason = body.error?.errors?.[0]?.reason || body.error?.status || (typeof body.error === 'string' ? body.error : 'google_error');
      throw new GoogleError(response.status, reason);
    }
    return body;
  }
  async function token(fields) {
    return request('https://oauth2.googleapis.com/token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ client_id: clientId, client_secret: clientSecret, ...fields }),
    });
  }
  return {
    exchange: (code, verifier) => token({ grant_type: 'authorization_code', code, code_verifier: verifier, redirect_uri: redirectUri }),
    refresh: (refreshToken) => token({ grant_type: 'refresh_token', refresh_token: refreshToken }),
    async revoke(value) {
      let response;
      try {
        response = await fetchImpl('https://oauth2.googleapis.com/revoke', {
          method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          body: new URLSearchParams({ token: value }), signal: AbortSignal.timeout(20_000),
        });
      } catch { throw new GoogleError(503, 'google_unreachable'); }
      if (!response.ok) throw new GoogleError(response.status, 'revoke_failed');
    },
    async get(path, params, accessToken, analytics = false) {
      const url = new URL(path, analytics ? 'https://youtubeanalytics.googleapis.com/v2/' : 'https://www.googleapis.com/youtube/v3/');
      url.search = new URLSearchParams(params).toString();
      return request(url, { headers: { Authorization: `Bearer ${accessToken}` } });
    },
  };
}
