import unittest
from tools import advisory_pair_validation as pairs

class PairValidationTests(unittest.TestCase):
    def vote(self,**changes):
        value={'pair':1,'same':True,'confidence':.9,'a':{'mechanism':'m','trigger':'t','consequence':'c'},'b':{'mechanism':'m','trigger':'t','consequence':'c'},'material_differences':[],'reason':'same complete claim'}
        value.update(changes);return value
    def test_added_consequence_overrides_same_vote(self):
        self.assertEqual(pairs.parse_votes({'pairs':[self.vote(material_differences=['A crashes; B silently falls back'])]},1),[False])
    def test_threshold_and_no_truthy_string_coercion(self):
        self.assertEqual(pairs.parse_votes({'pairs':[self.vote(confidence=.79)]},1),[False])
        self.assertEqual(pairs.parse_votes({'pairs':[self.vote(confidence=.8)]},1),[True])
        with self.assertRaises(ValueError):pairs.parse_votes({'pairs':[self.vote(same='true')]},1)
    def test_missing_duplicate_and_out_of_range_indices_fail(self):
        for votes,n in [([],1),([self.vote(),self.vote()],2),([self.vote(pair=2)],1)]:
            with self.assertRaises(ValueError):pairs.parse_votes({'pairs':votes},n)
    def test_case_sensitive_cache_and_complete_claim(self):
        self.assertNotEqual(pairs.claim_key('obj.Foo()'),pairs.claim_key('obj.foo()'))
        prompt=pairs.make_prompt([('x'*1000+' crashes','x'*1000+' silently falls back')])
        self.assertIn('crashes',prompt);self.assertIn('silently falls back',prompt)

class RefinementTests(unittest.IsolatedAsyncioTestCase):
    async def test_nontransitive_pair_bridge_never_merges_conflicting_members(self):
        async def compare(requests):return [set(p)!={1,2} for p in requests]
        groups=await pairs.refine_groups([[0,1,2]],compare)
        self.assertEqual(groups,[[0,1],[2]])
    async def test_rejected_members_are_reconsidered_as_separate_paraphrase_group(self):
        async def compare(requests):return [set(p)=={1,2} for p in requests]
        groups=await pairs.refine_groups([[0,1,2]],compare)
        self.assertEqual(groups,[[0],[1,2]])
    def test_dedup_scoring_identity_cannot_propagate_category(self):
        self.assertNotEqual(pairs.scoring_identity(1,{'verdict':'important_non_bug','confidence':.9}),pairs.scoring_identity(1,{'verdict':'hallucination','confidence':.9}))
        self.assertNotEqual(pairs.scoring_identity(1,{'verdict':'important_non_bug','confidence':.9}),pairs.scoring_identity(1,{'verdict':'important_non_bug','confidence':.7}))
