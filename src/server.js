import { createApp } from './app.js';

const app = createApp({ baseUrl: process.env.APP_BASE_URL, clientId: process.env.GOOGLE_CLIENT_ID,
  clientSecret: process.env.GOOGLE_CLIENT_SECRET, sessionSecret: process.env.SESSION_SECRET });
const port = Number(process.env.PORT || 3000);
const host = process.env.HOST || '0.0.0.0';
const server = app.listen(port, host, () => console.log(`AhangBan dashboard listening on port ${port}. OAuth configuration: ${process.env.GOOGLE_CLIENT_ID ? 'provided; see setup guide' : 'not provided'}.`));
for (const signal of ['SIGTERM', 'SIGINT']) process.on(signal, () => { app.locals.close(); server.close(() => process.exit(0)); });
