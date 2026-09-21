"""sdlc-report.html must say nothing the frozen metrics do not support.

Three layers: (1) the template's visible prose carries no typed numbers, only {{fact}} placeholders;
(2) the facts agree with the numbers REPORT.md publishes; (3) the claim guards reject data under
which the template's qualitative sentences would be false.
"""
import copy
import html
import importlib.util
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Tokens that contain digits or number-words but are names, not claims.
ALLOWED = [r"F[12]′?", r"§\s?[\d.]+", r"September 2026", r"one-shot", r"One-shot",
           r"GLM-5\.3-(?:vision|flash)", r"DeepSeek-4\.1-flash"]
NUMBER_WORDS = r"\b(two|three|four|five|six|seven|eight|nine|ten|dozen|double|twice|half|third|quarter)\b"


def visible_text(page: str) -> str:
    page = re.sub(r"<(script|style)\b.*?</\1>", " ", page, flags=re.S)
    page = re.sub(r"<[^>]+>", " ", page)
    return html.unescape(page)


class SdlcReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("sdlc", ROOT / "tools/sdlc_report_html.py")
        cls.gen = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.gen)
        cls.metrics = json.loads((ROOT / "analysis/final_report_metrics.json").read_text())
        cls.template = (ROOT / "tools/sdlc_report_template.html").read_text(encoding="utf-8")
        cls.dataset = json.loads((ROOT / "analysis/final_report_dataset.json").read_text())
        cls.facts, cls.data, cls.guards = cls.gen.compute(cls.metrics, cls.dataset)
        cls.page = cls.gen.render(cls.template, cls.facts, cls.data)
        cls.report_md = (ROOT / "REPORT.md").read_text(encoding="utf-8")
        cls.report_html = (ROOT / "REPORT.html").read_text(encoding="utf-8")

    def test_template_prose_has_no_typed_numbers(self):
        text = re.sub(r"\{\{\w+\}\}", " ", visible_text(self.template))
        for pattern in ALLOWED:
            text = re.sub(pattern, " ", text)
        digits = re.findall(r"\S*\d\S*", text)
        self.assertEqual(digits, [], f"typed numerals in template prose: {digits}")
        words = re.findall(NUMBER_WORDS, text, flags=re.I)
        self.assertEqual(words, [], f"typed number-words in template prose: {words}")

    def test_every_placeholder_resolves(self):
        self.assertNotRegex(self.page, r"\{\{\w+\}\}")

    def test_committed_page_matches_generator(self):
        self.assertEqual((ROOT / "sdlc-report.html").read_text(encoding="utf-8"), self.page,
                         "sdlc-report.html is stale: run tools/sdlc_report_html.py")

    def test_render_is_deterministic(self):
        facts, data, _ = self.gen.compute(copy.deepcopy(self.metrics), self.dataset)
        self.assertEqual(self.gen.render(self.template, facts, data), self.page)

    def test_headline_facts_match_the_published_report(self):
        f = self.facts
        cell = {r['key']: r for r in self.data['cells']}
        best_oneshot = max((r for r in self.data['cells'] if r['fw'] == 'one-shot'), key=lambda r: r['score'])
        for needle in (
            f"{f['hv_pos']}/{f['hv_pairs']}",                       # 39/42 harness-vs-vanilla
            f"{f['gold_total']} distinct bugs",                     # 147
            f"{f['gold_hidden']} verified hidden defects",          # 105
            f"union covers {f['union_found']}/{f['gold_total']}",   # 140/147
            f"| {self.gen.cell_label(self.guards['top']['key'])} | {f['best_bugs']} |",  # Opus · CE · medium | 88 (REPORT shorthand)
            f"{f['top_score']} [",                                  # 0.641 [CI]
            f"**{f['eff_unresolved']} not resolved by this sample**",
            f"| vision | {f['pilot_bugs']} | {cell[self.gen.PILOT]['advice']} | {f['pilot_unsup']} |",
            f"| flash | {f['cheap_bugs']} | {cell[self.gen.PILOT_CHEAP]['advice']} | {f['cheap_unsup']} |",
            f"| {f['pilot_score']} | $0.222 | {f['pilot_secs']} |",
            f"| {f['cheap_score']} | {f['cheap_cost']} | {f['cheap_secs']} |",
            f"Fable · vanilla · medium ({best_oneshot['score']:.3f})",
            f"{f['n_runs']} healthy runs",                          # 2,416
            f"public {f['n_bench_prs']}-PR benchmark",              # 50
            f"mean gap {f['sel_recall_gap'].replace('−', '-')}",    # +0.006
            f"{f['sel_cells']} cells with ≥40/50 PRs",              # 33
            f"overstated by {f['sel_f1_gap'].replace('−', '-')}4",  # +0.084
        ):
            self.assertIn(needle, self.report_md)
        self.assertEqual(self.gen.cell_label(best_oneshot["key"]), "Fable · one-shot · medium")
        self.assertEqual(f["best_oneshot_label"], self.gen.long_label(best_oneshot["key"]))
        self.assertIn("median token multiple **10.1×**", self.report_md)
        self.assertEqual(f["tok_mult"], "10")

    def test_report_links_point_at_real_anchors(self):
        anchors = set(re.findall(r'href="REPORT\.html#([^"]+)"', self.page))
        self.assertGreater(len(anchors), 8)
        for anchor in anchors:
            self.assertIn(f'id="{anchor}"', self.report_html, f"REPORT.html has no #{anchor}")

    def test_labels_spell_out_model_names_and_tables_spell_out_harnesses(self):
        short = set(self.gen.MODEL_NAME.values()) - set(self.gen.MODEL_FULL.values())  # 'Sol', 'GLM vision', ...
        for r in self.data["cells"]:
            self.assertNotIn(r["label"].split(" · ")[0], short, r["label"])
            self.assertNotRegex(r["long"], r"\b(CE|MRV)\b", r["long"])
        for name in ("top_label", "pilot_label", "cheap_label", "closed_label", "runner_label", "top_prose", "pilot_prose"):
            self.assertNotRegex(self.facts[name], r"\b(CE|MRV)\b", name)

    def test_every_harness_link_points_at_that_harness(self):
        url, name = self.gen.FW_URL, self.gen.FW_LONG
        links = re.findall(r'<a href="([^"]+)">([^<]+)</a>', self.page)
        for fw in url:
            named = [h for h, text in links if text == name[fw]]
            self.assertGreater(len(named), 2, name[fw])
            self.assertEqual(set(named), {url[fw]}, f"a link labelled {name[fw]} points elsewhere")
            self.assertEqual({text for h, text in links if h == url[fw]}, {name[fw]}, f"a link to {url[fw]} is labelled as something else")

    def test_pick_tiles_name_and_link_the_harness_their_configuration_ran(self):
        tiles = re.findall(r'<div class="pick"><span class="pick-k">([^<]+)</span><b>(.*?)</b>', self.page, flags=re.S)
        want = {"Best value": self.guards["pilot"], "Top score": self.guards["top"], "Tightest budget": self.guards["cheap"]}
        seen = {k: b for k, b in tiles if k in want}
        self.assertEqual(set(seen), set(want))
        for label, row in want.items():
            m, fw, effort = row["key"].split("|")
            self.assertEqual(seen[label], f'{self.gen.MODEL_FULL[m]} running <a href="{self.gen.FW_URL[fw]}">{self.gen.FW_LONG[fw]}</a>, {effort} effort', label)

    def test_top_score_tile_follows_the_data_to_a_different_harness(self):
        M = copy.deepcopy(self.metrics)
        M["true_gold_defects"]["verified"]["cells"]["claude-opus-5|metareview-realistic|high"]["F2p"] = 0.95
        facts = self.gen.compute(M, self.dataset)[0]
        self.assertEqual((facts["top_fw_long"], facts["top_fw_url"]), ("metareview", self.gen.FW_URL[self.gen.MRV]))

    def test_guard_rejects_a_pick_that_is_not_a_harness_run(self):
        M = copy.deepcopy(self.metrics)
        M["true_gold_defects"]["verified"]["cells"]["claude-fable-5-1|vanilla-engineered|medium"]["F2p"] = 0.95
        facts, _, guards = self.gen.compute(M, self.dataset)  # must not crash on the missing repo link
        self.assertEqual(facts["top_fw_url"], "")
        with self.assertRaises(self.gen.ClaimGuardError):
            self.gen.check_guards(guards)

    def test_answer_box_sits_above_the_findings_and_links_to_the_leaderboard(self):
        self.assertLess(self.page.index('id="answer"'), self.page.index('id="findings"'))
        self.assertIn('href="#leaderboard"', self.page)
        self.assertIn('id="leaderboard"', self.page)

    def test_guard_rejects_a_closed_one_shot_prompt_beating_an_open_weight_harness(self):
        M = copy.deepcopy(self.metrics)
        M["true_gold_defects"]["verified"]["cells"]["claude-fable-5-1|vanilla-engineered|medium"]["F2p"] = 0.50
        with self.assertRaises(self.gen.ClaimGuardError):
            self.gen.check_guards(self.gen.compute(M, self.dataset)[2])

    def test_disclosure_is_on_the_page_and_on_every_share_card(self):
        text = re.sub(r"\s+", " ", visible_text(self.page))
        self.assertIn("I wrote metareview", text)
        self.assertRegex(text, r"harnesseval · September 2026 · .*the author wrote metareview")

    def test_share_posts_fit_in_a_tweet_with_their_link(self):
        posts = re.findall(r'<p class="post">(.*?)</p>', self.page, flags=re.S)
        self.assertEqual(len(posts), 7)
        tags = re.search(r"const HASHTAGS = \[([^\]]*)\]", self.template).group(1)
        tag_text = " ".join("#" + h.strip("' ") for h in tags.split(","))
        for post in posts:
            text = html.unescape(re.sub(r"\s+", " ", post).strip())
            # post + space + hashtags + space + link; X counts any link as 23 characters
            self.assertLessEqual(len(text) + 1 + len(tag_text) + 1 + 23, 280, text)

    def test_report_prints_the_one_shot_prompt_the_adapter_runs(self):
        source = (ROOT / "harnesseval/adapters/vanilla.py").read_text(encoding="utf-8")
        prompt, line = self.gen.oneshot_prompt()
        self.assertTrue(source.splitlines()[line - 1].startswith("ENGINEERED_PROMPT"))
        self.assertIn('tmpl = NAIVE_PROMPT if variant == "naive" else ENGINEERED_PROMPT', source)
        self.assertIn(f"~~~text\n{prompt}\n~~~", self.report_md, "REPORT.md §2.2 must print the prompt verbatim")
        self.assertIn('href="REPORT.html#the-one-shot-baseline-prompt-verbatim"', self.page)

    def test_linkedin_posts_follow_the_long_form_rules(self):
        posts = re.findall(r'<p class="post-li">(.*?)</p>', self.page, flags=re.S)
        self.assertEqual(len(posts), 7)
        tags = re.search(r"const LI_HASHTAGS = \[([^\]]*)\]", self.template).group(1)
        n_tags = len([h for h in tags.split(",") if h.strip()])
        self.assertTrue(3 <= n_tags <= 5)
        for post in posts:
            lines = [re.sub(r"\s+", " ", ln).strip() for ln in html.unescape(post).split("\n")]
            text = "\n".join(lines).strip()
            self.assertLessEqual(len(lines[0]), 210, "hook must fit before 'see more': " + lines[0])
            self.assertTrue(text.rstrip().endswith("?"), "end with a question: " + text[-80:])
            self.assertNotRegex(text, r"\b([Ww]e|[Oo]ur|[Uu]s)\b", "the reader is not an author: " + lines[0])
            # a post must stand alone in an email or a LinkedIn post: what was studied, who ran it, the disclosure, and where to read it
            self.assertTrue(1000 <= len(text) <= 2400, f"{len(text)} chars: " + lines[0])
            self.assertLessEqual(len(text) + 2 + 60, 3000)  # with hashtags, inside LinkedIn's limit; the links are in the text
            self.assertIn(self.facts["page_url"] + "#", text, "link to the finding: " + lines[0])
            self.assertIn(self.facts["report_url"], text, "link to the full report: " + lines[0])
            self.assertIn("AI code review", text, lines[0])
            self.assertIn("Sifry wrote metareview", text, "author disclosure: " + lines[0])
            self.assertIn("Compound Engineering and metareview", text, "names the ways of working: " + lines[0])
            self.assertNotRegex(text, r"\b(CE|MRV)\b", "abbreviations a stranger cannot decode: " + lines[0])

    def test_link_preview_description_fits_the_networks(self):
        desc = html.unescape(re.search(r'<meta property="og:description" content="([^"]*)"', self.page).group(1))
        self.assertLessEqual(len(desc), 220, f"{len(desc)} chars; X and LinkedIn truncate around 200: {desc}")
        self.assertNotRegex(desc, r"\{\{")

    def test_share_images_carry_a_qr_code_for_their_own_link(self):
        ids = re.findall(r'id="([^"]+)"[^>]*data-share=', self.page)
        self.assertEqual(sorted(ids), sorted(self.data["qr"]))
        for sid, rows in self.data["qr"].items():
            n = len(rows)
            self.assertTrue(all(len(r) == n for r in rows) and (n - 17) % 4 == 0, sid)
            self.assertEqual(rows[0][:7], "1111111", sid)  # finder pattern
        try:
            import cv2
            import numpy as np
        except ImportError:  # the decoder is a local verification aid, not a project dependency
            return
        det = cv2.QRCodeDetector()
        for sid, rows in self.data["qr"].items():
            n, s, qz = len(rows), 8, 4
            img = np.full(((n + 2 * qz) * s, (n + 2 * qz) * s), 255, np.uint8)
            for r, row in enumerate(rows):
                for c, v in enumerate(row):
                    if v == "1":
                        img[(r + qz) * s:(r + qz + 1) * s, (c + qz) * s:(c + qz + 1) * s] = 0
            self.assertEqual(det.detectAndDecode(img)[0], f"{self.gen.PUBLIC_BASE}{self.gen.PAGE_NAME}#{sid}", sid)

    def test_qr_encoder_matches_the_reference_encoder(self):
        try:
            import segno
        except ImportError:
            return
        import importlib.util as ilu
        spec = ilu.spec_from_file_location("qr", ROOT / "tools/qr.py"); qr = ilu.module_from_spec(spec); spec.loader.exec_module(qr)
        # exact-fit payloads leave no pad codewords, where segno deviates from ISO 18004 by inserting a zero byte
        for v in range(1, 11):
            text = "".join(chr(97 + i % 26) for i in range(qr._BLOCKS[v][0] - (3 if v >= 10 else 2)))
            ours = qr.encode(text)
            self.assertTrue(any([[int(x) for x in row] for row in segno.make(text, error="m", version=v, mask=m, boost_error=False).matrix] == ours
                                for m in range(8)), f"version {v}")

    def test_chart_data_is_the_complete_cells_only(self):
        cells = self.metrics["true_gold_defects"]["verified"]["cells"]
        self.assertEqual({r["key"] for r in self.data["cells"]}, {k for k, c in cells.items() if c["n_pr"] == 6})
        for r in self.data["cells"]:
            self.assertEqual(r["bugs"], cells[r["key"]]["TP"])
            self.assertAlmostEqual(r["cost"], self.metrics["matrix"][r["key"]]["cost_run"], places=4)

    def test_guards_pass_on_the_frozen_data(self):
        self.gen.check_guards(self.guards)

    def test_guard_rejects_a_closed_model_entering_the_top_group(self):
        M = copy.deepcopy(self.metrics)
        M["true_gold_defects"]["verified"]["cells"]["gpt-5.6-sol|compound-realistic|high"]["F2p"] = 0.63
        with self.assertRaises(self.gen.ClaimGuardError):
            self.gen.check_guards(self.gen.compute(M, self.dataset)[2])

    def test_guard_rejects_the_pilot_no_longer_matching_opus(self):
        M = copy.deepcopy(self.metrics)
        M["true_gold_defects"]["verified"]["cells"]["glm-5.3-vision-background|metareview-realistic|low"]["F2p"] = 0.50
        with self.assertRaises(self.gen.ClaimGuardError):
            self.gen.check_guards(self.gen.compute(M, self.dataset)[2])

    def test_guard_rejects_a_closed_model_on_the_efficiency_frontier(self):
        M = copy.deepcopy(self.metrics)
        M["matrix"]["gpt-5.6-sol|compound-realistic|high"]["cost_run"] = 0.01
        with self.assertRaises(self.gen.ClaimGuardError):
            self.gen.check_guards(self.gen.compute(M, self.dataset)[2])

    def test_guard_rejects_effort_mostly_paying_off(self):
        M = copy.deepcopy(self.metrics)
        for v in M["effort_ladder"].values():
            v["delta"]["F1"] = [0.2, 0.1, 0.3]
        with self.assertRaises(self.gen.ClaimGuardError):
            self.gen.check_guards(self.gen.compute(M, self.dataset)[2])


if __name__ == "__main__":
    unittest.main()
