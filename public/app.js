const $ = id => document.getElementById(id);
let status, dashboard;
const numbers = new Intl.NumberFormat('fa-IR', { maximumFractionDigits: 1 });
const number = value => value == null ? '—' : numbers.format(Number(value));
const date = value => new Date(value).toLocaleDateString('fa-IR', { month: 'short', day: 'numeric' });
const messages = {
  setup_required: 'اول تنظیمات اتصال به گوگل را کامل کن؛ راهنما در بخش اتصال و تنظیمات است.',
  invalid_state: 'نشست ورود معتبر نیست یا منقضی شده. اتصال را از همین مرورگر دوباره شروع کن.',
  consent_denied: 'ورود یا دسترسی‌ها تأیید نشد؛ هیچ اتصالی برقرار نشده است.',
  auth_failed: 'تکمیل ورود ممکن نشد. تنظیمات OAuth و دسترسی سرور به گوگل را بررسی کن.',
  missing_scopes: 'هر دو مجوز خواندن کانال و آمار لازم‌اند. لطفاً دوباره وارد شو و هر دو را تأیید کن.',
  connected: 'اتصال امن برقرار شد. در حال خواندن اطلاعات کانال…',
  not_connected: 'ابتدا کانال را متصل کن.', reconnect_required: 'مجوز ورود منقضی یا لغو شده؛ دوباره به گوگل متصل شو.',
  google_unreachable: 'سرور به گوگل دسترسی ندارد. برنامه را روی میزبانی با دسترسی به گوگل اجرا کن.',
  google_api_error: 'دریافت اطلاعات از گوگل ممکن نشد. فعال بودن APIها، سهمیه و دسترسی حساب را بررسی کن.',
  no_channel: 'برای این حساب کانالی پیدا نشد. با حساب یا Brand Account درست وارد شو.',
  revoke_failed: 'لغو مجوز در گوگل انجام نشد. دوباره تلاش کن یا فقط از این برنامه خارج شو و مجوز را در حساب گوگل لغو کن.',
  csrf_failed: 'نشست مرورگر تغییر کرده. صفحه را تازه‌سازی کن.',
};
function notice(text, success = false) { $('notice').textContent = text; $('notice').classList.toggle('success', success); $('notice').hidden = !text; }
function view(name) {
  $('overview-view').hidden = name !== 'overview'; $('setup-view').hidden = name !== 'setup';
  document.querySelectorAll('.nav-item[data-view]').forEach(el => el.classList.toggle('active', el.dataset.view === name));
  $('breadcrumb').textContent = name === 'setup' ? 'اتصال و تنظیمات' : 'نمای کلی';
  $('page-title').textContent = name === 'setup' ? 'یک اتصال امن، برای کانال تو.' : 'یک نگاه، تمام کانال.';
  $('page-subtitle').textContent = name === 'setup' ? 'دسترسی‌ها روشن‌اند؛ اختیار کانالت همیشه دست خودت می‌ماند.' : 'نبض کانالت را ببین؛ برای ویدیوی بعدی، آگاهانه تصمیم بگیر.';
}
document.querySelectorAll('[data-view]').forEach(el => el.addEventListener('click', () => view(el.dataset.view)));
async function api(path, options = {}) {
  const response = await fetch(path, { ...options, headers: { ...(options.method === 'POST' ? { 'X-CSRF-Token': status.csrf } : {}), ...options.headers } });
  let data;
  try { data = await response.json(); } catch { throw new Error('پاسخ سرور قابل خواندن نیست؛ اتصال یا محدودیت درخواست‌ها را بررسی کن.'); }
  if (!response.ok) throw new Error(messages[data.error] || 'درخواست انجام نشد؛ کمی بعد دوباره تلاش کن.');
  return data;
}
async function loadStatus() {
  status = await api('/api/status');
  $('setup-status-title').textContent = status.connected ? 'کانال متصل است' : status.configured ? 'آمادهٔ ورود به گوگل' : 'منتظر تنظیمات سرور';
  $('setup-status-detail').textContent = status.connected ? 'اطلاعات فقط در نشست همین مرورگر قابل دسترسی است.' : status.configured ? 'اکنون می‌توانی با حساب مدیر کانال وارد شوی.' : 'فایل محیطی و OAuth Client هنوز کامل تنظیم نشده‌اند.';
  $('disconnect').hidden = $('logout').hidden = !status.connected;
  $('connect-banner').hidden = status.connected;
  $('redirect-uri').textContent = status.redirectUri || 'APP_BASE_URL/auth/google/callback';
  $('connect').textContent = status.configured ? 'اتصال با حساب گوگل ↗' : 'راه‌اندازی اتصال امن ↗';
}
function safeImage(image, url) {
  try {
    const parsed = new URL(url);
    if (parsed.protocol === 'https:' && ['i.ytimg.com', 'yt3.ggpht.com', 'yt3.googleusercontent.com'].includes(parsed.hostname)) image.src = parsed.href;
  } catch { /* No arbitrary remote image URLs. */ }
}
function render(data) {
  $('export').hidden = false;
  $('channel-strip').hidden = false;
  $('channel-title').textContent = data.channel.title;
  $('channel-handle').textContent = data.channel.handle || data.channel.id;
  safeImage($('channel-avatar'), data.channel.thumbnail);
  $('period-tag').textContent = `${date(data.period.startDate)} تا ${date(data.period.endDate)}`;
  $('data-status').textContent = 'اطلاعات واقعی · پایان بازه با ۳ روز فاصله';
  const totals = data.analytics?.totals;
  $('metric-views').textContent = number(totals?.views);
  $('metric-watch').textContent = number(totals ? totals.estimatedMinutesWatched / 60 : null);
  $('metric-subs').textContent = number(totals ? totals.subscribersGained - totals.subscribersLost : null);
  $('metric-duration').textContent = number(totals?.averageViewDuration);
  drawChart(data.analytics?.daily || [], data.period);
  $('videos').replaceChildren();
  $('video-empty').hidden = Boolean(data.videos.length);
  if (!data.videos.length) {
    $('video-empty').querySelector('strong').textContent = 'ویدیویی برای نمایش در دسترس نیست.';
    $('video-empty').querySelector('p').textContent = 'ممکن است کانال ویدیویی نداشته باشد یا دریافت فهرست انجام نشده باشد.';
  }
  for (const video of data.videos) {
    const link = document.createElement('a'); link.className = 'video-row';
    link.href = `https://www.youtube.com/watch?v=${encodeURIComponent(video.id)}`; link.target = '_blank'; link.rel = 'noopener noreferrer';
    const img = document.createElement('img'); img.alt = ''; img.loading = 'lazy'; img.referrerPolicy = 'no-referrer'; safeImage(img, video.thumbnail);
    const info = document.createElement('div'); info.className = 'video-info';
    const title = document.createElement('h3'); title.textContent = video.title;
    const published = document.createElement('small'); published.textContent = date(video.publishedAt); info.append(title, published);
    const stat = document.createElement('div'); stat.className = 'video-stat'; stat.textContent = number(video.statistics?.viewCount);
    const label = document.createElement('small'); label.textContent = 'بازدید کل'; stat.append(label);
    link.append(img, info, stat); $('videos').append(link);
  }
  const warnings = [];
  if (!data.expectedChannel) warnings.push('توجه: کانال انتخاب‌شده با @AhangBan تطبیق ندارد. عنوان و شناسهٔ کانال بالا را بررسی کن؛ برای تغییر حساب خارج شو و دوباره وارد شو.');
  if (data.warnings.includes('analytics_unavailable')) warnings.push('آمار Analytics در دسترس نیست؛ ممکن است هنوز داده‌ای آماده نباشد، دسترسی کافی نباشد یا API فعال نشده باشد. مقادیر خالی به معنی صفر نیست.');
  if (data.warnings.includes('videos_unavailable')) warnings.push('دریافت آخرین ویدیوها انجام نشد.');
  if (!warnings.length && !totals) warnings.push('برای این بازه هنوز دادهٔ تحلیلی قابل گزارش وجود ندارد.');
  notice(warnings.join(' '));
}
function drawChart(rows, period) {
  const svg = $('chart-svg'); svg.replaceChildren();
  $('chart-empty').hidden = rows.length > 0; svg.toggleAttribute('hidden', !rows.length);
  if (!rows.length) {
    $('chart-empty').querySelector('strong').textContent = 'هنوز دادهٔ قابل نمایش نداریم';
    $('chart-empty').querySelector('p').textContent = 'داده‌های آماده‌نشده یا خطای دسترسی به معنی صفر بازدید نیست.';
    return;
  }
  const max = Math.max(1, ...rows.map(row => Number(row.views)));
  const span = Math.max(1, Date.parse(period.endDate) - Date.parse(period.startDate));
  const points = rows.map(row => [8 + (Date.parse(row.day) - Date.parse(period.startDate)) / span * 784, 190 - Number(row.views) / max * 175]);
  const ns = 'http://www.w3.org/2000/svg';
  const area = document.createElementNS(ns, 'path');
  area.setAttribute('d', `M${points[0][0]},200 L${points.map(p => p.join(',')).join(' L')} L${points.at(-1)[0]},200 Z`);
  area.setAttribute('fill', '#b7ed8c'); area.setAttribute('fill-opacity', '.06'); svg.append(area);
  const line = document.createElementNS(ns, 'polyline'); line.setAttribute('points', points.map(p => p.join(',')).join(' '));
  line.setAttribute('stroke', '#b7ed8c'); line.setAttribute('stroke-width', '2.5'); line.setAttribute('fill', 'none'); svg.append(line);
  for (let i = 0; i < points.length; i++) {
    const dot = document.createElementNS(ns, 'circle'); dot.setAttribute('cx', points[i][0]); dot.setAttribute('cy', points[i][1]); dot.setAttribute('r', '3'); dot.setAttribute('fill', '#b7ed8c');
    const title = document.createElementNS(ns, 'title'); title.textContent = `${date(rows[i].day)}: ${number(rows[i].views)} بازدید`; dot.append(title); svg.append(dot);
  }
  document.querySelectorAll('.chart-grid span').forEach((el, i) => el.textContent = number(max * (3 - i) / 3));
  $('chart-start').textContent = date(period.startDate); $('chart-end').textContent = date(period.endDate);
}
function clearDashboard() {
  dashboard = null; $('export').hidden = true; $('channel-strip').hidden = true;
  for (const metric of ['views', 'watch', 'subs', 'duration']) $('metric-' + metric).textContent = '—';
  $('videos').replaceChildren(); $('video-empty').hidden = false;
  $('chart-svg').setAttribute('hidden', ''); $('chart-empty').hidden = false;
  document.querySelectorAll('.chart-grid span').forEach(el => el.textContent = '—');
  $('data-status').textContent = status?.connected ? 'دریافت اطلاعات انجام نشد' : 'در انتظار اتصال';
}
async function refresh() {
  $('refresh').disabled = true;
  try {
    await loadStatus();
    if (status.connected) { dashboard = await api('/api/dashboard'); render(dashboard); }
    else clearDashboard();
  } catch (err) { notice(err.message); await loadStatus().catch(() => {}); clearDashboard(); }
  finally { $('refresh').disabled = false; }
}
for (const id of ['connect', 'setup-connect']) $(id).addEventListener('click', event => {
  if (!status?.configured) { event.preventDefault(); view('setup'); notice(messages.setup_required); }
});
$('refresh').addEventListener('click', refresh);
$('copy-redirect').addEventListener('click', async () => {
  try { await navigator.clipboard.writeText($('redirect-uri').textContent); $('copy-redirect').textContent = 'کپی شد'; }
  catch { notice('کپی خودکار ممکن نشد؛ آدرس بازگشت را دستی انتخاب و کپی کن.'); }
});
for (const action of ['disconnect', 'logout']) $(action).addEventListener('click', async () => {
  const question = action === 'disconnect' ? 'مجوز برنامه در گوگل لغو و اتصال قطع شود؟' : 'از برنامه خارج می‌شوی؛ مجوز گوگل باقی می‌ماند. ادامه می‌دهی؟';
  if (!window.confirm(question)) return;
  $(action).disabled = true;
  try { await api(`/api/${action}`, { method: 'POST' }); window.location.replace('/'); }
  catch (err) { notice(err.message); $(action).disabled = false; }
});
const initialNotice = new URLSearchParams(location.search).get('notice');
if (initialNotice) { notice(messages[initialNotice] || 'ورود تکمیل نشد.', initialNotice === 'connected'); history.replaceState(null, '', '/'); }
refresh();

$('export').addEventListener('click', () => {
  if (!dashboard) return;
  const blob = new Blob([JSON.stringify({ exportedAt: new Date().toISOString(), ...dashboard }, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob); const link = document.createElement('a');
  link.href = url; link.download = 'ahangban-report.json'; link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
  notice('گزارش شامل آمار خصوصی کانال است، اما توکن یا رمز ندارد. فقط در صورت تمایل خودت آن را برای تحلیل در گفتگو بارگذاری کن.', true);
});
