# REPRO — absolutize_urls treats protocol-relative URLs (//...) as root-relative and rewrites them to the article host

**Verdict:** `behavior_change_not_regression` · standalone_real_code (real file, stubbed collaborators)

```bash
cd .cache/verify_repos/discourse && git checkout -f 4f8aed295a29954023b2849c060ef4fb299d1b5d
mkdir -p $(dirname spec/verify/topic_embed_verify.rb) && cp /Users/dsifry/Developer/harnesseval/analysis/verified_gold/4/B01-absolutizeurls-treats-protocol-relative-urls----as-r/test.patch spec/verify/topic_embed_verify.rb
ruby -I. spec/verify/topic_embed_verify.rb        # expect: RESULT: FAIL on head
git apply /Users/dsifry/Developer/harnesseval/analysis/verified_gold/4/B01-absolutizeurls-treats-protocol-relative-urls----as-r/fix.patch && ruby -I. spec/verify/topic_embed_verify.rb   # expect: RESULT: PASS
```
