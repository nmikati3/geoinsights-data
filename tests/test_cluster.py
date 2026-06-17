"""Tests for the incident-clustering logic in ``geoinsights_data.utils.cluster``.

The cluster module imports a few heavy / network-bound dependencies at module
load time (``geoinsights_data.utils.llm`` builds an OpenAI client on import, and
``hdbscan`` pulls in a large native stack). We stub those *before* importing the
module so the tests stay hermetic and fast, while exercising the real clustering
math (torch + scipy) and the real incident-ID/aggregation logic (pandas).
"""

import sys
import types

import numpy as np
import pandas as pd
import pytest

# ``torch`` / ``scipy`` / ``sklearn`` do the real clustering math we want to test.
# Skip the whole module if torch isn't installed (e.g. a minimal local env); CI
# installs it.
pytest.importorskip("torch")
pytest.importorskip("scipy")
pytest.importorskip("sklearn")


# --- Stub the network/native deps that cluster.py imports at module load -------
def _install_stubs():
    # Stub the project's llm module so importing cluster does not build an OpenAI
    # client (which raises when OPENAI_API_KEY is unset).
    fake_llm = types.ModuleType("geoinsights_data.utils.llm")
    fake_llm.compute_embeddings = lambda docs: None  # overridden per-test
    sys.modules.setdefault("geoinsights_data.utils.llm", fake_llm)

    # Stub hdbscan; the code paths that use it are mocked in these tests.
    fake_hdbscan = types.ModuleType("hdbscan")

    class _HDBSCAN:  # pragma: no cover - placeholder, not exercised here
        def __init__(self, *args, **kwargs):
            ...

        def fit(self, *args, **kwargs):
            return self

    fake_hdbscan.HDBSCAN = _HDBSCAN
    sys.modules.setdefault("hdbscan", fake_hdbscan)


_install_stubs()

from geoinsights_data.utils import cluster  # noqa: E402  (import after stubs)


def test_graph_clustering_groups_similar_documents(monkeypatch):
    """cluster_data('graph') should group near-parallel embeddings and separate
    near-orthogonal ones, using real cosine-similarity + connected-components."""

    docs = ["a1", "a2", "b1", "b2"]
    # Two clearly separated directions in 3-D space.
    fake_embeddings = np.array(
        [
            [1.0, 0.0, 0.0],
            [0.99, 0.01, 0.0],  # ~parallel to a1
            [0.0, 1.0, 0.0],
            [0.0, 0.99, 0.01],  # ~parallel to b1
        ],
        dtype=np.float32,
    )
    monkeypatch.setattr(cluster, "compute_embeddings", lambda d: fake_embeddings)

    result = cluster.cluster_data(docs, threshold=0.8, column="summary", method="graph")
    labels = dict(zip(result["summary"], result["label"]))

    assert labels["a1"] == labels["a2"], "near-parallel docs should share a cluster"
    assert labels["b1"] == labels["b2"], "near-parallel docs should share a cluster"
    assert labels["a1"] != labels["b1"], "near-orthogonal docs should be separate"


def test_run_clustering_builds_incident_ids_and_counts(monkeypatch):
    """run_clustering should assign stable incident IDs, count reports per incident,
    and compute incident_start_date — without touching embeddings."""

    # 30 reports for one incident (triggers the >=30 recluster path) + 6 for another.
    big = [f"big summary {i}" for i in range(30)]
    small = [f"small summary {i}" for i in range(6)]
    df = pd.DataFrame(
        {
            "summary": big + small,
            "date": ["2024-01-05"] * 30 + ["2024-02-10"] * 6,
        }
    )

    # Mock the embedding-dependent stages with deterministic labels.
    def fake_cluster_all(all_summaries, method, threshold, column):
        labels = [0 if s.startswith("big") else 1 for s in all_summaries[column]]
        return pd.DataFrame({column: list(all_summaries[column]), "label": labels})

    def fake_recluster(docs, column, threshold):
        return pd.DataFrame({column: docs, "new_label": [0] * len(docs)})

    monkeypatch.setattr(cluster, "cluster_all", fake_cluster_all)
    monkeypatch.setattr(cluster, "recluster", fake_recluster)

    out = cluster.run_clustering(df, threshold_cluster_all=0.9, threshold_recluster=0.95)

    # Exactly two distinct incidents.
    assert out["incident_id"].nunique() == 2

    counts = out.groupby("incident_id")["num_reports"].first().to_dict()
    assert sorted(counts.values()) == [6, 30]

    # Incident IDs are prefixed with the incident's start date (YYYYMMDD).
    big_incident = out[out["summary"].str.startswith("big")]["incident_id"].iloc[0]
    small_incident = out[out["summary"].str.startswith("small")]["incident_id"].iloc[0]
    assert big_incident.startswith("20240105-")
    assert small_incident.startswith("20240210-")

    # report_id is unique per report.
    assert out["report_id"].nunique() == len(out)
