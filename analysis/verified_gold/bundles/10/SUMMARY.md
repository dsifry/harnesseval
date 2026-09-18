# Verified hidden gold — PR 10

Candidates: 20 · verdicts: {'unresolved_file': 3, 'confirmed_regression': 1, 'behavior_change_not_regression': 8, 'inconclusive_env': 3, 'defect_present_before_pr': 4, 'not_a_bug': 1}

| bug id | bug | verdict | head | base | fix | file | tarball sha256 |
|---|---|---|---|---|---|---|---|
| 10-B03 | B03-embeddable-hosts-saved-with-a-port-never-match-because-l | `behavior_change_not_regression` | FAIL | ERROR:LoadError | PASS | `app/models/embeddablehost.rb` | `2165c2676e25…` |
| 10-B06 | B06-embeddablehost-allows-duplicate-host-mappings-making-loo | `behavior_change_not_regression` | FAIL | ERROR:LoadError | PASS | `app/models/embeddable_host.rb` | `01fbf288d3dc…` |
| 10-B09 | B09-embeddablehost-persists-arbitrary-categoryid-without-ver | `behavior_change_not_regression` | FAIL | ERROR:LoadError | PASS | `app/controllers/admin/embeddablehostscontroller.rb` | `8b086b48f431…` |
| 10-B12 | B12-migration-uses-createtable-force-true-causing-silent-dro | `behavior_change_not_regression` | FAIL | ERROR:LoadError | PASS | `db/migrate/20150818190757_create_embeddable_hosts.rb` | `b0d576d79435…` |
| 10-B13 | B13-put--admin-customize-embedding-update-is-a-no-op-that-re | `behavior_change_not_regression` | FAIL | ERROR:LoadError | PASS | `app/controllers/admin/embeddingcontroller.rb` | `1e10336cdb5d…` |
| 10-B16 | B16-migration-skips-importing-legacy-embeddable-hosts-by-usi | `behavior_change_not_regression` | FAIL | ERROR:LoadError | PASS | `db/migrate/20150818190757createembeddablehosts.rb` | `53faccf89b8d…` |
| 10-B21 | B21-embeddingserializer-emits-only-embeddablehostids-no-sid | `behavior_change_not_regression` | FAIL | ERROR:LoadError | PASS | `app/serializers/embeddingserializer.rb` | `dafbaf9810c3…` |
| 10-B23 | B23-embeddablehost-host-format-validation-allows-trailing-ne | `behavior_change_not_regression` | FAIL | ERROR:LoadError | PASS | `app/models/embeddablehost.rb` | `ac8dd4a5243f…` |
| 10-B02 | B02-plural-ids-hydration-blindly-calls-map-on-null-undefine | `confirmed_regression` | FAIL | PASS | PASS | `app/services/store.js.es6` | `40756d04245b…` |
| 10-B07 | B07-delete-action-swallows-destroyrecord-failures-no-popupa | `defect_present_before_pr` | FAIL | FAIL | PASS | `app/assets/javascripts/admin/components/embeddable-host.js.es6` | `224fa227968f…` |
| 10-B15 | B15-expandablefirstpost-no-longer-gated-by-configured-embed | `defect_present_before_pr` | FAIL | FAIL | PASS | `app/models/topic.rb` | `f27f1607998b…` |
| 10-B22 | B22-embed-host-lookup-uses-lowerhost-without-a-supporting-fu | `defect_present_before_pr` | FAIL | FAIL | PASS | `app/models/embeddablehost.rb` | `b12dc1853bf3…` |
| 10-B24 | B24-rest-adapter-only-replaces-first-underscore-in-type-name | `defect_present_before_pr` | FAIL | FAIL | PASS | `app/assets/javascripts/discourse/adapters/rest.js.es6` | `d9e7766f3e41…` |
| 10-B05 | B05-embeddablehost-hostname-validation-regex-rejects-valid-h | `inconclusive_env` | ? | — | — | `app/models/embeddablehost.rb` | `68c30dc47482…` |
| 10-B17 | B17-feed-polled-topicembed-imports-can-lose-category-and-lan | `inconclusive_env` | ERROR:NoMethodError | — | — | `app/models/topicembed.rb` | `1a253eaae292…` |
| 10-B18 | B18-routes-expose-rest-actions-for-embeddablehosts-that-the- | `inconclusive_env` | ERROR:uninitialized constant | — | — | `config/routes.rb` | `3b0030aa23fa…` |
| 10-B11 | B11-irreversible-destructive-data-migration-in-change-perman | `not_a_bug` | PASS | — | — | `db/migrate/20150818190757_create_embeddable_hosts.rb` | `10684a22359e…` |
| 10-B00 | B00-migration-interpolates-embeddable-host-strings-into-raw- | `unresolved_file` | — | — | — | `db/post_migrate/*_backfill_embeddable_hosts.rb` | `defca4f2bff5…` |
| 10-B08 | B08-creating-an-embeddable-host-with-no-category-overwrites- | `unresolved_file` | — | — | — | `assets/javascripts/discourse/components/embeddable-host.js` | `bc49974dcc6e…` |
| 10-B20 | B20-pretender--fruits-id-handler-ignores-requested-id-and-al | `unresolved_file` | — | — | — | `test/javascripts/helpers/create-pretender.js.es6` | `d8bce8eed737…` |
