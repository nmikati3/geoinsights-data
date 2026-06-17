# Contributing

Thanks for your interest in GeoInsights! Contributions are welcome: bug reports, documentation, tests, new domains, and improvements to the pipeline.

## Getting started

1. Fork and clone the repo.
2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   pip install pytest ruff
   ```
3. Run the tests:
   ```bash
   pytest
   ```

## Pull requests

- Keep PRs focused and reasonably small.
- Add or update tests when changing behavior (the clustering logic in `geoinsights_data/utils/cluster.py` is a good place to start).
- Run `ruff check geoinsights_data tests` before pushing.
- Describe the "why" in the PR description, not just the "what".

## Good first issues

- Add an accuracy/evaluation harness (precision/recall for the classifiers, cluster-purity metrics).
- Reduce duplication across the per-domain branches in `pipeline.py` and `join_func.py`.
- Add type hints and docstrings to the `utils/` modules.

## Code of conduct

Be kind and constructive. We follow the spirit of the
[Contributor Covenant](https://www.contributor-covenant.org/).
