import React, { useEffect, useMemo, useState } from 'react';

const h = React.createElement;
const BASE = import.meta.env.BASE_URL || './';

const verificationLabel = {
  'corroborated-primary': 'Corroborated',
  'primary-plus-discussion': 'Primary + discussion',
  'single-primary': 'Single primary',
  'owner-priority-unverified': 'Owner priority',
  'unverified-lead': 'Unverified lead',
};
const bandLabel = { act: 'Act', evaluate: 'Evaluate', watch: 'Watch', skip: 'Skip' };

function shortDate(value) {
  if (!value) return '—';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat(undefined, { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' }).format(date);
}

function compactNumber(value) {
  return new Intl.NumberFormat(undefined, { notation: 'compact', maximumFractionDigits: 1 }).format(Number(value || 0));
}

function cleanText(value = '') {
  return value.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim();
}

async function getJson(name) {
  const response = await fetch(`${BASE}data/${name}`, { cache: 'no-store' });
  if (!response.ok) throw new Error(`${name}: HTTP ${response.status}`);
  return response.json();
}

async function getBrainStatus() {
  try {
    const response = await fetch('/api/brain/status', { cache: 'no-store' });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  } catch {
    return { connected: false, writable: false, name: 'Observatory', message: 'Run the self-hosted dashboard with AI_RADAR_BRAIN_ROOT to enable staging.' };
  }
}

function Pill({ children, tone = 'neutral' }) {
  return h('span', { className: `pill pill-${tone}` }, children);
}

function Metric({ label, value, detail, tone = '' }) {
  return h('div', { className: `metric-card ${tone}` },
    h('span', { className: 'metric-label' }, label),
    h('strong', { className: 'metric-value' }, value),
    h('span', { className: 'metric-detail' }, detail)
  );
}

function SignalRow({ signal }) {
  const metrics = signal.public_metrics || {};
  return h('a', { className: 'signal-row', href: signal.url, target: '_blank', rel: 'noreferrer' },
    h('div', { className: 'signal-copy' },
      h('div', { className: 'signal-meta' },
        h(Pill, { tone: signal.authority === 'primary' ? 'primary' : signal.authority === 'owner' ? 'owner' : 'secondary' }, signal.source || 'source'),
        signal.watch ? h(Pill, { tone: 'watch' }, signal.watch) : null,
        h('span', null, shortDate(signal.published))
      ),
      h('div', { className: 'signal-title' }, signal.title || signal.summary || signal.url),
      signal.summary && signal.summary !== signal.title ? h('div', { className: 'signal-summary' }, cleanText(signal.summary)) : null
    ),
    Object.keys(metrics).length ? h('div', { className: 'signal-metrics' },
      h('span', null, `♥ ${compactNumber(metrics.like_count)}`),
      h('span', null, `↻ ${compactNumber(metrics.retweet_count ?? metrics.repost_count)}`)
    ) : h('span', { className: 'open-mark', 'aria-hidden': true }, '↗')
  );
}

function ProjectFitMap({ trend }) {
  const usefulness = trend.usefulness || {};
  const matches = usefulness.project_matches || [];
  const ideas = usefulness.core_idea_matches || [];
  const evidence = (trend.origins || []).slice(0, 3);
  const action = usefulness.next_action || trend.recommendation || 'Review';
  return h('section', { className: `project-map band-${usefulness.band || 'watch'}`, 'aria-label': 'Project fit map' },
    h('div', { className: 'map-heading' },
      h('span', null, 'Observatory relationship map'),
      h('small', null, `${matches.length} project${matches.length === 1 ? '' : 's'} · ${ideas.length} core idea${ideas.length === 1 ? '' : 's'}`)
    ),
    h('div', { className: 'map-flow' },
      h('div', { className: 'map-node signal-node' }, h('small', null, 'Signal'), h('strong', null, cleanText(trend.title).slice(0, 72))),
      h('span', { className: 'map-link', 'aria-hidden': true }, '→'),
      h('div', { className: 'project-nodes' },
        ...(matches.length ? matches.map((match) => h('div', { className: 'map-node project-node', key: match.id },
          h('div', null, h('small', null, 'Project'), h('strong', null, match.name)),
          h('span', null, `${match.score}% fit`),
          h('em', null, (match.matched_terms || []).join(' · ') || 'goal overlap')
        )) : [h('div', { className: 'map-node project-node no-match', key: 'none' }, h('small', null, 'Portfolio'), h('strong', null, 'No clear match'), h('em', null, 'This is allowed to be irrelevant'))])
      ),
      h('span', { className: 'map-link', 'aria-hidden': true }, '→'),
      h('div', { className: 'map-node action-node' }, h('small', null, 'Next move'), h('strong', null, action))
    ),
    h('div', { className: 'evidence-branches' },
      h('span', null, 'Evidence'),
      ...(evidence.length ? evidence.map((origin) => h('span', { key: origin }, origin)) : [h('span', { key: 'none' }, 'No origin yet')])
    ),
    h('div', { className: 'core-idea-branches' },
      h('span', null, 'Core ideas'),
      ...(ideas.length ? ideas.map((idea) => h('div', { className: 'core-idea', key: `${idea.project_id}-${idea.id}` },
        h('strong', null, idea.name),
        h('small', null, idea.project_name),
        idea.description ? h('p', null, idea.description) : null,
        h('em', null, (idea.matched_terms || []).join(' · '))
      )) : [h('div', { className: 'core-idea empty', key: 'none' }, h('strong', null, 'No core-idea match'), h('small', null, 'Irrelevance is allowed'))])
    )
  );
}

function UsefulnessDial({ usefulness }) {
  const score = Number(usefulness?.score || 0);
  const band = usefulness?.band || 'skip';
  return h('div', { className: `usefulness-dial band-${band}`, style: { '--score': `${score * 3.6}deg` }, 'aria-label': `Estimated usefulness ${score} out of 100` },
    h('div', null, h('strong', null, score), h('small', null, '/100')),
    h('span', null, bandLabel[band] || band)
  );
}

function TrendCard({ trend, index, period, brain, capture, onCapture }) {
  const origins = trend.origins || [];
  const usefulness = trend.usefulness || { score: 0, band: 'skip', reasons: [], project_matches: [] };
  const tone = trend.verification === 'corroborated-primary' ? 'verified' :
    trend.verification === 'owner-priority-unverified' ? 'owner' : 'neutral';
  const summary = cleanText((trend.signals || []).find((signal) => signal.summary)?.summary || 'No summary supplied. Review the evidence before relying on this signal.');
  return h('article', { className: `trend-card band-${usefulness.band}` },
    h('div', { className: 'trend-rank' }, h('span', null, 'Rank'), h('strong', null, String(index + 1).padStart(2, '0'))),
    h('div', { className: 'trend-main' },
      h('div', { className: 'trend-topline' },
        h('div', { className: 'tag-row' },
          h(Pill, { tone: usefulness.band || 'neutral' }, `${bandLabel[usefulness.band] || 'Skip'} · ${usefulness.confidence || 'low'} confidence`),
          h(Pill, { tone }, verificationLabel[trend.verification] || trend.verification || 'Lead'),
          usefulness.research_needed ? h(Pill, { tone: 'research' }, 'Research needed') : null
        ),
        h('span', { className: 'trend-score' }, `${Number(trend.score || 0).toFixed(1)} signal strength`)
      ),
      h('div', { className: 'title-grid' },
        h('div', null, h('h2', null, trend.title), h('p', { className: 'trend-summary' }, summary)),
        h(UsefulnessDial, { usefulness })
      ),
      h(ProjectFitMap, { trend }),
      h('div', { className: 'reason-grid' },
        h('div', null, h('span', { className: 'mini-label' }, 'Why it landed here'), h('ul', null, ...(usefulness.reasons || []).map((reason) => h('li', { key: reason }, reason)))),
        h('div', { className: 'next-action' },
          h('span', { className: 'mini-label' }, 'Recommendation'),
          h('p', null, usefulness.next_action || trend.recommendation),
          h('button', {
            className: 'brain-button',
            disabled: !brain.writable || !trend.id || capture?.state === 'busy' || capture?.state === 'done',
            onClick: () => onCapture(period, trend.id),
            title: brain.message,
          }, capture?.state === 'busy' ? 'Staging…' : capture?.state === 'done' ? 'In the Atlas review queue ✓' : brain.writable ? 'Move to Atlas review queue' : 'Connect Observatory'),
          capture?.message ? h('small', { className: `capture-message ${capture.state}` }, capture.message) : null
        )
      ),
      h('div', { className: 'origin-row' },
        h('span', null, `${trend.signal_count ?? trend.signals?.length ?? 0} signals`),
        h('span', null, `${origins.length} origins`),
        ...origins.slice(0, 4).map((origin) => h('span', { className: 'origin-chip', key: origin }, origin))
      ),
      h('details', { className: 'evidence' },
        h('summary', null, `Open evidence ${trend.signals?.length ? `(${trend.signals.length})` : ''}`),
        h('div', { className: 'signal-list' }, ...(trend.signals || []).map((signal, i) => h(SignalRow, { signal, key: `${signal.url}-${i}` })))
      )
    )
  );
}

function XPanel({ x }) {
  const status = x || {};
  const enabled = Boolean(status.enabled);
  const spend = Number(status.estimated_spend_this_week_usd || 0);
  const budget = Number(status.weekly_budget_usd || 0);
  const pct = budget > 0 ? Math.min(100, spend / budget * 100) : 0;
  return h('section', { className: 'side-panel x-panel' },
    h('div', { className: 'panel-heading' },
      h('div', null, h('span', { className: 'eyebrow' }, 'Optional input'), h('h3', null, enabled ? 'X bookmarks connected' : 'X polling is off')),
      h(Pill, { tone: enabled ? 'verified' : 'neutral' }, enabled ? 'Live' : '$0 default')
    ),
    h('p', null, enabled ? `${status.bookmarks?.length || 0} bookmarks are available as intent signals.` : 'Share Sheet capture remains free. Official polling needs OAuth and an explicit nonzero budget.'),
    h('div', { className: 'budget-line' }, h('span', null, `$${spend.toFixed(3)} / $${budget.toFixed(2)}`), h('span', null, `${status.resources_read_this_week || 0} reads`)),
    h('div', { className: 'progress' }, h('span', { style: { width: `${pct}%` } }))
  );
}

function EmptyState({ loading, error }) {
  return h('div', { className: 'empty-state' }, h('div', { className: 'radar-orb' }), h('h2', null, loading ? 'Loading the radar…' : error ? 'Dashboard data unavailable' : 'No items in this band'), h('p', null, error || (loading ? 'Reading generated reports.' : 'Try a different filter, or run discovery to refresh the report.')));
}

export default function App() {
  const [period, setPeriod] = useState('daily');
  const [data, setData] = useState({ daily: null, weekly: null, x: null, inbox: null });
  const [query, setQuery] = useState('');
  const [band, setBand] = useState('attention');
  const [verification, setVerification] = useState('all');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [brain, setBrain] = useState({ connected: false, writable: false, name: 'Observatory', message: 'Checking local connection…' });
  const [captures, setCaptures] = useState({});

  useEffect(() => {
    let active = true;
    Promise.all([getJson('daily.json'), getJson('weekly.json'), getJson('x-bookmarks.json'), getJson('shared-inbox.json')])
      .then(([daily, weekly, x, inbox]) => active && setData({ daily, weekly, x, inbox }))
      .catch((err) => active && setError(err.message))
      .finally(() => active && setLoading(false));
    return () => { active = false; };
  }, []);

  useEffect(() => { getBrainStatus().then(setBrain); }, []);

  async function captureTrend(selectedPeriod, trendId) {
    setCaptures((current) => ({ ...current, [trendId]: { state: 'busy', message: 'Creating a review candidate…' } }));
    try {
      const response = await fetch('/api/brain/candidates', {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ period: selectedPeriod, trendId }),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || `HTTP ${response.status}`);
      setCaptures((current) => ({ ...current, [trendId]: { state: 'done', message: result.path } }));
    } catch (captureError) {
      setCaptures((current) => ({ ...current, [trendId]: { state: 'error', message: captureError.message } }));
    }
  }

  const report = data[period] || { trends: [], projects: [] };
  const trends = report.trends || [];
  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return trends.filter((trend) => {
      if (band === 'attention' && trend.usefulness?.band === 'skip') return false;
      if (!['all', 'attention'].includes(band) && trend.usefulness?.band !== band) return false;
      if (verification !== 'all' && trend.verification !== verification) return false;
      if (!needle) return true;
      const corpus = [trend.title, trend.recommendation, ...(trend.origins || []), ...(trend.usefulness?.project_matches || []).flatMap((p) => [p.name, ...(p.matched_terms || [])]), ...(trend.signals || []).flatMap((s) => [s.title, s.summary, s.source, s.watch])].join(' ').toLowerCase();
      return corpus.includes(needle);
    });
  }, [trends, query, band, verification]);

  const counts = Object.fromEntries(['act', 'evaluate', 'watch', 'skip'].map((key) => [key, trends.filter((trend) => trend.usefulness?.band === key).length]));
  const aidb = trends.filter((trend) => (trend.origins || []).includes('editorial:ai-daily-brief')).length;

  return h('div', { className: 'app-shell' },
    h('header', { className: 'topbar' },
      h('div', { className: 'brand' }, h('div', { className: 'brand-mark' }, h('span')), h('div', null, h('strong', null, 'AI Radar'), h('small', null, 'project-fit intelligence'))),
      h('div', { className: 'topbar-meta' }, h('span', { className: 'live-dot' }), h('span', null, report.generated_at ? `Updated ${shortDate(report.generated_at)}` : 'Awaiting run'))
    ),
    h('main', { className: 'layout' },
      h('section', { className: 'hero' },
        h('div', null, h('span', { className: 'eyebrow' }, 'Signal → project → action'), h('h1', null, 'Useful to what you are building?'), h('p', null, 'A project-fit estimate separates strong news from things that deserve your time. “Skip” is a healthy outcome; evidence strength alone cannot manufacture relevance.')),
        h('div', { className: 'period-switch', role: 'tablist' }, ...['daily', 'weekly'].map((key) => h('button', { key, className: period === key ? 'active' : '', onClick: () => setPeriod(key) }, key === 'daily' ? 'Today' : '7 days')))
      ),
      h('section', { className: 'metrics-grid' },
        h(Metric, { label: 'Act now', value: counts.act, detail: 'high project fit + evidence', tone: 'act' }),
        h(Metric, { label: 'Evaluate', value: counts.evaluate, detail: 'promising, verify first', tone: 'evaluate' }),
        h(Metric, { label: 'Watch / skip', value: counts.watch + counts.skip, detail: `${counts.skip} explicitly irrelevant`, tone: 'watch' }),
        h(Metric, { label: 'AI Daily Brief', value: aidb, detail: 'always-on editorial leads', tone: 'brief' })
      ),
      h('div', { className: 'content-grid' },
        h('section', { className: 'feed' },
          h('div', { className: 'feed-tools' },
            h('label', { className: 'search-box' }, h('span', null, '⌕'), h('input', { value: query, onChange: (e) => setQuery(e.target.value), placeholder: 'Search tools, projects, evidence…', 'aria-label': 'Search' })),
            h('select', { value: band, onChange: (e) => setBand(e.target.value), 'aria-label': 'Filter usefulness' },
              h('option', { value: 'attention' }, `Needs attention (${counts.act + counts.evaluate + counts.watch})`),
              h('option', { value: 'all' }, `All items (${trends.length})`),
              ...['act', 'evaluate', 'watch', 'skip'].map((key) => h('option', { key, value: key }, `${bandLabel[key]} (${counts[key]})`))
            ),
            h('select', { value: verification, onChange: (e) => setVerification(e.target.value), 'aria-label': 'Filter verification' }, h('option', { value: 'all' }, 'All evidence'), ...Object.entries(verificationLabel).map(([key, label]) => h('option', { key, value: key }, label)))
          ),
          h('div', { className: 'feed-caption' }, h('span', null, `${filtered.length} of ${trends.length} items`), h('span', null, 'Usefulness is a transparent estimate—not a claim of ROI.')),
          loading || error || filtered.length === 0 ? h(EmptyState, { loading, error }) : h('div', { className: 'trend-list' }, ...filtered.map((trend, index) => h(TrendCard, { trend, index, period, brain, capture: captures[trend.id], onCapture: captureTrend, key: trend.id || `${trend.title}-${index}` })))
        ),
        h('aside', { className: 'sidebar' },
          h('section', { className: 'side-panel brief-panel' }, h('span', { className: 'eyebrow' }, 'Always on'), h('h3', null, 'The AI Daily Brief'), h('p', null, 'Every official machine-readable edition enters as editorial discovery. It can suggest research, but never counts as primary verification.'), h('a', { href: 'https://www.aidailybrief.ai/', target: '_blank', rel: 'noreferrer' }, 'Open the official brief ↗')),
          h('section', { className: 'side-panel portfolio-panel' }, h('span', { className: 'eyebrow' }, 'Fit model'), h('h3', null, `${report.projects?.length || 0} configured projects`), h('p', null, 'Edit config/projects.json. Specific goals and keywords make the ranking more discriminating.'), h('div', { className: 'portfolio-list' }, ...(report.projects || []).map((project) => h('div', { key: project.id }, h('strong', null, project.name), h('span', null, project.goals?.[0] || project.description))))),
          h('section', { className: 'side-panel brain-panel' }, h('span', { className: 'eyebrow' }, 'Review queue'), h('h3', null, brain.connected ? 'Observatory connected' : 'Connect Observatory'), h('p', null, brain.message), h(Pill, { tone: brain.writable ? 'verified' : 'neutral' }, brain.writable ? 'Staging enabled' : 'No write access')),
          h(XPanel, { x: data.x }),
          h('section', { className: 'side-panel trust-panel' }, h('span', { className: 'eyebrow' }, 'Trust boundary'), h('h3', null, 'Evidence, never instructions'), h('p', null, 'External content cannot change policy, trigger tools, expose secrets, or promote durable knowledge. Editorial and personal signals require primary research before adoption.'))
        )
      )
    )
  );
}
