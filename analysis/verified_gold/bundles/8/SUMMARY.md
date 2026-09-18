# Verified hidden gold — PR 8

Candidates: 21 · verdicts: {'not_a_bug_unconfirmed': 1, 'defect_present_before_pr': 12, 'behavior_change_not_regression': 5, 'unresolved_file': 2, 'inconclusive_env': 1}

| bug id | bug | verdict | head | base | fix | file | tarball sha256 |
|---|---|---|---|---|---|---|---|
| 8-B03 | B03-admingroupscontrolleraddmembers-splits-usernames-witho | `behavior_change_not_regression` | FAIL | ERROR:NoMethodError | PASS | `app/controllers/admin/groups_controller.rb` | `b2f1130f5b4d…` |
| 8-B04 | B04-admin-group-creation-drops-submitted-aliaslevel-and-save | `behavior_change_not_regression` | FAIL | ERROR:NoMethodError | PASS | `app/controllers/admin/groups_controller.rb` | `358d5a4a4303…` |
| 8-B05 | B05-patch-updates-unintentionally-hide-groups-when-visible-p | `behavior_change_not_regression` | FAIL | ERROR:NameError | PASS | `app/controllers/admin/groupscontroller.rb` | `4b785c354664…` |
| 8-B15 | B15-admingroupscontroller-specs-hardcode-group-id1-implici | `behavior_change_not_regression` | FAIL | ERROR:NoMethodError | PASS | `spec/controllers/admin/groups_controller_spec.rb` | `bcc13e8cd4c0…` |
| 8-B18 | B18-group-name-is-stripped-on-create-but-not-on-update-allow | `behavior_change_not_regression` | FAIL | ERROR:NoMethodError | PASS | `app/controllers/admin/groups_controller.rb` | `34624629e748…` |
| 8-B01 | B01-unvalidated-limit-offset-in-groupscontrollermembers-allo | `defect_present_before_pr` | FAIL | FAIL | PASS | `app/controllers/groups_controller.rb` | `84d946eea739…` |
| 8-B08 | B08-admin-group-add-remove-member-actions-drop-the-ajax-prom | `defect_present_before_pr` | FAIL | FAIL | PASS | `app/assets/javascripts/admin/controllers/admin-group.js.es6` | `04965c0ca80d…` |
| 8-B10 | B10-admingroupscontrollerremovemember-deletes-association- | `defect_present_before_pr` | FAIL | FAIL | PASS | `app/controllers/admin/groupscontroller.rb` | `3f2c6cf4c3be…` |
| 8-B11 | B11-remove-member-link-wrongly-shown-for-automatic-groups-du | `defect_present_before_pr` | FAIL | ? | PASS | `app/assets/javascripts/admin/templates/groupmember.hbs` | `30cd877995c0…` |
| 8-B12 | B12-addmembers-crashes-with-500-when-usernames-param-is-an- | `defect_present_before_pr` | FAIL | FAIL | PASS | `app/controllers/admin/groups_controller.rb` | `54ea00fc36ec…` |
| 8-B13 | B13-admin-group-addmembers-leaves-usernames-input-uncleared- | `defect_present_before_pr` | FAIL | FAIL | PASS | `app/assets/javascripts/admin/controllers/admin-group.js.es6` | `206789998d30…` |
| 8-B14 | B14-group-members-reload-pagination-uses-live-edited-group-n | `defect_present_before_pr` | FAIL | FAIL | PASS | `app/assets/javascripts/discourse/models/group.js` | `ad54e56ce0fb…` |
| 8-B16 | B16-admin-group-addmembers-accepts-unbounded-comma-separated | `defect_present_before_pr` | FAIL | FAIL | PASS | `app/controllers/admin/groupscontroller.rb` | `5d00873f3bc6…` |
| 8-B17 | B17-admingroupscontroller-spec-regression-removed-coverage- | `defect_present_before_pr` | FAIL | FAIL | PASS | `spec/controllers/admin/groups_controller_spec.rb` | `484363107e67…` |
| 8-B19 | B19-admin-group-edit-form-implicitly-submits-on-enter-causin | `defect_present_before_pr` | FAIL | FAIL | PASS | `app/assets/javascripts/discourse/templates/admin/group.hbs` | `74091b098c67…` |
| 8-B21 | B21-admin-addmembers-can-re-add-existing-user-and-raise-reco | `defect_present_before_pr` | FAIL | FAIL | PASS | `app/controllers/admin/groups_controller.rb` | `47087817b034…` |
| 8-B26 | B26-admin-group-template-bypasses-usercountdisplay-and-rende | `defect_present_before_pr` | FAIL | FAIL | PASS | `admin/templates/group.hbs` | `27f3c7a24ad8…` |
| 8-B24 | B24-admin-groups-api-no-longer-exposes-get--admin-groups-id- | `inconclusive_env` | FAIL | — | FAIL | `config/routes.rb` | `26c87446e7ac…` |
| 8-B00 | B00-updating-a-group-without-visible-param-unintentionally-f | `not_a_bug_unconfirmed` | PASS | — | — | `app/controllers/admin/groups_controller.rb` | `8286ad9cbd36…` |
| 8-B23 | B23-label-forname-does-not-match-the-ember-text-field-i | `unresolved_file` | — | — | — | `N/A (template containing the new form markup is not present in the provided PR diff; issue is identified from the report only)` | `3b6626fc5ae2…` |
| 8-B27 | B27-userid-sent-in-a-delete-request-body-may-never-reach-par | `unresolved_file` | — | — | — | `None` | `5be13e50b2ec…` |
