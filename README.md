# AI Radar

**A reviewable, local-first scout for AI developments that matter to your projects.**

AI Radar combines scheduled public-source discovery, transparent ranking and clustering, optional iPhone Share Sheet capture, and a responsive React dashboard. Retrieved content is untrusted evidence and never receives authority over tools, credentials, policy, or durable knowledge.

This is a fresh-history public scaffold with synthetic configuration only. It contains no collected reports, watch history, bookmarks, credentials, account identifiers, or private project connections.

## What it does

- Collects configured arXiv, Hacker News, GitHub, first-party, and RSS signals with source-fault isolation.
- Separates signal strength from estimated project usefulness.
- Produces reviewable daily and weekly reports without committing generated data.
- Shows evidence, filters, watch targets, and trust boundaries in a loopback-only dashboard.
- Can stage an explicit review candidate in a local Observatory checkout; it never silently promotes external content.
- Keeps official X bookmark ingestion disabled by default with a `$0.00` weekly software budget.

## Quick start

Requirements: Python 3.12+ and Node.js 22.12+.

```sh
git clone https://github.com/OWNER/ai-radar.git
cd ai-radar
python3.12 -m unittest discover -s tests -v
python3.12 -m radar.report --help
cd dashboard
npm ci
npm run check
npm test
npm run build
```

Run the dashboard without credentials:

```sh
cd dashboard
npm start
```

Open <http://127.0.0.1:4174>. Generated reports and dashboard data remain ignored by Git. Follow [START-HERE.md](START-HERE.md) to replace the synthetic watchlist and project examples.

## Privacy and trust boundary

Keep a configured repository private if you enable personal captures or bookmarks. The default GitHub workflow uses read-only repository permissions and uploads artifacts; it does not push generated reports. Fork pull requests receive no repository secrets, and retrieved source text is never executed as instruction.

## License

MIT. See [LICENSE](LICENSE).
