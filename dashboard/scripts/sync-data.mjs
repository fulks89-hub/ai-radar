import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';

const root = resolve(process.cwd(), '..');
const output = resolve(process.cwd(), 'public', 'data');
await mkdir(output, { recursive: true });

const files = {
  'daily.json': { generated_at: null, trends: [] },
  'weekly.json': { generated_at: null, trends: [] },
  'x-bookmarks.json': { enabled: false, status: 'not-generated', bookmarks: [], estimated_spend_this_week_usd: 0, weekly_budget_usd: 0 },
  'shared-inbox.json': { captures: [] },
  'latest.json': { generated_at: null, signals: [] },
};

for (const [name, fallback] of Object.entries(files)) {
  const source = resolve(root, 'reports', name);
  let text;
  try {
    text = await readFile(source, 'utf8');
    JSON.parse(text);
  } catch {
    text = JSON.stringify(fallback, null, 2) + '\n';
  }
  await writeFile(resolve(output, name), text, 'utf8');
}
