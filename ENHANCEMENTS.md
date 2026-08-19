# Enhancement Plan — AI Analytics Engineering Upgrade

Goal: evolve the project from "working AI pipeline" to "measured, production-framed
AI semantic infrastructure" for AI Analytics Engineer positioning. Order matters:
measurement before presentation, so the presentation has true numbers to show.

## Phase A — Pipeline hardening (one evening)

- [ ] **A1. Vector refresh joins the DAG.** Add a `refresh_zone_vectors` task to
      the Airflow DAG, downstream of `dbt_test`, running `build_zone_vectors.py`
      in the worker. Requires: `chromadb` added to `_PIP_ADDITIONAL_REQUIREMENTS`
      in the compose override; script uses the mounted project path for the
      chroma store. Outcome (honest claim unlocked): *"embedding refresh is
      blocked if upstream data validation fails."*
- [ ] **A2. Tests for the new marts.** In `schema.yml`: `zone_id` unique +
      not_null on `dim_zone_venues` and `zone_trip_stats`; not_null on
      `total_venues`. Suite grows ~13 tests.
- [ ] **A3. Kill the deprecation warning.** Nest the remaining
      `accepted_range` args under `arguments:` in `schema.yml`.

## Phase B — Evaluation harness (the centerpiece, ~a weekend)

- [ ] **B1. Golden question set.** ~20 questions in `eval/questions.yml`, spread
      across: simple aggregates, rankings/superlatives, time trends, hour-of-day,
      zone character (RAG), and hybrid (both tools). Each with expected answer
      type and tolerance.
- [ ] **B2. Ground truth.** Hand-written SQL per numeric question in
      `eval/ground_truth.sql`; run once, store answers in `eval/answers.json`.
- [ ] **B3. Agent evaluation.** `eval_agent.py`: run every question through
      `agent.py`'s chat, extract numeric claims, score vs ground truth within
      tolerance; log which tools were called. Output: per-question pass/fail.
- [ ] **B4. Baseline: raw text-to-SQL.** `baseline_sql.py`: same model, given
      only raw table schemas (no semantic layer), asked to write SQL directly;
      execute and score the same questions.
- [ ] **B5. Results.** `EVAL.md`: accuracy table (semantic-layer agent vs raw
      text-to-SQL), failure analysis, cost-per-question notes, retrieval
      observations. Link from README. This produces the one measured claim
      for the resume.

## Phase C — Presentation (one evening)

- [ ] **C1. Architecture diagram** in README (source → Airflow/dbt → BigQuery
      bronze/silver/gold → semantic layer + vector store → agent).
- [ ] **C2. Demo recording.** 2-minute GIF/video: agent answering a metric
      question (show the generated SQL / tool call), a character question, and
      a hybrid question.
- [ ] **C3. README overhaul** with AI-analytics framing — honest version:
      governed metrics vs text-to-SQL (with eval numbers), context engineering
      story (numbers-to-narrative zone profiles), quality gates in the DAG.
- [ ] **C4. Resume bullets** drafted from measured results only.

## Framing rules (from feedback review)

- Adopt the AI-analytics vocabulary ONLY over things that exist in this repo.
- No unmeasured claims: every quantified statement traces to EVAL.md.
- Do not claim chunking/metadata-filtering strategies that weren't built; the
  real story is numbers-to-narrative document generation and tool routing.
- Interview stories live in PROGRESS.md: schema drift, poisoned idempotency,
  cache collisions, the Williamsburg retrieval fix, the unicorn encoding bug.
