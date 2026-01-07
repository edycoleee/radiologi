<!-- .github/copilot-instructions.md - guidance for AI coding agents -->
# Project snapshot

Repository: `flask-satset`

- Current detectable files: `README.md` (empty). No source code, tests, or manifests were found in the workspace at the time of writing.

# Purpose for AI agents

This file gives immediate, repository-specific steps and guardrails so an AI coding agent can be productive without human hand-holding. Because this repo currently contains no application code, focus on discovery and verification steps first, and only change code when the agent has a clear, small, and testable task or explicit user instruction.

# Quick discovery checklist (do these before making edits)
- Confirm repo contents: run `ls -la` and search for common project files: `requirements.txt`, `pyproject.toml`, `setup.cfg`, `Pipfile`, `Makefile`, `Procfile`, `Dockerfile`.
- Search for code and tests: look for `**/*.py`, `app/`, `src/`, `tests/`, and common Flask entrypoints like `app.py`, `run.py`, or a package directory matching the repo name.
- Inspect `README.md` and any `docs/` or `.github/` for setup or run instructions.
- If nothing is found, stop and ask the repository maintainer what the intended starting point or branch is.

# If you find application code (how to proceed)
- Respect existing structure. Typical Flask layout we expect: a package directory (e.g., `app/`), an entrypoint `app.py` or `wsgi.py`, and `requirements.txt` or `pyproject.toml` for dependencies. But do not assume — confirm by reading files.
- Aim for minimal, incremental changes: small PRs that are isolated and easy to review. Provide a concise PR description explaining why the change is safe.

# Patterns and conventions to look for (examples to extract and follow)
- Configuration: search for files named `config.py`, `settings.py`, or a `config/` directory. Use the existing configuration style (single-module or class-based) rather than inventing a new pattern.
- App factory: many Flask apps use an `create_app()` factory. If present, prefer modifying or extending that factory rather than creating separate global app objects.
- Blueprints: if code uses Flask Blueprints (`flask.Blueprint`), add new routes as new or existing blueprints to keep concerns separated.

# Development workflow hints (discovery first)
- Don't run anything until you know how the repo is configured. If you find `requirements.txt` or `pyproject.toml`, list dependencies with `pip install -r requirements.txt` or `pip install -e .` in a virtual environment — but only after confirming with the maintainer or CI config.
- If tests exist (common folders: `tests/`, `test_*.py`), run them with `pytest` from the repository root and fix a single failing test at a time.

# PR and commit conventions
- Keep commit messages concise and imperative: `Fix X`, `Add Y endpoint`, `Refactor Z`.
- Keep changes small and focused. When proposing new structure, include a short migration plan in the PR description.

# When information is missing (what to ask the user)
- Where is the application code (branch or path)?
- Preferred dependency manager (pip, pipenv, poetry)?
- Test command and CI expectations.
- Any coding style or formatting rules (e.g., black, isort, pre-commit hooks)?

# Safety and review
- Do not add or remove dependencies without explicit confirmation.
- Avoid large refactors in an otherwise empty repository — request direction.

# Where to update this file
- If you find authoritative docs in the repo (setup instructions, CI config), update this file to reference those exact files and commands.

If anything in this document is unclear or incomplete, please tell me what extra files or conventions exist in this repo and I will refine these instructions.
