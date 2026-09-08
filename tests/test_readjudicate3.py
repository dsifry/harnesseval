"""Unit tests for the v3 adjudicator (readjudicate3.py) — handoff 2026-09-08 §3C.

Machinery only, no API calls: provenance stripping, near-verbatim clustering (the
identical-text-cannot-flip property), k-vote majority + tie-break, the grounded-hallucination
prompt contract, and the FROZEN flip regression fixture (116 members: 98
important_non_bug + 18 hallucination, all labeled expected=bug).

Run: uv run python -m pytest tests/test_readjudicate3.py -q
"""
import asyncio
import json
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import readjudicate3 as rj  # noqa: E402


class TestStripProvenance(unittest.TestCase):
    def test_bracketed_confidence_severity(self):
        self.assertEqual(
            rj.strip_provenance("app/jobs/x.rb:29 — [confidence:100][severity:P1] `rss = parse` fails"),
            "app/jobs/x.rb:29 — `rss = parse` fails")

    def test_handoff_conf_form(self):
        self.assertEqual(rj.strip_provenance("[conf=100,P1] the timeout is missing"),
                         "the timeout is missing")

    def test_trailing_parenthetical(self):
        self.assertEqual(
            rj.strip_provenance("hosts saved with ports never match (confidence 75, P2)"),
            "hosts saved with ports never match")

    def test_lens_and_persona_tags(self):
        self.assertEqual(rj.strip_provenance("[lens/architecture] [compound-persona/p2/adversarial] N+1 query in loop"),
                         "N+1 query in loop")
        self.assertEqual(rj.strip_provenance("[deterministic/eval-injection] eval found"), "eval found")

    def test_meaningful_brackets_survive(self):
        # a bracket that is not provenance metadata must survive
        self.assertEqual(rj.strip_provenance("array index [1] is never bounds-checked"),
                         "array index [1] is never bounds-checked")

    def test_idempotent_and_ws_collapsed(self):
        t = "x — [confidence:75]  double  spaces"
        self.assertEqual(rj.strip_provenance(rj.strip_provenance(t)), rj.strip_provenance(t))


class TestClustering(unittest.TestCase):
    def test_identical_texts_one_cluster(self):
        texts = ["A timeout is missing on open(url)", "[conf=100,P1] A timeout is missing on open(url)"]
        # provenance-stripped, the two forms are identical -> one cluster, one verdict
        self.assertEqual(rj.cluster_texts(texts), [0, 0])

    def test_openssl_case_cannot_flip(self):
        """The handoff's canonical flip: identical wording, bug in one run,
        true_hallucination in another. Under v3 both phrasings are one cluster and
        structurally inherit ONE verdict."""
        base = (".env.example:241 documents `openssl rand -base64 24` for the AES-256 key, which "
                "produces 24 bytes instead of the required 32 bytes, causing aes-256-cbc to "
                "throw 'Invalid key length' and breaking the credential-sync webhook")
        texts = [base, base + " (confidence 75, P2)", "[confidence:100][severity:P1] " + base]
        cids = rj.cluster_texts(texts)
        self.assertEqual(len(set(cids)), 1, cids)

    def test_near_verbatim_same_cluster(self):
        a = "app/models/embeddable_host.rb:2 — validation permits host:port but record_for_host matches uri.host so the port is stripped and the host never matches"
        b = "app/models/embeddable_host.rb:2 — the validation accepts host:port but record_for_host matches on uri.host which excludes the port, so a host saved with a port never matches at runtime"
        self.assertEqual(rj.cluster_texts([a, b]), [0, 0])

    def test_different_issues_different_clusters(self):
        self.assertEqual(len(set(rj.cluster_texts(
            ["no .catch on destroyRecord", "pagination offset mutated before request"]))), 2)

    def test_deterministic_partition(self):
        texts = ["t one alpha", "t one alpha (confidence 90)", "t two beta", "something else entirely"]
        self.assertEqual(rj.cluster_texts(texts), rj.cluster_texts(texts))


class TestMajorityVote(unittest.TestCase):
    def test_two_of_three_wins(self):
        votes = [{"category": "bug", "confidence": 0.9, "reasoning": "a"},
                 {"category": "bug", "confidence": 0.7, "reasoning": "b"},
                 {"category": "hallucination", "confidence": 0.8, "reasoning": "c"}]
        m = rj._majority(votes)
        self.assertEqual(m["category"], "bug")
        self.assertAlmostEqual(m["confidence"], 0.8)

    def test_three_way_disagreement_returns_none(self):
        votes = [{"category": c, "confidence": 0.9, "reasoning": "r"} for c in
                 ("bug", "important_non_bug", "hallucination")]
        self.assertIsNone(rj._majority(votes))

    def test_adjudicate_majority(self):
        async def vote(judge, prompt, sem, effort="medium"):
            calls.append(prompt)
            i = len(calls) % 3
            return {"category": ("bug", "bug", "hallucination")[i], "confidence": 0.8, "reasoning": "r"}
        calls: list[str] = []
        with mock.patch.object(rj, "_one_vote", side_effect=vote):
            out = asyncio.run(rj.adjudicate("finding text", "diff body", "gpt-5.2",
                                            asyncio.Semaphore(3), k=3))
        self.assertEqual(out["verdict"], "bug")
        self.assertEqual(len(calls), 3)  # majority on the first k — no tie-break spend

    def test_adjudicate_tiebreak_sees_all_reasonings(self):
        state = {"n": 0}

        async def vote(judge, prompt, sem, effort="medium"):
            state["n"] += 1
            n = state["n"]
            if n <= 3:  # the k votes: one of each — a guaranteed 3-way disagreement
                return {"category": ("bug", "important_non_bug", "hallucination")[n - 1],
                        "confidence": 0.9, "reasoning": f"reason-{n}"}
            # the tie-break call: must have seen all three reasonings
            for i in (1, 2, 3):
                self.assertIn(f"reason-{i}", prompt)
            self.assertIn("bug (conf 0.90)", prompt)
            self.assertIn("hallucination (conf 0.90)", prompt)
            return {"category": "bug", "confidence": 0.85, "reasoning": "tiebreak"}

        with mock.patch.object(rj, "_one_vote", side_effect=vote):
            out = asyncio.run(rj.adjudicate("finding text", "diff body", "gpt-5.2",
                                            asyncio.Semaphore(4), k=3))
        self.assertEqual(state["n"], 4)          # 3 votes + exactly one tie-break
        self.assertEqual(out["verdict"], "bug")  # the tie-break's verdict wins
        self.assertEqual(out["confidence"], 0.85)

    def test_below_conf_floor_unresolved(self):
        async def vote(judge, prompt, sem, effort="medium"):
            return {"category": "bug", "confidence": 0.3, "reasoning": "plausible but unverifiable"}
        with mock.patch.object(rj, "_one_vote", side_effect=vote):
            out = asyncio.run(rj.adjudicate("finding text", "diff body", "gpt-5.2",
                                            asyncio.Semaphore(3), k=3))
        self.assertEqual(out["verdict"], "unresolved")
        self.assertIn("CONF_FLOOR", out["rationale"])

    def test_vote_errors_do_not_launder_as_verdicts(self):
        async def vote(judge, prompt, sem, effort="medium"):
            return {"error": "unparseable-response"}
        with mock.patch.object(rj, "_one_vote", side_effect=vote):
            out = asyncio.run(rj.adjudicate("finding text", "diff body", "gpt-5.2",
                                            asyncio.Semaphore(3), k=3))
        self.assertEqual(out["verdict"], "unresolved")


class TestPromptContract(unittest.TestCase):
    def test_hallucination_requires_cited_contradiction(self):
        self.assertIn("quote in your reasoning the specific diff line or detail that CONTRADICTS",
                      rj.V2_PROMPT)
        self.assertIn("If you cannot cite a contradiction", rj.V2_PROMPT)

    def test_cannot_verify_routes_to_low_confidence_bug(self):
        self.assertIn('return "bug" with confidence < 0.5', rj.V2_PROMPT)

    def test_hedged_wording_rule(self):
        self.assertIn("Hedged wording", rj.V2_PROMPT)
        self.assertIn("NOT evidence of falsity", rj.V2_PROMPT)

    def test_tiebreak_prompt_carries_the_same_ground_rules(self):
        self.assertIn("must quote the specific diff line", rj.TIEBREAK_PROMPT)
        self.assertIn("hedged wording is not evidence of falsity", rj.TIEBREAK_PROMPT)


class TestFrozenFlipFixture(unittest.TestCase):
    """The frozen regression set — any V2/V3 prompt change is scored against it
    (score_flips.py); these pins make silent re-derivation impossible."""

    @classmethod
    def setUpClass(cls):
        cls.fixture = json.load(open(Path(__file__).resolve().parents[1] / "tests/fixtures/flip_pairs.json"))

    def test_shape_matches_the_handoff_numbers(self):
        self.assertEqual(self.fixture["n_flips"], 116)
        self.assertEqual(self.fixture["by_v2_verdict"],
                         {"important_non_bug": 98, "hallucination": 18})

    def test_every_flip_labeled_expected_bug(self):
        for f in self.fixture["flips"]:
            self.assertEqual(f["expected"], "bug")

    def test_identical_normalized_texts_never_split_clusters(self):
        """The hard determinism property: within every cross-phrasing stability group,
        members that normalize to the same text (the openssl case's shape) must land in
        ONE cluster and therefore inherit ONE verdict. Genuinely different phrasings of
        the same bug may be separate clusters — their convergence is the grounded prompt
        + majority vote's job, not the cluster's."""
        checked = 0
        for g in self.fixture["stability_groups"]:
            texts = [m["issue_text"] for m in g["members"]]
            norms = {}
            cids = rj.cluster_texts(texts)
            for t, c in zip(texts, cids):
                norms.setdefault(rj.normalize_for_cluster(t), set()).add(c)
            for norm, cs in norms.items():
                self.assertEqual(len(cs), 1,
                                 f"group {g['ce_key']}: identical text split across clusters {cs}")
                checked += 1
        self.assertGreater(checked, 0)

    def test_the_openssl_case_is_in_the_set(self):
        hits = [f for f in self.fixture["flips"] if "openssl" in f["issue_text"].lower()]
        self.assertTrue(hits, "the .env.example openssl key-length flip must be in the frozen set")
        self.assertEqual(hits[0]["v2_verdict"], "hallucination")


if __name__ == "__main__":
    unittest.main()
