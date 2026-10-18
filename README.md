# PRPilot

PRPilot is a serverless, AI-assisted GitHub pull-request review agent. It runs in GitHub Actions, reads pull-request metadata and changed-file patches through the GitHub REST API, asks Google Gemini for structured findings, validates every proposed location against the fetched patch, then posts one GitHub review with inline comments and a concise summary.

It does **not** check out, build, or execute pull-request code in the review workflow. It never merges a PR or applies source-code edits. AI advice remains subject to human review.

## What it does

- Runs for opened, reopened, and synchronized pull requests.
- Uses Google’s official `google-genai` SDK with `gemini-3.8-flash`. This model identifier was verified against Google’s [official Gemini model catalog](https://ai.google.dev/gemini-api/docs/models) on 2026-10-18; override it with `GEMINI_MODEL` if your Gemini project uses a different supported model.
- Requires JSON findings with severity, category, file, destination line, explanation, suggested fix, confidence, and a heuristic flag.
- Rejects malformed AI output and withholds a finding unless its line is an actual added `RIGHT` line in GitHub’s current patch.
- Adds only pre-existing approved labels: `bug`, `enhancement`, `documentation`, `tests`, and `security`.
- Marks test/documentation coverage notices as **heuristic warnings**, never verified failures.
- Detects duplicate reviews for the same commit and retries transient GitHub/Gemini failures with bounded backoff.
- On a merged PR, makes a draft `CHANGELOG.draft.md` entry under Features, Fixes, or Maintenance. The workflow uses a protected GitHub environment as the required human approval gate; it does not publish release notes.

## Repository layout

```text
.github/workflows/prpilot-review.yml       Safe PR review workflow
.github/workflows/prpilot-changelog.yml   Human-gated draft-changelog workflow
prpilot/                                  Review, GitHub, Gemini, diff, changelog code
tests/                                     Unit tests
.prpilot.example.yml                      Review-policy template
```

## Setup

1. Create a Gemini API key in [Google AI Studio](https://aistudio.google.com/app/apikey). Keep it secret; do not put it in this repository.
2. On GitHub, go to **Settings → Secrets and variables → Actions → New repository secret** and add `GEMINI_API_KEY`.
3. Create these repository labels exactly (case-sensitive): `bug`, `enhancement`, `documentation`, `tests`, and `security`. PRPilot deliberately will not create labels.
4. Go to **Settings → Environments**, create `prpilot-release-notes`, and configure **required reviewers**. This is mandatory before enabling changelog drafting: it provides the human approval gate.
5. Push the project. For a new local directory, replace `OWNER/REPOSITORY` and run:

   ```bash
   git init
   git add .
   git commit -m "feat: add PRPilot"
   git branch -M main
   git remote add origin https://github.com/OWNER/REPOSITORY.git
   git push -u origin main
   ```

   For an existing clone, use `git add .`, `git commit -m "feat: add PRPilot"`, and `git push` instead. In **Settings → Actions → General**, set workflow permissions to **Read and write permissions** and allow GitHub Actions to create pull requests/reviews if your organization policy requires that. The review workflow requests only `contents: read`, `pull-requests: write`, and `issues: write`; the changelog job requests `contents: write` only after environment approval.
6. Open a PR that changes a source file. The **PRPilot AI review** check appears under the PR’s Checks tab. Push a new commit to cause another review.

For a local syntax/test run:

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows PowerShell
pip install -r requirements.txt
pytest
```

## Fork and threat-model behavior

The review workflow uses `pull_request`, never `pull_request_target`. For PRs from forks, GitHub does not pass repository secrets and reduces `GITHUB_TOKEN` permissions; PRPilot logs that the Gemini key is unavailable and exits safely. The workflow checks out only the default branch, so it cannot run untrusted PR code. Diffs, PR titles, and bodies are passed to Gemini as untrusted data with an explicit instruction not to follow instructions embedded in them.

GitHub may omit a `patch` for very large or binary files. Findings for those files are rejected because PRPilot cannot prove their location. GitHub’s token remains the final authorization boundary, and the user must grant the workflow permissions above.

## Operational notes

- The GitHub Actions check itself is the status check; configure branch protection to require `PRPilot AI review` only after validating it in your repository.
- A Gemini key and a GitHub repository are required for a live review; tests run without either.
- `CHANGELOG.draft.md` is intentionally a draft artifact. Publishing a release and release notes remains a human action.
- The changelog append operation requires that the protected environment approves the job and that the default branch accepts Actions commits. If branch protection blocks it, a maintainer should create the draft entry manually or adapt the workflow to open a PR.
