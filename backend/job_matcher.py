"""
AI Job Matcher Module
Matches candidates to the best-fit job postings based on skills, experience,
and AI-powered analysis. This replaces the old static job_description matching.
"""

import os
import json
import logging
import math
import re
import threading
from typing import Dict, List, Optional
import httpx

logger = logging.getLogger(__name__)


class JobMatcher:
    """
    AI-powered candidate-to-job matching engine.
    Compares candidate skills/experience against all active job postings
    and returns ranked matches.
    """

    def __init__(self, api_key: Optional[str] = None):
        # Resolve key: explicit arg > env var
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.model = "gpt-4o-mini"
        self.client = None

        if self.api_key:
            http_client = None
            try:
                from openai import OpenAI
                http_client = httpx.Client(timeout=30.0)
                self.client = OpenAI(api_key=self.api_key, http_client=http_client)
            except TypeError as e:
                if http_client is not None:
                    http_client.close()
                if "proxies" in str(e):
                    proxy = (
                        os.environ.get("HTTPS_PROXY")
                        or os.environ.get("https_proxy")
                        or os.environ.get("HTTP_PROXY")
                        or os.environ.get("http_proxy")
                    )
                    http_client = httpx.Client(
                        proxy=proxy,
                        timeout=30.0,
                    )
                    from openai import OpenAI
                    try:
                        self.client = OpenAI(
                            api_key=self.api_key, http_client=http_client
                        )
                    except Exception:
                        http_client.close()
                        raise
                else:
                    raise
            except Exception:
                if http_client is not None:
                    http_client.close()
                raise

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def match_candidate_to_jobs(
        self,
        candidate_skills: List[str],
        candidate_experience: int,
        candidate_education: str,
        resume_text: str,
        active_jobs: List[Dict],
    ) -> List[Dict]:
        """
        Match a candidate against a list of active job postings.

        Returns a list of dicts sorted by match_score DESC:
        [
            {
                "job_id": 3,
                "match_score": 87,
                "skill_match_score": 90,
                "experience_match_score": 80,
                "ai_reasoning": "Strong alignment …"
            },
            …
        ]
        """
        if not active_jobs:
            logger.info("[JOB_MATCHER] No active jobs to match against")
            return []

        candidate_skills = self._parse_skills(candidate_skills)
        candidate_experience = self._non_negative_number(candidate_experience)

        # Step 1 — rule-based scoring for every valid job
        matches = []
        for job in active_jobs:
            if not isinstance(job, dict) or not self._positive_job_id(job.get("id")):
                logger.warning("[JOB_MATCHER] Skipping malformed job without a valid id")
                continue
            rule_score = self._rule_based_score(
                candidate_skills, candidate_experience, job
            )
            matches.append({**rule_score, "job": job})

        # Step 2 — AI re-rank top 5 candidates (cost-efficient)
        top_matches = sorted(matches, key=lambda m: m["match_score"], reverse=True)[:5]

        if self.client and resume_text:
            try:
                ai_matches = self._ai_rerank(
                    candidate_skills,
                    candidate_experience,
                    candidate_education,
                    resume_text,
                    [m["job"] for m in top_matches],
                )
                # Merge AI scores
                valid_job_ids = {m["job"]["id"] for m in top_matches}
                ai_map = self._validated_ai_matches(ai_matches, valid_job_ids)
                for m in top_matches:
                    jid = m["job"]["id"]
                    if jid in ai_map:
                        # Weighted blend: 40% rule + 60% AI
                        ai = ai_map[jid]
                        m["match_score"] = self._bounded_score(
                            0.4 * m["match_score"] + 0.6 * ai["match_score"]
                        )
                        m["ai_reasoning"] = ai.get("ai_reasoning", "")
            except Exception as e:
                logger.warning(f"[JOB_MATCHER] AI reranking failed: {e}. Using rule-based scores.")

        # Final sort and clean
        # AI only reranks the top five, but every active job must remain in the
        # result so persistence can replace stale matches deterministically.
        results = sorted(matches, key=lambda m: m["match_score"], reverse=True)
        return [
            {
                "job_id": m["job"]["id"],
                "job_title": m["job"].get("title", ""),
                "match_score": m["match_score"],
                "skill_match_score": m["skill_match_score"],
                "experience_match_score": m["experience_match_score"],
                "ai_reasoning": m.get("ai_reasoning", "Rule-based match"),
            }
            for m in results
        ]

    def get_best_match(
        self,
        candidate_skills: List[str],
        candidate_experience: int,
        candidate_education: str,
        resume_text: str,
        active_jobs: List[Dict],
    ) -> Optional[Dict]:
        """Return the single best job match, or None."""
        matches = self.match_candidate_to_jobs(
            candidate_skills, candidate_experience, candidate_education,
            resume_text, active_jobs
        )
        return matches[0] if matches else None

    # ------------------------------------------------------------------
    # Rule-based scoring
    # ------------------------------------------------------------------

    def _rule_based_score(
        self,
        candidate_skills: List[str],
        candidate_experience: int,
        job: Dict,
    ) -> Dict:
        """Compute deterministic skill + experience match scores."""
        # Parse job skills
        required_skills = {
            self._normalise_skill(skill)
            for skill in self._parse_skills(job.get("required_skills", ""))
        }
        preferred_skills = {
            self._normalise_skill(skill)
            for skill in self._parse_skills(job.get("preferred_skills", ""))
        }
        required_skills.discard("")
        preferred_skills.discard("")
        preferred_skills -= required_skills
        candidate_skill_set = {
            self._normalise_skill(skill) for skill in candidate_skills
        }
        candidate_skill_set.discard("")

        # Skill match — required skills have 2× weight
        req_matched = len(required_skills & candidate_skill_set)
        pref_matched = len(preferred_skills & candidate_skill_set)
        if required_skills and preferred_skills:
            skill_score = self._bounded_score(
                (req_matched / len(required_skills)) * 75
                + (pref_matched / len(preferred_skills)) * 25
            )
        elif required_skills:
            skill_score = self._bounded_score(
                (req_matched / len(required_skills)) * 100
            )
        elif preferred_skills:
            skill_score = self._bounded_score(
                (pref_matched / len(preferred_skills)) * 100
            )
        else:
            skill_score = 0

        # Experience match
        min_exp = self._non_negative_number(job.get("min_experience"))
        raw_max_exp = job.get("max_experience")
        max_exp = (
            self._non_negative_number(raw_max_exp)
            if raw_max_exp is not None
            else min_exp + 10
        )
        max_exp = max(min_exp, max_exp)
        if candidate_experience >= min_exp and candidate_experience <= max_exp:
            exp_score = 100
        elif candidate_experience < min_exp:
            gap = min_exp - candidate_experience
            exp_score = max(0, 100 - gap * 20)
        else:
            overshoot = candidate_experience - max_exp
            exp_score = max(50, 100 - overshoot * 10)  # Overqualified but not terrible
        exp_score = self._bounded_score(exp_score)

        # Experience level match
        level = str(job.get("experience_level") or "mid").strip().lower()
        level_ranges = {
            "junior": (0, 2), "mid": (2, 5), "senior": (5, 10),
            "lead": (8, 15), "principal": (12, 25)
        }
        lo, hi = level_ranges.get(level, (0, 99))
        level_bonus = 10 if lo <= candidate_experience <= hi else 0

        overall = self._bounded_score(
            skill_score * 0.6 + exp_score * 0.3 + level_bonus
        )

        return {
            "match_score": overall,
            "skill_match_score": skill_score,
            "experience_match_score": exp_score,
            "ai_reasoning": "",
        }

    # ------------------------------------------------------------------
    # AI reranking
    # ------------------------------------------------------------------

    def _ai_rerank(
        self,
        candidate_skills: List[str],
        candidate_experience: int,
        candidate_education: str,
        resume_text: str,
        jobs: List[Dict],
    ) -> List[Dict]:
        """Use GPT to rerank the top job matches with reasoning."""
        jobs_desc = "\n".join(
            f"JOB #{j['id']}: {j.get('title','')} | "
            f"Required: {j.get('required_skills','')} | "
            f"Preferred: {j.get('preferred_skills','')} | "
            f"Experience: {j.get('min_experience',0)}-{j.get('max_experience','N/A')} yrs | "
            f"Level: {j.get('experience_level','mid')} | "
            f"Dept: {j.get('department','')}"
            for j in jobs
        )

        prompt = f"""You are an expert HR recruiter. Rank how well this candidate matches each job.

CANDIDATE:
- Skills: {', '.join(candidate_skills[:20])}
- Experience: {candidate_experience} years
- Education: {candidate_education}
- Resume excerpt: {resume_text[:600]}

JOBS:
{jobs_desc}

Return a JSON array sorted by best match first. Each element:
{{
  "job_id": <int>,
  "match_score": <0-100>,
  "ai_reasoning": "<2-sentence explanation>"
}}

Consider:
1. Skill alignment (required > preferred)
2. Experience level appropriateness (don't rank a junior candidate high for senior roles)
3. Domain/industry fit
4. Overqualification penalty (senior applying for junior)

Respond ONLY with valid JSON array, no extra text."""

        # NOTE: response_format=json_object requires a top-level JSON object (not an array).
        # We instruct the model to wrap in {"matches": [...]} and unwrap below.
        prompt = prompt.replace(
            "Respond ONLY with valid JSON array, no extra text.",
            "Respond ONLY with valid JSON in this format: {\"matches\": [<array of match objects>]}, no extra text."
        )

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are an expert recruiter. Respond only with valid JSON."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,  # Low temperature for consistent matching
            max_tokens=800,
            seed=42,  # Fixed seed for reproducibility
            response_format={"type": "json_object"},
        )

        result = json.loads(response.choices[0].message.content)
        # Unwrap envelope: support {"matches": [...]}, {"rankings": [...]}, or bare list
        if isinstance(result, dict):
            result = result.get("matches", result.get("rankings", list(result.values())[0] if result else []))
        return result if isinstance(result, list) else []

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_skills(skills_value) -> List[str]:
        """Parse skills from various storage formats."""
        if not skills_value:
            return []
        if isinstance(skills_value, (list, tuple, set)):
            values = skills_value
            return list(dict.fromkeys(
                str(value).strip() for value in values if str(value).strip()
            ))[:100]
        try:
            parsed = json.loads(skills_value)
        except (json.JSONDecodeError, TypeError):
            parsed = None
        if parsed is not None:
            if isinstance(parsed, list):
                return list(dict.fromkeys(
                    str(value).strip() for value in parsed if str(value).strip()
                ))[:100]
            if isinstance(parsed, str):
                skills_value = parsed
            else:
                return []
        # Comma-separated string
        values = re.split(r"[,;\n]", str(skills_value))
        return list(dict.fromkeys(value.strip() for value in values if value.strip()))[:100]

    @staticmethod
    def _normalise_skill(value) -> str:
        normalised = re.sub(r"[^a-z0-9+#]+", "", str(value).strip().lower())
        aliases = {
            "js": "javascript",
            "ts": "typescript",
            "reactjs": "react",
            "nodejs": "node",
            "node": "node",
            "py": "python",
            "csharp": "c#",
            "dotnet": "net",
        }
        return aliases.get(normalised, normalised)

    @staticmethod
    def _non_negative_number(value) -> float:
        try:
            number = float(value or 0)
        except (TypeError, ValueError):
            return 0.0
        return number if math.isfinite(number) and number >= 0 else 0.0

    @staticmethod
    def _positive_job_id(value) -> bool:
        try:
            return int(value) > 0
        except (TypeError, ValueError):
            return False

    @staticmethod
    def _bounded_score(value) -> int:
        try:
            score = float(value)
        except (TypeError, ValueError):
            return 0
        if not math.isfinite(score):
            return 0
        return int(round(min(100, max(0, score))))

    @classmethod
    def _validated_ai_matches(cls, matches, allowed_job_ids):
        validated = {}
        if not isinstance(matches, list):
            return validated
        for match in matches:
            if not isinstance(match, dict):
                continue
            try:
                job_id = int(match.get("job_id"))
            except (TypeError, ValueError):
                continue
            if job_id not in allowed_job_ids or job_id in validated:
                continue
            reasoning = str(match.get("ai_reasoning") or "").strip()[:1000]
            validated[job_id] = {
                "job_id": job_id,
                "match_score": cls._bounded_score(match.get("match_score")),
                "ai_reasoning": reasoning,
            }
        return validated

    def close(self):
        """Release network resources owned by the OpenAI client."""
        if self.client and hasattr(self.client, "close"):
            self.client.close()


# Module-level convenience — refreshed automatically if OPENAI_API_KEY changes at runtime
_matcher_instance = None
_matcher_api_key = None
_matcher_lock = threading.Lock()


def get_job_matcher() -> JobMatcher:
    """Get or create the JobMatcher singleton.
    
    Re-creates the instance if the OPENAI_API_KEY environment variable has
    changed since the last call (e.g., set via the admin settings page).
    """
    global _matcher_instance, _matcher_api_key
    current_key = os.environ.get("OPENAI_API_KEY")
    with _matcher_lock:
        if _matcher_instance is None or current_key != _matcher_api_key:
            if _matcher_instance is not None:
                try:
                    _matcher_instance.close()
                except Exception:
                    logger.warning(
                        "[JOB_MATCHER] Failed to close the previous matcher client",
                        exc_info=True,
                    )
            _matcher_instance = JobMatcher()
            _matcher_api_key = current_key
    return _matcher_instance


def match_candidate_to_jobs(candidate_skills, candidate_experience,
                            candidate_education, resume_text, active_jobs):
    """Convenience wrapper."""
    return get_job_matcher().match_candidate_to_jobs(
        candidate_skills, candidate_experience, candidate_education,
        resume_text, active_jobs
    )
