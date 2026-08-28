# Migration mapping

Use this reference only when an existing knowledge or project system is in scope.

## Inventory levels

1. **Structure:** authorized roots, formats, counts, folder names, repository names, and modification dates.
2. **Classification sample:** representative titles, frontmatter/metadata, README summaries, and link patterns.
3. **Content analysis:** only the files needed to resolve mappings, duplicates, conflicts, provenance, or owner priorities.

Skip secrets, dependency/vendor folders, build outputs, Git internals, caches, generated indexes, binaries without a supported reader, and anything outside the authorized roots.

## Default Observatory mappings

| Existing material | Observatory destination | Guidance |
|---|---|---|
| Active initiative, product, client-safe workstream, or repository group | `Project` | Link repositories and related knowledge; do not copy source code into the corpus. |
| Topic note or evergreen explanation | `Concept` | Merge duplicates and preserve uncertainty. |
| Article, paper, video, podcast episode, dataset, or conversation reference | `Source` | Preserve provenance and stable resource identifiers. |
| Deep, reusable multi-source analysis | `ResearchDossier` | Keep mechanisms, disagreement, failure modes, and open questions. |
| Person or organization important to the graph | `Person` | Record only owner-approved, relevant context. |
| Original hypothesis or product thought | `Idea` | Do not present it as externally verified fact. |
| Unresolved investigation | `Question` | Link the project and evidence that make it important. |
| Tasks, transient status, build output, cache, or runtime memory | `.ops/`, staging, or external link | Keep temporary state out of canonical knowledge. |

OKF types are open, but prefer the local ontology unless a distinct type creates durable value. Treat “assets” according to meaning: a tool/product generally becomes a Concept or Source; a company can be a Person/organization; a repository usually belongs to a Project; a media feed belongs in Radar configuration.

## Preview format

Provide a compact table with: source class, count, proposed type/path, copy/link/skip decision, provenance plan, and risks. Include 3–5 representative mappings and call out ambiguous examples separately.

## Migration execution

- Keep the source unchanged.
- Write candidates beneath `staging/migration/` first.
- Preserve source locations without exposing machine-specific absolute paths in shareable output.
- Normalize filenames only in the staged destination.
- Link related cards with ordinary relative Markdown links.
- Never infer human verification from ownership, age, or repetition.
- Promote only after validation and owner review.
