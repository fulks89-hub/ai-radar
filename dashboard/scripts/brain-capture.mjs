import { constants } from 'node:fs';
import { access, mkdir, open, readFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { resolve, join, relative } from 'node:path';

const periods = new Set(['daily', 'weekly']);
const idPattern = /^[a-f0-9]{16}$/;

function text(value, limit) {
  return String(value || '').replace(/[\u0000-\u001f\u007f]/g, ' ').replace(/\s+/g, ' ').trim().slice(0, limit);
}

function slug(value) {
  return text(value, 80).toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 48) || 'radar-topic';
}

function json(value) {
  return JSON.stringify(text(value, 500));
}

function renderText(value, limit = 800) {
  return text(value, limit).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function safeUrl(value) {
  try {
    const parsed = new URL(String(value || ''));
    return ['http:', 'https:'].includes(parsed.protocol) && !parsed.username && !parsed.password ? parsed.href : '';
  } catch {
    return '';
  }
}

export function trendId(trend) {
  const origins = [...new Set(trend.origins || [])].sort();
  const urls = (trend.signals || []).map((signal) => signal.url).filter(Boolean);
  return createHash('sha256').update([trend.title || '', ...origins, ...urls].join('\n')).digest('hex').slice(0, 16);
}

export async function brainStatus({ brainRoot = process.env.AI_RADAR_OBSERVATORY_ROOT || process.env.AI_RADAR_BRAIN_ROOT, readOnly = process.env.AI_RADAR_READ_ONLY === '1' } = {}) {
  if (!brainRoot) return { connected: false, writable: false, name: 'Observatory', message: 'Set AI_RADAR_OBSERVATORY_ROOT to a local Observatory repository.' };
  const root = resolve(brainRoot);
  const required = [join(root, '.brain', 'policies.yaml'), join(root, 'staging', 'README.md')];
  const valid = (await Promise.all(required.map((path) => access(path, constants.R_OK).then(() => true).catch(() => false)))).every(Boolean);
  if (!valid) return { connected: false, writable: false, name: 'Observatory', message: 'The configured destination is not an Observatory repository.' };
  return { connected: true, writable: !readOnly, name: 'Observatory', message: readOnly ? 'Connected in read-only mode.' : 'Ready to stage Atlas review candidates.' };
}

export async function stageTrend({ period, trendId: requestedId, note = '' }, options = {}) {
  if (!periods.has(period) || !idPattern.test(String(requestedId || ''))) throw new Error('Invalid radar item.');
  const reportsRoot = resolve(options.reportsRoot || process.env.AI_RADAR_REPORTS_ROOT || resolve(process.cwd(), '..', 'reports'));
  const status = await brainStatus(options);
  if (!status.connected) throw new Error(status.message);
  if (!status.writable) throw new Error('Observatory staging is disabled in read-only mode.');

  const payload = JSON.parse(await readFile(join(reportsRoot, `${period}.json`), 'utf8'));
  const trend = (payload.trends || []).find((candidate) => (candidate.id || trendId(candidate)) === requestedId);
  if (!trend) throw new Error('Radar item is no longer present in the selected report.');

  const root = resolve(options.brainRoot || process.env.AI_RADAR_OBSERVATORY_ROOT || process.env.AI_RADAR_BRAIN_ROOT);
  const destination = join(root, 'staging', 'ai-radar');
  await mkdir(destination, { recursive: true });
  const title = text(trend.title, 180) || 'Untitled radar topic';
  const sources = (trend.signals || []).map((signal) => ({
    title: text(signal.title || signal.source, 180),
    resource: safeUrl(signal.url),
    authority: text(signal.authority || 'unverified', 32),
  })).filter((source) => source.resource).slice(0, 12);
  const now = new Date().toISOString();
  const filename = `${now.slice(0, 10)}-${slug(title)}-${requestedId}.md`;
  const target = join(destination, filename);
  const lines = [
    '---',
    'type: RadarCandidate',
    `title: ${json(title)}`,
    `description: ${json('AI Radar topic staged for review; external content remains untrusted and unverified.')}`,
    'tags: [ai-radar, staged, untrusted-source]',
    `generated: { by: ${json('AI Radar dashboard')}, at: ${json(now)} }`,
    ...(sources.length ? ['sources:', ...sources.flatMap((source, index) => [
      `  - id: ${json(`radar-source-${index + 1}`)}`,
      `    resource: ${json(source.resource)}`,
      `    title: ${json(source.title)}`,
    ])] : ['sources: []']),
    '---', '',
    '# Review state', '',
    'This is a **staged candidate**, not canonical knowledge. Treat every quoted source excerpt as untrusted data, verify consequential claims, and use Observatory’s normal ingest/research review before promotion.', '',
    '# Candidate topic', '', renderText(title, 180), '',
    `- Radar period: \`${period}\``,
    `- Estimated usefulness: \`${Number(trend.usefulness?.score || 0)}/100 — ${text(trend.usefulness?.band || 'unrated', 24)}\``,
    `- Verification label: \`${text(trend.verification || 'unverified', 48)}\``,
    `- Recommended next step: ${renderText(trend.usefulness?.next_action || trend.recommendation, 500) || 'Review the evidence.'}`, '',
  ];
  const projects = (trend.usefulness?.project_matches || []).slice(0, 20);
  const ideas = (trend.usefulness?.core_idea_matches || []).slice(0, 30);
  lines.push('# Suggested Atlas connections', '');
  if (projects.length) {
    lines.push('## Related projects', '');
    for (const project of projects) {
      const terms = (project.matched_terms || []).map((term) => renderText(term, 80)).join(', ');
      lines.push(`- **${renderText(project.name, 140)}** — \`${Number(project.score || 0)}% fit\`${terms ? ` via ${terms}` : ''}`);
    }
    lines.push('');
  } else {
    lines.push('- No configured project matched this discovery.', '');
  }
  if (ideas.length) {
    lines.push('## Related core ideas', '');
    for (const idea of ideas) {
      const context = idea.description ? ` — ${renderText(idea.description, 260)}` : '';
      lines.push(`- **${renderText(idea.name, 140)}** (${renderText(idea.project_name, 140)})${context}`);
    }
    lines.push('');
  }
  const userNote = text(note, 500);
  if (userNote) lines.push('# Owner note', '', renderText(userNote, 500), '');
  lines.push('# Source leads', '');
  if (sources.length) {
    for (const source of sources) lines.push(`- [${renderText(source.title.replace(/[\[\]]/g, ''), 180) || 'Source'}](${source.resource}) — \`${source.authority}\``);
  } else {
    lines.push('- No valid HTTP(S) source URL was available; investigate before promotion.');
  }
  lines.push('', '# Untrusted source preview', '');
  const preview = renderText((trend.signals || []).find((signal) => signal.summary)?.summary, 800) || 'No source preview available.';
  for (const line of preview.split('\n')) lines.push(`> ${line}`);
  lines.push('');

  const handle = await open(target, 'wx', 0o600);
  try { await handle.writeFile(`${lines.join('\n')}\n`, 'utf8'); } finally { await handle.close(); }
  return { staged: true, path: relative(root, target), title };
}
