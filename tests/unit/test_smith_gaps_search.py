"""BM25 precedent search for `smith_math.py gaps --query`, added 2026-09-07.

Replaces a literal-substring match that required the exact query text to appear verbatim
in a gap's JSON blob -- a query phrased with the same MEANING but different WORDS (the whole
point of a precedent search: you rarely remember a past incident's exact wording) returned
zero hits. Scoped as Tier A of the "add RAG/harness features to Agent Smith" conversation:
hand-rolled BM25 rather than a pip dependency, because every module in this compute layer is
stdlib-only by design (see smith_core.py's docstring) and the corpus (~84 gap records) is far
too small to need anything heavier.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

import smith_memory as sm


class TestTokenize:
    def test_lowercases_and_strips_stopwords(self):
        toks = sm._gaps_tokenize("The Basis Was Spliced, Not A Real Move")
        assert "the" not in toks
        assert "was" not in toks
        assert "not" not in toks
        assert "basis" in toks
        assert "spliced" in toks

    def test_empty_and_none_are_safe(self):
        assert sm._gaps_tokenize("") == []
        assert sm._gaps_tokenize(None) == []

    def test_single_char_tokens_dropped(self):
        # e.g. stray punctuation-adjacent fragments shouldn't pollute term stats
        assert "a" not in sm._gaps_tokenize("a b c basis")


class TestBM25Rank:
    def test_ranks_exact_term_overlap_above_no_overlap(self):
        docs = [
            "the basis was spliced across two measurement methods, not a real price move",
            "completely unrelated text about quarterly earnings and share buybacks",
        ]
        ranked = sm._bm25_rank("measurement basis spliced", docs)
        assert [i for i, _ in ranked] == [0]  # doc 1 shares zero query terms -> excluded, not just ranked low

    def test_paraphrase_with_shared_vocabulary_still_scores(self):
        """The actual bug this feature fixes: a paraphrase (not a substring) must still surface,
        as long as it shares SOME vocabulary with the query -- BM25 is lexical, not semantic."""
        docs = [
            "two different measurement bases were plotted as one line, producing a phantom decline",
            "a completely different gap about an orphaned broker position",
        ]
        # The old substring implementation required this exact phrase to appear verbatim.
        # It does not appear verbatim in doc 0 -- confirm BM25 finds it anyway via shared terms.
        query = "measurement basis mismatch phantom"
        ranked = sm._bm25_rank(query, docs)
        assert ranked, "expected at least one match via shared vocabulary"
        assert ranked[0][0] == 0

    def test_zero_overlap_query_returns_empty(self):
        docs = ["basis spliced measurement error", "orphaned broker position reconciliation"]
        ranked = sm._bm25_rank("xyzzy quux frobnicate", docs)
        assert ranked == []

    def test_query_with_only_stopwords_returns_empty(self):
        docs = ["basis spliced measurement error"]
        ranked = sm._bm25_rank("the a of and", docs)
        assert ranked == []

    def test_scores_sorted_descending(self):
        docs = [
            "basis basis basis mismatch",       # high term frequency for "basis"
            "basis mentioned once, unrelated otherwise about earnings",
            "no shared terms here about broker reconciliation orphans",
        ]
        ranked = sm._bm25_rank("basis mismatch", docs)
        scores = [s for _, s in ranked]
        assert scores == sorted(scores, reverse=True)
        assert ranked[0][0] == 0  # highest term-frequency doc ranks first

    def test_empty_docs_list_does_not_crash(self):
        assert sm._bm25_rank("basis mismatch", []) == []

    def test_doc_with_no_tokens_is_skipped_not_crashed(self):
        docs = ["", "basis mismatch error found"]
        ranked = sm._bm25_rank("basis mismatch", docs)
        assert [i for i, _ in ranked] == [1]


class TestCmdGapsQueryIntegration:
    """End-to-end through cmd_gaps' own field selection (gap/description + resolution + owner),
    against a small synthetic registry -- mirrors the real state.json/known-gaps-archive.json
    shape closely enough to catch a wiring regression without depending on live data."""

    class _Args:
        def __init__(self, **kw):
            self.base_dir = kw.get("base_dir")
            self.id = kw.get("id")
            self.query = kw.get("query")
            self.top = kw.get("top", 8)
            self.open_only = kw.get("open_only", False)

    def _seed(self, tmp_path):
        state = {"known_gaps": [
            {"id": "G1", "status": "open", "opened": "2026-01-01",
             "description": "Basis splice: two measurement bases fused into one band, phantom price move",
             "resolution": "", "owner": "orchestrator"},
            {"id": "G2", "status": "closed", "opened": "2026-01-02", "resolved_on": "2026-01-03",
             "description": "Orphaned broker position not present in the ledger",
             "resolution": "Reconciled against email confirmations", "owner": "smith-ledger"},
        ]}
        (tmp_path / "state.json").write_text(__import__("json").dumps(state))
        (tmp_path / "known-gaps-archive.json").write_text(__import__("json").dumps({"known_gaps": []}))
        return str(tmp_path)

    def test_query_finds_paraphrase_via_shared_terms(self, tmp_path, capsys):
        base = self._seed(tmp_path)
        args = self._Args(base_dir=base, query="measurement basis mismatch phantom decline", top=5)
        sm.cmd_gaps(args)
        out = __import__("json").loads(capsys.readouterr().out)
        ids = [g["id"] for g in out["gaps"]]
        assert "G1" in ids
        assert "relevance" in out["gaps"][0]

    def test_query_excludes_zero_overlap_gap(self, tmp_path, capsys):
        base = self._seed(tmp_path)
        args = self._Args(base_dir=base, query="measurement basis mismatch phantom decline", top=5)
        sm.cmd_gaps(args)
        out = __import__("json").loads(capsys.readouterr().out)
        ids = [g["id"] for g in out["gaps"]]
        assert "G2" not in ids  # shares no vocabulary with the query

    def test_id_lookup_unaffected_by_the_rewrite(self, tmp_path, capsys):
        base = self._seed(tmp_path)
        args = self._Args(base_dir=base, id="G2")
        sm.cmd_gaps(args)
        out = __import__("json").loads(capsys.readouterr().out)
        assert out["matched"] == 1
        assert out["gaps"][0]["id"] == "G2"
        assert "relevance" not in out["gaps"][0]

    def test_open_only_unaffected_by_the_rewrite(self, tmp_path, capsys):
        base = self._seed(tmp_path)
        args = self._Args(base_dir=base, open_only=True)
        sm.cmd_gaps(args)
        out = __import__("json").loads(capsys.readouterr().out)
        assert out["matched"] == 1
        assert out["gaps"][0]["id"] == "G1"

    def test_top_caps_result_count(self, tmp_path, capsys):
        base = self._seed(tmp_path)
        args = self._Args(base_dir=base, query="basis measurement position broker orphaned", top=1)
        sm.cmd_gaps(args)
        out = __import__("json").loads(capsys.readouterr().out)
        assert len(out["gaps"]) <= 1
