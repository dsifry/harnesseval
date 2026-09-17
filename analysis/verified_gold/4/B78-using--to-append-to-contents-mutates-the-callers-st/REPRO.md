# REPRO — Using `<<` to append to `contents` mutates the caller's String and can crash on frozen strings

**Verdict:** `behavior_change_not_regression` · standalone_real_code (real file, stubbed collaborators)

```bash
cd .cache/verify_repos/discourse && git checkout -f 4f8aed295a29954023b2849c060ef4fb299d1b5d
mkdir -p $(dirname spec/verify/topic_embed_verify.rb) && cp /Users/dsifry/Developer/harnesseval/analysis/verified_gold/4/B78-using--to-append-to-contents-mutates-the-callers-st/test.patch spec/verify/topic_embed_verify.rb
ruby -I. spec/verify/topic_embed_verify.rb        # expect: RESULT: FAIL on head
git apply /Users/dsifry/Developer/harnesseval/analysis/verified_gold/4/B78-using--to-append-to-contents-mutates-the-callers-st/fix.patch && ruby -I. spec/verify/topic_embed_verify.rb   # expect: RESULT: PASS
```
