# Check-the-check — independent re-verification of promoted bundles

Re-ran 6 promoted bundles from their saved artifacts only (no driver state, no
authoring model). Each must reproduce: head FAIL, fixed PASS, base PASS or module-absent.

**Reproduced: 5/6**

| bug | claimed verdict | head | fixed | base | reproduces |
|---|---|---|---|---|---|
| 10967-B11 | `confirmed_regression` | FAIL | ? | ? | ❌ |
| 10967-B03 | `confirmed_regression` | FAIL | PASS | PASS | ✅ |
| 11059-B32 | `behavior_change_not_regression` | FAIL | PASS | N/A_module_absent | ✅ |
| 14740-B33 | `behavior_change_not_regression` | FAIL | PASS | N/A_module_absent | ✅ |
| 11059-B05 | `behavior_change_not_regression` | FAIL | PASS | N/A_module_absent | ✅ |
| 14740-B17 | `behavior_change_not_regression` | FAIL | PASS | N/A_module_absent | ✅ |
