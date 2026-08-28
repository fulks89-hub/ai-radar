from __future__ import annotations

import datetime as dt
import re
from dataclasses import asdict, dataclass

from radar.rank import age_days

WORD_RE = re.compile(r"[a-z0-9]+")
ACTION_TERMS = {
    "api", "benchmark", "build", "cli", "code", "dataset", "demo", "deploy",
    "framework", "github", "guide", "integration", "library", "open source",
    "release", "repository", "sdk", "store", "tool", "tutorial", "workflow",
}
EVIDENCE_POINTS = {
    "corroborated-primary": 20,
    "primary-plus-discussion": 17,
    "single-primary": 14,
    "owner-priority-unverified": 7,
    "unverified-lead": 4,
}
SOURCE_ACTION_POINTS = {
    "github-release": 12,
    "github-commit": 10,
    "official-page": 8,
    "official-rss": 8,
    "arxiv": 6,
    "editorial-brief": 4,
    "owner-share": 5,
    "x-bookmark": 4,
}


@dataclass(frozen=True)
class ProjectMatch:
    id: str
    name: str
    score: int
    matched_terms: list[str]
    goal: str


@dataclass(frozen=True)
class CoreIdeaMatch:
    id: str
    name: str
    project_id: str
    project_name: str
    matched_terms: list[str]
    description: str


@dataclass(frozen=True)
class UsefulnessAssessment:
    score: int
    band: str
    confidence: str
    project_matches: list[ProjectMatch]
    core_idea_matches: list[CoreIdeaMatch]
    reasons: list[str]
    next_action: str
    research_needed: bool

    def to_dict(self) -> dict:
        return asdict(self)


def _tokens(text: str) -> set[str]:
    return {token for token in WORD_RE.findall(text.lower()) if len(token) > 2}


def _project_exclusions(project: dict, corpus: str) -> list[str]:
    terms = [str(value).strip().lower() for value in project.get("exclude_keywords", [])]
    return sorted({term for term in terms if term and term in corpus})


def match_projects(text: str, projects: list[dict]) -> list[ProjectMatch]:
    corpus = text.lower()
    corpus_tokens = _tokens(text)
    matches: list[ProjectMatch] = []
    for project in projects:
        if _project_exclusions(project, corpus):
            continue
        keywords = [str(value).strip().lower() for value in project.get("keywords", [])]
        hits = sorted({keyword for keyword in keywords if keyword and keyword in corpus})
        goals = [str(value).strip() for value in project.get("goals", []) if str(value).strip()]
        goal_text = " ".join(goals)
        goal_overlap = len(corpus_tokens & _tokens(goal_text))
        if not hits:
            continue
        keyword_points = sum(55 if " " in keyword else 30 for keyword in hits)
        score = min(100, keyword_points + min(goal_overlap, 5) * 4)
        if score <= 0:
            continue
        matches.append(
            ProjectMatch(
                id=str(project.get("id") or project.get("name") or "project"),
                name=str(project.get("name") or "Unnamed project"),
                score=score,
                matched_terms=hits[:4],
                goal=goals[0] if goals else str(project.get("description") or ""),
            )
        )
    return sorted(matches, key=lambda row: (-row.score, row.name))


def match_core_ideas(text: str, projects: list[dict]) -> list[CoreIdeaMatch]:
    corpus = text.lower()
    matches: list[CoreIdeaMatch] = []
    for project in projects:
        if _project_exclusions(project, corpus):
            continue
        project_id = str(project.get("id") or project.get("name") or "project")
        project_name = str(project.get("name") or "Unnamed project")
        for index, idea in enumerate(project.get("core_ideas", [])):
            if isinstance(idea, str):
                name = idea.strip()
                description = ""
                keywords = [name.lower()]
                idea_id = f"{project_id}-idea-{index + 1}"
            else:
                name = str(idea.get("name") or "").strip()
                description = str(idea.get("description") or "").strip()
                keywords = [str(value).strip().lower() for value in idea.get("keywords", [])]
                idea_id = str(idea.get("id") or f"{project_id}-idea-{index + 1}")
            hits = sorted({keyword for keyword in keywords if keyword and keyword in corpus})
            if not name or not hits:
                continue
            matches.append(CoreIdeaMatch(
                id=idea_id,
                name=name,
                project_id=project_id,
                project_name=project_name,
                matched_terms=hits[:5],
                description=description,
            ))
    return sorted(matches, key=lambda row: (row.project_name, row.name))


def _freshness_points(signals: list, now: dt.datetime) -> int:
    ages = [age_days(signal.published, now) for signal in signals]
    known = [age for age in ages if age is not None]
    if not known:
        return 0
    youngest = min(known)
    if youngest <= 1:
        return 5
    if youngest <= 3:
        return 4
    if youngest <= 7:
        return 3
    if youngest <= 30:
        return 1
    return 0


def assess_usefulness(
    *,
    title: str,
    signals: list,
    verification: str,
    projects: list[dict],
    now: dt.datetime | None = None,
) -> UsefulnessAssessment:
    now = now or dt.datetime.now(dt.timezone.utc)
    text = " ".join(
        [title]
        + [f"{signal.title} {signal.summary} {signal.reason}" for signal in signals]
    )
    project_matches = match_projects(text, projects)
    core_idea_matches = match_core_ideas(text, projects)
    excluded_projects = [
        (str(project.get("name") or "Unnamed project"), _project_exclusions(project, text.lower()))
        for project in projects
        if _project_exclusions(project, text.lower())
    ]
    top_fit = project_matches[0].score if project_matches else 0
    fit_points = round(top_fit * 0.5)
    evidence_points = EVIDENCE_POINTS.get(verification, 3)
    action_points = max((SOURCE_ACTION_POINTS.get(signal.source, 2) for signal in signals), default=0)
    lower_text = text.lower()
    if any(term in lower_text for term in ACTION_TERMS):
        action_points = min(15, action_points + 4)
    intent_points = 0
    if any(signal.authority == "owner" for signal in signals):
        intent_points = 10
    elif any(signal.watch for signal in signals):
        intent_points = 6
    freshness_points = _freshness_points(signals, now)
    score = min(100, fit_points + evidence_points + action_points + intent_points + freshness_points)

    # Evidence strength cannot substitute for relevance. Without a configured project
    # match, a signal may be worth watching but cannot be called useful to the portfolio.
    if not project_matches:
        score = min(score, 49)
    if any(signal.authority == "owner" for signal in signals):
        score = max(score, 35)
    elif any(signal.watch for signal in signals):
        score = max(score, 35)

    if score >= 75:
        band = "act"
    elif score >= 55:
        band = "evaluate"
    elif score >= 35:
        band = "watch"
    else:
        band = "skip"

    confidence = "high" if project_matches and evidence_points >= 17 else (
        "medium" if project_matches or evidence_points >= 14 else "low"
    )
    reasons: list[str] = []
    if project_matches:
        top = project_matches[0]
        terms = ", ".join(top.matched_terms) if top.matched_terms else "goal-language overlap"
        reasons.append(f"Matches {top.name}: {terms}")
    else:
        reasons.append("No direct match to the configured projects")
    for project_name, terms in excluded_projects[:3]:
        reasons.append(f"Excluded from {project_name}: {', '.join(terms[:3])}")
    if core_idea_matches:
        ideas = ", ".join(match.name for match in core_idea_matches[:3])
        reasons.append(f"Connects to core ideas: {ideas}")
    reasons.append(f"Evidence: {verification.replace('-', ' ')}")
    reasons.append(f"Actionability: {action_points}/15")
    if intent_points:
        reasons.append("Explicit share or configured watch raised attention, not verification")

    target = project_matches[0].name if project_matches else "the current portfolio"
    if band == "act":
        next_action = f"Prototype or apply this against {target}."
    elif band == "evaluate":
        next_action = f"Compare the primary evidence with {target} before adopting it."
    elif band == "watch":
        next_action = "Keep monitoring; there is not yet enough project fit or evidence to act."
    else:
        next_action = "Skip for now; no concrete project benefit is visible."

    research_needed = verification in {"owner-priority-unverified", "unverified-lead"} or all(
        signal.authority != "primary" for signal in signals
    )
    return UsefulnessAssessment(
        score=score,
        band=band,
        confidence=confidence,
        project_matches=project_matches,
        core_idea_matches=core_idea_matches,
        reasons=reasons,
        next_action=next_action,
        research_needed=research_needed,
    )
