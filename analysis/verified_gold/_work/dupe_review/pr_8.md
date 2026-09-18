# PR 8 — 5 verified hidden gold bugs (id, summary, file:startline-endline, first supporting report)

## 8-B00
- summary: Updating a group without `visible` param unintentionally flips visibility to false
- location: app/controllers/groupscontroller.rb:19, 19-31, 19-36, 22, 22-26, 23, 24, 25
- reports: 150
- example report: public group members page fetches only 50 users and has no pagination controls, making later members inaccessible

## 8-B03
- summary: Admin::GroupsController#add_members splits usernames without trimming, causing spaced names to be skipped while still returning success
- location: app/controllers/admin/groupscontroller.rb:53, 56-69, 65-82, 71, 72
- reports: 51
- example report: addmembers doesn't .strip split username items, so 'bob, alice' silently drops ' alice'

## 8-B04
- summary: Admin group creation drops submitted aliaslevel and saves default instead
- location: app/controllers/admin/groupscontroller.rb:22, 23, 23-33, 24-26, 25, 540
- reports: 48
- example report: admin group creation ignores the submitted aliaslevel, causing new groups to retain the default alias level

## 8-B15
- summary: Admin::GroupsController specs hardcode group id=1, implicitly depending on seeded automatic group
- location: spec/controllers/admin/groupscontrollerspec.rb:94
- reports: 7
- example report: spec/controllers/admin/groupscontrollerspec.rb automatic-group tests hardcode groupid: 1 and group.find(1), relying on seed-data ids

## 8-B18
- summary: Group name is stripped on create but not on update, allowing whitespace-padded names
- location: admin/groupscontroller.rb:24
- reports: 4
- example report: groupscontrollerupdate does not strip group.name (unlike create), so a name like " bob " can be saved via update, inconsistent with create and the username-style name rule
