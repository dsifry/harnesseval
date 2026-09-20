# PR 8 — 6 VERIFIED defects (total gold, excluding the 42 original goldens)

Every entry below already passed: its own test FAILS on the PR head, its own minimal fix makes it PASS, and the
bundle's own (sibling) fix leaves it RED — i.e. an executed orthogonality check. The question is whether any two
entries nevertheless describe the SAME underlying defect (same root cause, same code path, one fix would cover both).

## 8-D01  [D-verified]  bundle=8-B00
- label: Updating a group without `visible` param unintentionally flips visibility to false
- location: app/controllers/admin/groups_controller.rb:(no line refs)
- example finding: [bug] the rewritten public members action applies a default limit of 50 to every group — the removed code returned the complete member list for non-automatic groups and capped only automatic groups at 200 — while nothing in this diff adds pagination to the public group members page (the group-member

## 8-D02  [D-verified, orthogonal]  bundle=8-B05
- label: Incorrect visible assignment on create/update: unconditional and strict string comparison cause silent false
- location: app/controllers/admin/groups_controller.rb:(no line refs)
- example finding: [bug] the group write contract was changed in a single step with no expand/contract window: the nested group[...] payload and the patch changes membership api were removed and replaced by flat top-level params plus new /members endpoints, so an old-contract put/patch reaches update with params[:visi

## 8-D03  [D-verified]  bundle=8-B03
- label: Admin::GroupsController#add_members splits usernames without trimming, causing spaced names to be skipped while still returning success
- location: app/controllers/admin/groups_controller.rb:(no line refs)
- example finding: [bug] addmembers passes each token of the raw comma-joined string to user.findbyusername(username) without stripping (usernames.split(",").each do |username| if user = user.findbyusername(username)), so a padded token like " alice" from an admin typing "bob, alice" in the free-text add-members field

## 8-D04  [D-verified]  bundle=8-B04
- label: Admin group creation drops submitted aliaslevel and saves default instead
- location: app/controllers/admin/groups_controller.rb:(no line refs)
- example finding: [bug] the rewritten create action reads only params[:name] and params[:visible] while the frontend posts asjson() verbatim — which includes aliaslevel — so the alias level selected in the new-group form is silently discarded and the group is created with aliaslevel 0. an admin who creates a group wi

## 8-D05  [D-verified]  bundle=8-B15
- label: Admin::GroupsController specs hardcode group id=1, implicitly depending on seeded automatic group
- location: spec/controllers/admin/groups_controller_spec.rb:(no line refs)
- example finding: [bug] the '.update ignore name change on automatic group' test hardcodes id: 1 and group.find(1), asserting behavior against whatever group happens to have id 1 in the test database rather than a group the test creates. the test's validity depends on discourse's seeded automatic groups keeping id 1;

## 8-D06  [D-verified]  bundle=8-B18
- label: Group name is stripped on create but not on update, allowing whitespace-padded names
- location: app/controllers/admin/groups_controller.rb:(no line refs)
- example finding: [advisory] create strips the group name ((params[:name] || '').strip) but update does not (group.name = params[:name]), so the same value round-trips differently through the two endpoints. an admin who edits an existing group and submits a name with trailing whitespace bypasses the normalization cre
