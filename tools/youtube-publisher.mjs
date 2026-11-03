#!/usr/bin/env node
/** Local Windows/desktop publisher. NOT an Arena connector or remote-control agent.
 * OAuth secrets/tokens/session URLs stay in process memory, never logs/receipts.
 * Uses the user's existing OAuth client with NEW consent for youtube.upload.
 * No real Google call is made merely by importing this module or running tests.
 */
import { createHash, randomBytes, timingSafeEqual } from 'node:crypto';
import { createServer } from 'node:http';
import { mkdir, readFile, open, rename, rm } from 'node:fs/promises';
import { resolve, join, basename } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawn } from 'node:child_process';
import { parseArgs } from 'node:util';

export const SCOPES = ['https://www.googleapis.com/auth/youtube.readonly', 'https://www.googleapis.com/auth/youtube.upload'];
const API = 'https://www.googleapis.com/youtube/v3/';
const CHUNK = 8 * 1024 * 1024;
const pause = ms => new Promise(r => setTimeout(r, ms));
const equal = (a, b) => typeof a === 'string' && typeof b === 'string' && Buffer.byteLength(a) === Buffer.byteLength(b) && timingSafeEqual(Buffer.from(a), Buffer.from(b));
export class PublishError extends Error {
  constructor(code, status = null, detail = null) { super(code); this.name = 'PublishError'; this.code = code; this.status = status; this.detail = detail; }
}
function check(condition, code) { if (!condition) throw new PublishError(code); }
export function validateJob(job) {
  check(job?.schemaVersion === 1 && job.id === 'ahangban-009', 'invalid_job');
  check(/^[a-f0-9]{40}$/.test(job.sourceCommit), 'invalid_source_commit');
  check(job.expectedChannelHandle?.toLowerCase() === '@ahangban', 'unexpected_target_channel');
  check(typeof job.title === 'string' && job.title.length > 0 && job.title.length <= 100 && !/[<>]/.test(job.title), 'invalid_title');
  check(typeof job.description === 'string' && Buffer.byteLength(job.description) <= 5000 && !/[<>]/.test(job.description), 'invalid_description');
  check(Array.isArray(job.tags) && job.tags.every(s => typeof s === 'string' && s.length < 100) && job.tags.join(',').length <= 450, 'invalid_tags');
  for (const kind of ['video', 'thumbnail']) {
    const a = job.assets?.[kind];
    check(a && /^downloads\/[a-z0-9-]+\.(mp4|jpg)$/.test(a.path) && /^[a-f0-9]{64}$/.test(a.sha256) && Number.isSafeInteger(a.bytes) && a.bytes > 0, 'invalid_asset');
    check(a.path.endsWith(kind === 'video' ? '.mp4' : '.jpg'), 'wrong_asset_type');
  }
  check(job.categoryId === '10' && job.language === 'fa' && job.containsSyntheticMedia === true, 'unexpected_metadata');
  return job;
}
export function makeMetadata(job, privacy, notMadeForKids) {
  validateJob(job); check(['public', 'private'].includes(privacy), 'explicit_visibility_required');
  check(notMadeForKids === true, 'explicit_audience_confirmation_required');
  return { snippet: { title: job.title, description: job.description, tags: job.tags, categoryId: job.categoryId,
    defaultLanguage: job.language, defaultAudioLanguage: job.language },
  status: { privacyStatus: privacy, selfDeclaredMadeForKids: false, containsSyntheticMedia: true } };
}
export function chooseChannel(body, handle) {
  const channels = body.items?.filter(c => c.snippet?.customUrl?.toLowerCase() === handle.toLowerCase()) || [];
  check(body.items?.length === 1 && channels.length === 1 && /^[A-Za-z0-9_-]{20,40}$/.test(channels[0].id), 'wrong_or_missing_ahangban_channel');
  return channels[0];
}
const SAFE_CODES = new Set(['EPERM', 'EACCES', 'EBUSY', 'ENOENT', 'ENOSPC', 'EIO', 'ECONNRESET', 'ECONNREFUSED', 'ENOTFOUND', 'EAI_AGAIN', 'ETIMEDOUT', 'ENETUNREACH', 'UND_ERR_CONNECT_TIMEOUT', 'UND_ERR_HEADERS_TIMEOUT', 'UND_ERR_BODY_TIMEOUT', 'ABORT_ERR', 'TIMEOUT']);
const GOOGLE_REASONS = new Set(['forbidden', 'insufficientPermissions', 'quotaExceeded', 'dailyLimitExceeded', 'uploadLimitExceeded', 'invalidImage', 'invalidValue', 'authError', 'youtubeSignupRequired', 'channelNotFound', 'videoNotFound', 'rateLimitExceeded', 'backendError', 'accessNotConfigured', 'accountDelegationForbidden', 'badRequest', 'invalidParameter', 'thumbnailTooLarge']);
function safeCode(error) {
  const code = error?.cause?.code || error?.code;
  if (SAFE_CODES.has(code)) return code;
  if (error?.name === 'TimeoutError' || error?.name === 'AbortError') return 'TIMEOUT';
  return null;
}
export function formatError(error) {
  const code = error instanceof PublishError ? error.code : 'local_or_network_error';
  const status = error instanceof PublishError && Number.isInteger(error.status) ? `HTTP ${error.status}` : null;
  const candidate = error instanceof PublishError ? error.detail : safeCode(error);
  const detail = SAFE_CODES.has(candidate) || GOOGLE_REASONS.has(candidate) ? candidate : null;
  return code + ([status, detail].filter(Boolean).length ? ` (${[status, detail].filter(Boolean).join(', ')})` : '');
}
async function googleReason(response) {
  try {
    const body = await response.json(); const reason = body.error?.errors?.[0]?.reason;
    return GOOGLE_REASONS.has(reason) ? reason : null;
  } catch { return null; }
}
async function checkedJson(response, stage) {
  if (!response.ok) throw new PublishError(stage, response.status, await googleReason(response));
  try { return await response.json(); } catch { throw new PublishError(`${stage}_invalid_response`); }
}
export async function googleRequest(url, options, { stage, fetchImpl = fetch, sleep = pause, attempts = 3 }) {
  for (let attempt = 1; attempt <= attempts; attempt++) {
    let response;
    try { response = await fetchImpl(url, { ...options, redirect: 'error', signal: AbortSignal.timeout(30_000) }); }
    catch (error) {
      if (attempt === attempts) throw new PublishError(`${stage}_network_error`, null, safeCode(error));
      await sleep(500 * 2 ** (attempt - 1)); continue;
    }
    if (response.ok) return response;
    if ([408, 429, 500, 502, 503, 504].includes(response.status) && attempt < attempts) {
      await response.body?.cancel(); await sleep(500 * 2 ** (attempt - 1)); continue;
    }
    throw new PublishError(stage, response.status, await googleReason(response));
  }
}
function showVideoLinks(id) {
  check(/^[A-Za-z0-9_-]{11}$/.test(id), 'invalid_video_id');
  console.log(`Video: https://www.youtube.com/watch?v=${id}`);
  console.log(`Studio: https://studio.youtube.com/video/${id}/edit`);
  console.log('A saved video ID confirms an upload, NOT its current public visibility or copyright clearance.');
}
export async function downloadAsset(job, kind, directory, fetchImpl = fetch) {
  validateJob(job); await mkdir(directory, { recursive: true });
  const a = job.assets[kind], target = join(directory, basename(a.path));
  try {
    const data = await readFile(target);
    if (data.length === a.bytes && createHash('sha256').update(data).digest('hex') === a.sha256) return target;
  } catch { /* A missing or corrupt local cache must be replaced, not trusted. */ }
  const url = `https://github.com/Masoumiofficial/ahangban-youtube/raw/${job.sourceCommit}/${a.path}`;
  const response = await fetchImpl(url, { signal: AbortSignal.timeout(180_000) });
  check(response.ok && response.body, 'asset_download_failed');
  const temporary = target + '.part'; const f = await open(temporary, 'w'); let count = 0; const hash = createHash('sha256');
  try {
    for await (const chunk of response.body) {
      count += chunk.length; check(count <= a.bytes, 'asset_size_mismatch'); hash.update(chunk); await f.writeFile(chunk);
    }
    check(count === a.bytes && hash.digest('hex') === a.sha256, 'asset_hash_mismatch');
  } catch (e) { await f.close(); await rm(temporary, { force: true }); throw e; }
  await f.close(); await rename(temporary, target); return target;
}
export function validateSessionUrl(value) {
  let url; try { url = new URL(value); } catch { throw new PublishError('invalid_upload_session'); }
  check(url.protocol === 'https:' && url.hostname === 'www.googleapis.com' && !url.username && !url.password && !url.port && url.pathname.startsWith('/upload/youtube/v3/videos'), 'untrusted_upload_session');
  return url.href;
}
export function acknowledgedOffset(response, total) {
  const range = response.headers.get('range');
  if (!range) return 0;
  const match = /^bytes=0-(\d+)$/.exec(range); check(match, 'invalid_upload_range');
  const offset = Number(match[1]) + 1; check(Number.isSafeInteger(offset) && offset > 0 && offset <= total, 'invalid_upload_range');
  return offset;
}
export async function resumableUpload({ file, bytes, sessionUrl, accessToken, fetchImpl = fetch, sleep = pause }) {
  const url = validateSessionUrl(sessionUrl); const f = await open(file, 'r'); let offset = 0, failures = 0;
  const request = options => fetchImpl(url, { ...options, redirect: 'manual', signal: AbortSignal.timeout(180_000),
    headers: { Authorization: `Bearer ${accessToken}`, ...options.headers } });
  const finish = async response => {
    const data = await checkedJson(response, 'upload_failed'); check(/^[A-Za-z0-9_-]{11}$/.test(data.id || ''), 'missing_video_id'); return data;
  };
  try {
    while (offset < bytes) {
      const start = offset, length = Math.min(CHUNK, bytes - offset), buffer = Buffer.alloc(length);
      const { bytesRead } = await f.read(buffer, 0, length, start); check(bytesRead === length, 'local_video_truncated');
      let response;
      try { response = await request({ method: 'PUT', headers: { 'Content-Type': 'video/mp4', 'Content-Length': String(length), 'Content-Range': `bytes ${start}-${start + length - 1}/${bytes}` }, body: buffer }); }
      catch { response = null; }
      if (response?.status === 200 || response?.status === 201) return await finish(response);
      if (response?.status === 308) {
        const next = acknowledgedOffset(response, bytes); check(next >= start && next <= start + length, 'invalid_upload_range');
        if (next > start) { offset = next; failures = 0; continue; }
      } else if (response && ![408, 429, 500, 502, 503, 504].includes(response.status)) {
        throw new PublishError('upload_failed', response.status);
      }
      failures += 1; check(failures <= 4, 'upload_interrupted_outcome_uncertain'); await sleep(1000 * 2 ** (failures - 1));
      // Reconcile the SAME upload session before sending more bytes; never initiate a duplicate.
      let probe;
      try { probe = await request({ method: 'PUT', headers: { 'Content-Length': '0', 'Content-Range': `bytes */${bytes}` } }); }
      catch { continue; }
      if (probe.status === 200 || probe.status === 201) return await finish(probe);
      check(probe.status === 308, 'upload_session_unavailable'); offset = acknowledgedOffset(probe, bytes);
    }
    const final = await request({ method: 'PUT', headers: { 'Content-Length': '0', 'Content-Range': `bytes */${bytes}` } });
    return await finish(final);
  } finally { await f.close(); }
}
export async function readReceipt(path) { try { return JSON.parse(await readFile(path, 'utf8')); } catch (e) { if (e.code === 'ENOENT') return null; throw new PublishError('invalid_local_receipt'); } }
export async function writeReceipt(path, receipt, { renameImpl = rename, sleep = pause } = {}) {
  // Allowlist only NON-SECRET fields. Never remove the old receipt if replacement fails.
  const safe = Object.fromEntries(['jobId', 'videoSha256', 'channelId', 'requestedPrivacy', 'videoId', 'state', 'thumbnailSet', 'thumbnailHttpStatus', 'thumbnailError', 'lastStatusError', 'actualPrivacy', 'processingStatus', 'updatedAt'].filter(k => receipt[k] !== undefined).map(k => [k, receipt[k]]));
  try {
    await mkdir(resolve(path, '..'), { recursive: true });
    await (await import('node:fs/promises')).writeFile(path + '.part', JSON.stringify(safe, null, 2) + '\n');
    for (let i = 0; ; i++) {
      try { await renameImpl(path + '.part', path); break; }
      catch (error) {
        if (!['EPERM', 'EACCES', 'EBUSY'].includes(error.code) || i >= 3) throw error;
        await sleep(100 * (i + 1));
      }
    }
  } catch (error) { throw new PublishError('receipt_write_failed', null, safeCode(error)); }
}
export function checkReceipt(receipt, job, channelId) {
  if (!receipt) return;
  check(receipt.jobId === job.id && receipt.videoSha256 === job.assets.video.sha256 && receipt.channelId === channelId, 'receipt_target_mismatch');
  check(receipt.state !== 'upload_started' || receipt.videoId, 'previous_upload_outcome_uncertain_check_studio');
  if (receipt.videoId) check(/^[A-Za-z0-9_-]{11}$/.test(receipt.videoId), 'invalid_local_receipt');
}
export async function authorize({ clientId, clientSecret, baseUrl, fetchImpl = fetch, openBrowser = openBrowserDefault }) {
  const base = new URL(baseUrl || 'http://localhost:3000');
  check(base.protocol === 'http:' && ['localhost', '127.0.0.1'].includes(base.hostname) && base.pathname === '/' && !base.search && !base.hash && !base.username && !base.password, 'local_oauth_origin_required');
  check(clientId && clientSecret, 'existing_local_oauth_configuration_missing');
  const state = randomBytes(32).toString('base64url'), verifier = randomBytes(48).toString('base64url');
  const redirect = `${base.origin}/auth/google/callback`; const auth = new URL('https://accounts.google.com/o/oauth2/v2/auth');
  auth.search = new URLSearchParams({ client_id: clientId, redirect_uri: redirect, response_type: 'code', scope: SCOPES.join(' '), state,
    code_challenge: createHash('sha256').update(verifier).digest('base64url'), code_challenge_method: 'S256', prompt: 'consent', include_granted_scopes: 'false' });
  let used = false, timer, server;
  try {
    const code = await new Promise((resolveCode, reject) => {
      server = createServer((req, res) => {
        res.setHeader('Cache-Control', 'no-store'); res.setHeader('Content-Type', 'text/plain; charset=utf-8');
        res.setHeader('Content-Security-Policy', "default-src 'none'; frame-ancestors 'none'");
        if (req.method !== 'GET' || req.headers.host !== base.host) { res.writeHead(403); res.end('Forbidden'); return; }
        const url = new URL(req.url, base.origin);
        if (url.pathname === '/') { res.writeHead(302, { Location: auth.href }); res.end(); return; }
        if (url.pathname !== '/auth/google/callback') { res.writeHead(404); res.end('Not found'); return; }
        if (used || !equal(url.searchParams.get('state'), state)) { res.writeHead(400); res.end('Invalid or expired sign-in.'); return; }
        used = true;
        if (url.searchParams.has('error') || !url.searchParams.get('code')) {
          res.end('Google permission was not granted. No video uploaded.'); reject(new PublishError('google_consent_denied')); return;
        }
        res.end('Sign-in received. Return to the PowerShell window. Upload status is shown there, not on this page.');
        resolveCode(url.searchParams.get('code'));
      });
      server.on('error', e => reject(new PublishError(e.code === 'EADDRINUSE' ? 'close_running_dashboard_then_retry' : 'local_callback_failed')));
      server.listen(Number(base.port || 80), '127.0.0.1', () => {
        console.log(`Open ${base.origin}/ to approve Google upload access. No passwords or tokens belong in chat.`);
        Promise.resolve(openBrowser(base.origin)).catch(() => {});
      });
      timer = setTimeout(() => reject(new PublishError('google_signin_timed_out')), 10 * 60_000);
    });
    const response = await fetchImpl('https://oauth2.googleapis.com/token', { method: 'POST', signal: AbortSignal.timeout(30_000),
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, body: new URLSearchParams({ client_id: clientId, client_secret: clientSecret,
        code, code_verifier: verifier, grant_type: 'authorization_code', redirect_uri: redirect }) });
    const token = await checkedJson(response, 'google_signin_failed');
    check(typeof token.access_token === 'string' && SCOPES.every(s => token.scope?.split(' ').includes(s)), 'upload_permission_not_granted');
    return token.access_token;
  } finally { clearTimeout(timer); server?.close(); server?.closeAllConnections(); }
}
function openBrowserDefault(url) {
  const command = process.platform === 'win32' ? ['rundll32.exe', ['url.dll,FileProtocolHandler', url]] : process.platform === 'darwin' ? ['open', [url]] : ['xdg-open', [url]];
  return new Promise((resolveOpen, reject) => { const child = spawn(command[0], command[1], { stdio: 'ignore', windowsHide: true }); child.once('error', reject); child.once('spawn', () => { child.unref(); resolveOpen(); }); });
}
export async function publish({ job, videoFile, thumbnailFile, accessToken, privacy, notMadeForKids, receiptPath, fetchImpl = fetch, sleep = pause, processingTimeout = 180_000, resumeOnly = false }) {
  const metadata = makeMetadata(job, privacy, notMadeForKids);
  let receipt = await readReceipt(receiptPath);
  if (resumeOnly) check(receipt?.videoId, 'resume_receipt_missing_no_upload_started');
  if (receipt?.videoId) {
    checkReceipt(receipt, job, receipt.channelId);
    console.log('Saved upload found. No new video upload will be started.'); showVideoLinks(receipt.videoId);
  }
  const get = async (path, parameters) => {
    const u = new URL(path, API); u.search = new URLSearchParams(parameters);
    const stage = path === 'channels' ? 'channel_lookup_failed' : parameters.part.includes('snippet') ? 'video_identity_lookup_failed' : 'video_status_lookup_failed';
    const response = await googleRequest(u, { headers: { Authorization: `Bearer ${accessToken}` } }, { stage, fetchImpl, sleep });
    return checkedJson(response, stage);
  };
  const channel = chooseChannel(await get('channels', { part: 'snippet', mine: 'true', maxResults: '50' }), job.expectedChannelHandle);
  console.log(`Verified channel: ${job.expectedChannelHandle}. Requested visibility: ${privacy}.`);
  checkReceipt(receipt, job, channel.id);
  if (receipt?.videoId) check(receipt.requestedPrivacy === privacy, 'existing_video_visibility_differs_no_duplicate_upload');
  if (!receipt?.videoId) {
    check(!resumeOnly, 'resume_receipt_missing_no_upload_started');
    const init = await fetchImpl('https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status&notifySubscribers=true', {
      method: 'POST', signal: AbortSignal.timeout(30_000), headers: { Authorization: `Bearer ${accessToken}`, 'Content-Type': 'application/json; charset=utf-8',
        'X-Upload-Content-Type': 'video/mp4', 'X-Upload-Content-Length': String(job.assets.video.bytes) }, body: JSON.stringify(metadata) });
    if (!init.ok) throw new PublishError('youtube_upload_initialization_failed', init.status, await googleReason(init));
    const sessionUrl = validateSessionUrl(init.headers.get('location'));
    receipt = { jobId: job.id, videoSha256: job.assets.video.sha256, channelId: channel.id, requestedPrivacy: privacy, state: 'upload_started', updatedAt: new Date().toISOString() };
    await writeReceipt(receiptPath, receipt); console.log('Uploading the hash-verified final video. Do not close this window.');
    const result = await resumableUpload({ file: videoFile, bytes: job.assets.video.bytes, sessionUrl, accessToken, fetchImpl, sleep });
    receipt = { ...receipt, videoId: result.id, state: 'uploaded', updatedAt: new Date().toISOString() };
    // Print the irreversible successful result BEFORE any later disk/status/thumbnail failure.
    showVideoLinks(receipt.videoId); await writeReceipt(receiptPath, receipt);
  } else { console.log('Continuing the existing upload; metadata and video bytes will not be resent.'); }
  const id = receipt.videoId;
  const pendingStatus = async error => {
    receipt.state = 'uploaded_status_pending'; receipt.lastStatusError = formatError(error); receipt.updatedAt = new Date().toISOString();
    console.log(`Existing upload retained; status check needs attention: ${formatError(error)}.`);
    console.log('Public visibility is NOT confirmed. Open the Studio link above; do not upload another copy.');
    await writeReceipt(receiptPath, receipt);
    return { videoId: id, privacy: receipt.actualPrivacy, processing: receipt.processingStatus || 'unknown', publicConfirmed: false, thumbnailSet: !!receipt.thumbnailSet, statusPending: true };
  };
  let owned;
  try { owned = (await get('videos', { part: 'snippet,status,processingDetails', id })).items?.[0]; }
  catch (error) { return pendingStatus(error); }
  check(owned?.id === id && owned.snippet?.channelId === channel.id && owned.snippet?.title === job.title, 'uploaded_video_identity_mismatch');
  if (!receipt.thumbnailSet) {
    try {
      const response = await googleRequest(`https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId=${id}&uploadType=media`, {
        method: 'POST', headers: { Authorization: `Bearer ${accessToken}`, 'Content-Type': 'image/jpeg' }, body: await readFile(thumbnailFile) }, { stage: 'thumbnail_set_failed', fetchImpl, sleep });
      if (response.ok) { receipt.thumbnailSet = true; delete receipt.thumbnailHttpStatus; delete receipt.thumbnailError; }
    } catch (error) {
      receipt.thumbnailSet = false; receipt.thumbnailHttpStatus = error instanceof PublishError ? error.status : null; receipt.thumbnailError = formatError(error);
      console.log(`Custom thumbnail pending: ${formatError(error)}. Video upload is retained; status check continues.`);
      if (error.status === 403) console.log('403 alone does not identify the cause. Check Studio channel feature eligibility/custom-thumbnail access and Google permissions; do not change/delete the video.');
    }
    await writeReceipt(receiptPath, receipt);
  }
  const deadline = Date.now() + processingTimeout; let video = owned;
  while (true) {
    receipt.actualPrivacy = video.status?.privacyStatus; receipt.processingStatus = video.processingDetails?.processingStatus || video.status?.uploadStatus;
    receipt.state = 'status_checked'; delete receipt.lastStatusError; receipt.updatedAt = new Date().toISOString(); await writeReceipt(receiptPath, receipt);
    if (['failed', 'terminated'].includes(receipt.processingStatus) || ['failed', 'rejected', 'deleted'].includes(video.status?.uploadStatus)) throw new PublishError('youtube_processing_or_policy_rejection');
    if (receipt.processingStatus === 'succeeded' || video.status?.uploadStatus === 'processed' || Date.now() >= deadline) break;
    await sleep(8000);
    try {
      video = (await get('videos', { part: 'status,processingDetails', id })).items?.[0]; check(video?.id === id, 'uploaded_video_status_unavailable');
    } catch (error) { return pendingStatus(error); }
  }
  const processed = receipt.processingStatus === 'succeeded' || video.status?.uploadStatus === 'processed';
  const publicConfirmed = processed && receipt.actualPrivacy === 'public';
  if (publicConfirmed) console.log('PUBLIC status and successful processing confirmed by YouTube API.');
  else if (privacy === 'public' && receipt.actualPrivacy !== 'public') console.log('NOT confirmed public. YouTube reports a non-public status. An unaudited API project or account restriction may force private uploads; this tool cannot bypass it.');
  else console.log(`Actual visibility: ${receipt.actualPrivacy || 'unknown'}; processing: ${receipt.processingStatus || 'pending'}.`);
  console.log('Content ID / copyright clearance is NOT confirmed by this API. Review Checks in Studio.');
  return { videoId: id, privacy: receipt.actualPrivacy, processing: receipt.processingStatus, publicConfirmed, thumbnailSet: !!receipt.thumbnailSet };
}
async function main() {
  const { values } = parseArgs({ options: { job: { type: 'string' }, project: { type: 'string' }, public: { type: 'boolean' }, private: { type: 'boolean' }, 'not-made-for-kids': { type: 'boolean' }, 'resume-only': { type: 'boolean' } } });
  check(Boolean(values.public) !== Boolean(values.private), 'choose_public_or_private_explicitly');
  check(values['not-made-for-kids'], 'explicit_audience_confirmation_required');
  const project = resolve(values.project || process.cwd()), work = join(project, 'rendered', 'youtube-publisher'); await mkdir(work, { recursive: true });
  const job = validateJob(JSON.parse(await readFile(resolve(values.job || join(project, 'tools/youtube-publish-job.json')), 'utf8')));
  let lock;
  try { lock = await open(join(work, 'publisher.lock'), 'wx'); }
  catch { throw new PublishError('publisher_already_running_or_stale_lock'); }
  try {
    if (values['resume-only']) {
      const existing = await readReceipt(join(work, `${job.id}-receipt.json`));
      check(existing?.videoId, 'resume_receipt_missing_no_upload_started');
      checkReceipt(existing, job, existing.channelId); showVideoLinks(existing.videoId);
      console.log('RESUME ONLY: creating a new upload is disabled.');
    }
    console.log('AhangBan 009: existing upload will be continued when a receipt is present.');
    console.log(`Requested: ${values.public ? 'PUBLIC' : 'PRIVATE'}; audience: NOT made for kids; synthetic-content disclosure: YES.`);
    console.log('No Content ID clearance is promised. Existing dashboard must be closed to free its OAuth port.');
    const videoFile = values['resume-only'] ? null : await downloadAsset(job, 'video', work), thumbnailFile = await downloadAsset(job, 'thumbnail', work);
    const accessToken = await authorize({ clientId: process.env.GOOGLE_CLIENT_ID, clientSecret: process.env.GOOGLE_CLIENT_SECRET, baseUrl: process.env.APP_BASE_URL });
    const result = await publish({ job, videoFile, thumbnailFile, accessToken, privacy: values.public ? 'public' : 'private', notMadeForKids: true, receiptPath: join(work, `${job.id}-receipt.json`), resumeOnly: !!values['resume-only'] });
    if ((values.public && !result.publicConfirmed) || !result.thumbnailSet) process.exitCode = 2;
  } finally { await lock.close(); await rm(join(work, 'publisher.lock'), { force: true }); }
}
if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main().catch(e => {
    // Never print raw fetch/Google exceptions: these can contain secret request URLs.
    console.error(`Publisher stopped: ${formatError(e)}`);
    console.error('No public-release claim is made. Keep credentials private; share only this error code or the non-secret receipt.'); process.exitCode = 1;
  });
}
