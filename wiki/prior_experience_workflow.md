# Prior Experience & Migration User Workflow

This guide explains how flight school users should enter previous experience and prior syllabus progress after installing or upgrading the Flight School Management modules.

The workflow is designed for manual onboarding of organizations that already have historical flight hours, simulator time, solo time, instructor time, and syllabus completion records. It does **not** create operational flights, scheduled flights, aircraft utilization, or document attachments.

---

## 1. Purpose and Scope

Use **Prior Experience & Migration** when you need to record training or personnel history that happened before the organization started using this Odoo system.

### Supported prior data

1. Previous flight hours.
2. Previous simulator hours.
3. Previous solo hours.
4. Previous instructor hours for instructors.
5. Previous enrollment activity progress.
6. Previous syllabus mission completions.
7. Source and verification metadata, such as previous school, employer, logbook reference, or migration batch.

### Out of scope

1. Historical scheduled flights.
2. Fake operational flight logs.
3. Aircraft total-hour updates from prior experience.
4. Document or evidence attachments.
5. Personnel history or admin staff history.
6. Automated CSV/import processing.

---

## 2. Prerequisites

Before entering prior experience, confirm that the core operational records already exist.

### 2.1 Required modules

The following modules must be installed or upgraded:

1. `fs_core`
2. `fs_fleet`
3. `fs_people`
4. `fs_training`
5. `fs_scheduling`
6. `fs_flights`

`fs_documents` is not required for this workflow.

### 2.2 Required access rights

| Task                                     | Required group                         |
| ---------------------------------------- | -------------------------------------- |
| View prior experience records            | Flight School User or higher           |
| Create and edit prior experience records | Flight School Manager or Administrator |
| Approve records                          | Flight School Manager or Administrator |
| Apply records to totals/progression      | Flight School Manager or Administrator |
| Revert applied records                   | Flight School Manager or Administrator |

Example:

> A training coordinator can prepare source data, but an Odoo user in the **Flight School Manager** group should create, approve, and apply the record.

### 2.3 Required master data

Confirm these records exist before entering prior data:

1. **People**
   - Student records for student history.
   - Pilot records for licensed pilot history.
   - Instructor records for instructor history.
2. **Training**
   - Flight activities.
   - Class types.
   - Training classes.
   - Student/person enrollments.
   - Missions if syllabus progress will be recorded.
3. **Fleet context**
   - Aircraft categories and aircraft types if you want to describe the prior-hours source context.
   - These are informational in this workflow and do not update aircraft totals.

### 2.4 Recommended source preparation

Prepare one source packet per person or per migration batch.

Example source packet:

| Field               | Example                  |
| ------------------- | ------------------------ |
| Person              | Student: Ahmed Ben Salem |
| Source type         | Previous School          |
| Source organization | Tunis Flight Academy     |
| Source reference    | Logbook pages 12-18      |
| Source date range   | 2025-01-01 to 2025-08-31 |
| Flight hours        | 12.5                     |
| Simulator hours     | 3.0                      |
| Solo hours          | 1.2                      |
| Enrollment          | CPL24A                   |
| Activity            | MAN Dual                 |
| Missions completed  | Mission 1, Mission 2     |

---

## 3. Installation Verification Steps

After installation or upgrade, verify the feature is available before entering production data.

### 3.1 Verify module installation

1. Log in as an administrator.
2. Open **Apps**.
3. Search for **Flight School Flights**.
4. Confirm the module is installed and up to date.
5. Search for **Flight School Training**.
6. Confirm the module is installed and up to date.

Command-line example for administrators:

```bash
odoo-bin -c /path/to/odoo.conf -d flight_school \
  -u fs_training,fs_flights \
  --stop-after-init
```

### 3.2 Verify menu access

1. Open the Odoo main menu.
2. Go to **Flights**.
3. Confirm the menu item **Prior Experience** is visible.
4. Open **Prior Experience**.
5. Confirm the list view title shows **Prior Experience & Migration**.

Expected result:

> You can see prior experience records with status badges such as **Draft**, **In Review**, **Approved**, and **Applied**.

### 3.3 Verify form fields

Open a new prior experience form and confirm these sections are visible:

1. Header statusbar.
2. Person section.
3. Summary totals.
4. **Hour Details** tab.
5. **Syllabus Progression** tab.
6. **Source & Verification** tab.
7. **Notes** tab.

### 3.4 Verify related screens

1. Open **Training** and select an enrollment.
2. Confirm the enrollment form includes a **Prior Progression** tab.
3. Confirm the enrollment smart buttons include prior-hour and prior-mission counters.
4. Open **Training > Mission Completions**.
5. Confirm source fields and the **Prior Experience** filter are available.

---

## 4. Workflow Overview

The prior experience record follows this controlled lifecycle:

1. **Draft** — Enter source, person, hour details, and syllabus progression.
2. **In Review** — Submit the record for review.
3. **Approved** — Manager confirms the record is ready to affect totals and progression.
4. **Applied** — System updates person totals, enrollment hours, and mission completions.
5. **Reverted to Approved** — Manager can revert applied deltas for correction.
6. **Cancelled** — Record is cancelled before application.

Important behavior:

- Applying the same record twice does not double-count hours.
- Reverting uses stored applied deltas, not recalculated values.
- Applied records cannot be edited directly; revert first, correct, then reapply.

---

## 5. Phase 1 — Create the Prior Experience Header

### Steps

1. Go to **Flights > Prior Experience**.
2. Click **New**.
3. In **Person**, select the **Person Type**:
   1. Student
   2. Pilot
   3. Instructor
4. Select the matching person field:
   - Use **Student** when Person Type is Student.
   - Use **Pilot** when Person Type is Pilot.
   - Use **Instructor** when Person Type is Instructor.
5. Enter a short **Description**.
6. Set the **Entry Date**.
7. Open **Source & Verification**.
8. Enter source details.
9. Save the record.

### Example

| Field               | Value                              |
| ------------------- | ---------------------------------- |
| Person Type         | Student                            |
| Student             | Ahmed Ben Salem                    |
| Description         | Previous school onboarding history |
| Entry Date          | 2026-05-20                         |
| Source Type         | Previous School                    |
| Source Organization | Tunis Flight Academy               |
| Source Reference    | Logbook pages 12-18                |
| Source Start Date   | 2025-01-01                         |
| Source End Date     | 2025-08-31                         |
| Verified By         | Training Manager                   |
| Verified Date       | 2026-05-20                         |

### Validation checks

The system will block the record if:

1. No person is selected.
2. More than one person is selected.
3. The selected person does not match the person type.
4. The source start date is after the source end date.

---

## 6. Phase 2 — Enter Prior Hour Details

Use the **Hour Details** tab for detailed prior hours.

### 6.1 Add a prior-hour line

1. Open the **Hour Details** tab.
2. Add a new line.
3. Select **Hour Kind**:
   - Flight
   - Simulator
   - Solo
   - Instruction
4. Enter **Hours**.
5. Optionally select an **Enrollment**.
6. Optionally select an **Activity**.
7. Keep **Count Toward Enrollment** checked if the line should update training progress.
8. Optionally enter aircraft category/type context.
9. Optionally enter a source note.
10. Save.

### 6.2 Example: prior flight hours that count toward enrollment

| Field                   | Value                |
| ----------------------- | -------------------- |
| Hour Kind               | Flight               |
| Hours                   | 2.5                  |
| Enrollment              | CPL24A               |
| Activity                | MAN Dual             |
| Count Toward Enrollment | Yes                  |
| Aircraft Category       | Single Engine Piston |
| Aircraft Type           | Cessna 172           |
| Source Note             | Logbook page 12      |

Expected result after apply:

1. Student `total_flight_hours` increases by 2.5.
2. The selected enrollment activity line increases by 2.5.
3. Enrollment progression recalculates automatically.

### 6.3 Example: simulator hours

| Field                   | Value                        |
| ----------------------- | ---------------------------- |
| Hour Kind               | Simulator                    |
| Hours                   | 1.0                          |
| Enrollment              | CPL24A                       |
| Activity                | VSV SIM                      |
| Count Toward Enrollment | Yes                          |
| Source Note             | Simulator certificate line 4 |

Expected result after apply:

1. Person `total_sim_hours` increases by 1.0.
2. The matching enrollment simulator activity increases by 1.0.

### 6.4 Example: solo hours that should not affect enrollment progress

| Field                   | Value              |
| ----------------------- | ------------------ |
| Hour Kind               | Solo               |
| Hours                   | 0.8                |
| Enrollment              | Empty              |
| Activity                | Empty              |
| Count Toward Enrollment | No                 |
| Source Note             | Logbook solo total |

Expected result after apply:

1. Person `solo_hours` increases by 0.8.
2. No enrollment activity row is updated.

### 6.5 Example: instructor hours

| Field                   | Value                                |
| ----------------------- | ------------------------------------ |
| Person Type             | Instructor                           |
| Hour Kind               | Instruction                          |
| Hours                   | 4.0                                  |
| Count Toward Enrollment | No                                   |
| Source Note             | Previous employer instruction record |

Expected result after apply:

1. Instructor `total_instruction_hours` increases by 4.0.
2. No student enrollment is updated unless a separate flight/simulator line is added with enrollment context.

### 6.6 Legacy aggregate hours

If an older record only contains aggregate fields such as **Flight Hours**, **Simulator Hours**, **Solo Hours**, or **Instruction Hours**, the system preserves those fields for compatibility.

Recommended practice:

1. Use detailed lines for new prior data.
2. Use legacy aggregate fields only for old records or quick migration corrections.
3. Add activities and enrollments when the hours should affect training progression.

---

## 7. Phase 3 — Enter Prior Syllabus Progression

Use the **Syllabus Progression** tab when the person completed missions before system onboarding.

### Steps

1. Open the prior experience record.
2. Go to **Syllabus Progression**.
3. Add a new line.
4. Select **Enrollment**.
5. Select **Mission**.
6. Enter **Completion Date**.
7. Optionally select the recorded instructor.
8. Optionally enter source organization and source reference.
9. Add notes if needed.
10. Save.

### Example

| Field               | Value                        |
| ------------------- | ---------------------------- |
| Enrollment          | CPL24A                       |
| Mission             | Mission 01 - Familiarization |
| Completion Date     | 2025-02-15                   |
| Recorded Instructor | Capt. Nabil Trabelsi         |
| Source Organization | Tunis Flight Academy         |
| Source Reference    | Training record TR-2025-02   |
| Notes               | Completed before transfer    |

Expected result after apply:

1. A matching `fs.mission.completion` record is created or updated.
2. The mission completion is marked completed.
3. Source is set to **Prior Experience**.
4. Source metadata identifies the prior syllabus completion line.

### Duplicate behavior

If a mission completion already exists for the same enrollment and mission:

1. The existing record is updated instead of creating a duplicate.
2. The previous source state is stored on the prior syllabus line.
3. Revert restores the previous mission completion state when safe.

---

## 8. Phase 4 — Review and Approve

Only managers or administrators should approve records.

### Steps

1. Open the prior experience record.
2. Review the person selection.
3. Review source details.
4. Review hour detail lines.
5. Review syllabus progression lines.
6. Confirm the totals in **Summary Totals**.
7. Click **Submit for Review** if the record is still in Draft.
8. Click **Approve**.

### Example review checklist

| Check                        | Expected result                                   |
| ---------------------------- | ------------------------------------------------- |
| Person Type and person match | Student type has a student selected               |
| Date range                   | Start date is before end date                     |
| Hours                        | No negative values                                |
| Enrollment                   | Belongs to the selected person                    |
| Activity                     | Present when Count Toward Enrollment is checked   |
| Syllabus mission             | Belongs to the selected enrollment/class type     |
| Source details               | Organization/reference are clear enough for audit |

---

## 9. Phase 5 — Apply Prior Data

Applying is the step that updates operational aggregates and training progression.

### Steps

1. Confirm the record is in **Approved** state.
2. Click **Apply Prior Data**.
3. Wait for the form to refresh.
4. Confirm the status changed to **Applied**.
5. Confirm the **Applied Date** and **Applied By** fields are populated.

### What the system updates

| Data entered             | Updated record                       |
| ------------------------ | ------------------------------------ |
| Flight hour line         | Person `total_flight_hours`          |
| Simulator hour line      | Person `total_sim_hours`             |
| Solo hour line           | Person `solo_hours`                  |
| Instructor hour line     | Instructor `total_instruction_hours` |
| Counted enrollment line  | `fs.enrollment.hours.hours_logged`   |
| Syllabus completion line | `fs.mission.completion`              |

### What the system does not update

1. Aircraft total hours.
2. Scheduled flights.
3. Operational flight logs.
4. Daily operations boards.
5. Document records.

---

## 10. Phase 6 — Validate the Applied Record

After applying, validate the result from multiple screens.

### 10.1 Validate person totals

1. Open the related Student, Pilot, or Instructor record.
2. Check the experience totals.
3. Confirm the prior line totals were added once.

Example:

| Before                           | Prior line     | After                            |
| -------------------------------- | -------------- | -------------------------------- |
| Student total flight hours: 10.0 | Flight: 2.5    | Student total flight hours: 12.5 |
| Student simulator hours: 1.0     | Simulator: 1.0 | Student simulator hours: 2.0     |

### 10.2 Validate enrollment progress

1. Open the related enrollment.
2. Go to **Training Progress**.
3. Check mandatory and additional activity hours.
4. Confirm overall progression updated.
5. Go to **Prior Progression**.
6. Confirm prior hour lines and prior syllabus completions are visible.

Example:

| Activity | Before | Prior applied | After |
| -------- | ------ | ------------- | ----- |
| MAN Dual | 0.0    | 2.5           | 2.5   |
| VSV SIM  | 0.0    | 1.0           | 1.0   |

### 10.3 Validate mission completion

1. Open **Training > Mission Completions**.
2. Use the **Prior Experience** filter.
3. Search for the enrollment and mission.
4. Confirm:
   1. Completed is checked.
   2. Completion date is correct.
   3. Source is **Prior Experience**.
   4. Source organization and reference are correct.

### 10.4 Validate audit fields

On the prior experience record, confirm:

1. Status is **Applied**.
2. Applied date is set.
3. Applied by is set.
4. Source and verification fields remain visible.
5. Applied delta fields are visible on detailed line forms.

---

## 11. Correcting or Reverting Prior Experience

Applied records are locked for direct edits. This protects the system from accidental double-counting.

### 11.1 Revert an applied record

1. Open **Flights > Prior Experience**.
2. Open the applied record.
3. Click **Revert Prior Data**.
4. Confirm the warning.
5. Verify the state returns to **Approved**.

Expected result:

1. Person totals are reduced by the stored applied deltas.
2. Enrollment hours are reduced by the stored applied deltas.
3. Mission completions created by this prior record are removed.
4. Existing mission completions updated by this prior record are restored when safe.

### 11.2 Correct and reapply

1. Revert the applied record.
2. Edit the hour lines or syllabus lines.
3. Save.
4. Click **Apply Prior Data** again.
5. Validate totals and progression.

### Example correction

Scenario:

> A student was entered with 2.5 prior MAN Dual hours, but the source logbook shows 2.0.

Steps:

1. Revert the record.
2. Change the hour line from `2.5` to `2.0`.
3. Save.
4. Apply again.
5. Confirm student total and enrollment MAN Dual hours reflect `2.0`.

---

## 12. Troubleshooting

### 12.1 The Prior Experience menu is not visible

Possible causes:

1. `fs_flights` is not installed or upgraded.
2. The user does not have a Flight School group.
3. The apps list was not updated after deployment.

Resolution:

1. Upgrade `fs_flights`.
2. Assign the user to **Flight School User** or higher.
3. Refresh the browser and update the apps list.

### 12.2 The Apply button is not visible

Possible causes:

1. The record is not in **Approved** state.
2. The user is not a Manager or Administrator.
3. The record is already Applied.

Resolution:

1. Submit and approve the record first.
2. Ask a manager to apply it.
3. If already applied, validate the output or revert for correction.

### 12.3 The system says the person selection is invalid

Possible causes:

1. Person Type is Student, but Pilot or Instructor is selected.
2. More than one person field has a value.
3. No person was selected.

Resolution:

1. Clear the wrong person field.
2. Select exactly one matching person.
3. Save again.

### 12.4 Enrollment progress did not change

Possible causes:

1. **Count Toward Enrollment** is unchecked.
2. No enrollment was selected on the hour line.
3. No activity was selected on the hour line.
4. The line is Solo or Instruction and was intentionally not counted toward enrollment.

Resolution:

1. Revert the record if already applied.
2. Select the correct enrollment.
3. Select the correct activity.
4. Check **Count Toward Enrollment** if appropriate.
5. Reapply the record.

### 12.5 Mission completion was not created

Possible causes:

1. No syllabus progression line was entered.
2. Enrollment or mission is missing on the syllabus line.
3. The record was approved but not applied.

Resolution:

1. Add a syllabus progression line.
2. Select enrollment, mission, and completion date.
3. Approve and apply the record.
4. Check **Training > Mission Completions** with the **Prior Experience** filter.

### 12.6 Hours appear doubled

Possible causes:

1. The same history was entered in two different prior experience records.
2. The person already had opening balances before migration.
3. Similar prior data was also entered as an operational flight.

Resolution:

1. Search **Flights > Prior Experience** for the person.
2. Review all applied records.
3. Revert duplicate prior records.
4. Avoid creating fake operational flights for migration data.

### 12.7 Applied records cannot be edited

This is expected.

Resolution:

1. Click **Revert Prior Data**.
2. Edit the record.
3. Apply it again.

### 12.8 A user can view but not create records

This is expected for basic users.

Resolution:

1. Ask a Flight School Manager or Administrator to create or apply the record.
2. Do not grant manager rights unless the user is authorized to change totals and progression.

---

## 13. Recommended Operating Controls

Use these controls for reliable migration and auditability.

1. Enter prior data from verified sources only.
2. Use one record per person/source packet unless a batch record is easier to audit.
3. Always fill source organization and source reference when available.
4. Prefer detailed lines over legacy aggregate fields.
5. Only check **Count Toward Enrollment** when the activity should affect syllabus progression.
6. Have a manager review every record before applying.
7. Validate person totals and enrollment progression immediately after applying.
8. Revert and correct mistakes instead of editing database values manually.
9. Do not create operational flight logs for historical migration data.
10. Do not use prior experience to update fleet aircraft totals.

---

## 14. End-to-End Example

### Scenario

Student Ahmed Ben Salem transfers from another school with:

1. 2.5 MAN Dual flight hours.
2. 1.0 VSV SIM simulator hour.
3. Mission 01 already completed.
4. Source reference: `LOG-2025-18`.

### Steps

1. Go to **Flights > Prior Experience**.
2. Click **New**.
3. Select:
   - Person Type: `Student`
   - Student: `Ahmed Ben Salem`
4. Enter:
   - Description: `Transfer history from Tunis Flight Academy`
   - Source Type: `Previous School`
   - Source Organization: `Tunis Flight Academy`
   - Source Reference: `LOG-2025-18`
5. Open **Hour Details**.
6. Add line 1:
   - Hour Kind: `Flight`
   - Hours: `2.5`
   - Enrollment: `CPL24A`
   - Activity: `MAN Dual`
   - Count Toward Enrollment: `Yes`
7. Add line 2:
   - Hour Kind: `Simulator`
   - Hours: `1.0`
   - Enrollment: `CPL24A`
   - Activity: `VSV SIM`
   - Count Toward Enrollment: `Yes`
8. Open **Syllabus Progression**.
9. Add line:
   - Enrollment: `CPL24A`
   - Mission: `Mission 01 - Familiarization`
   - Completion Date: `2025-02-15`
10. Click **Submit for Review**.
11. As a manager, click **Approve**.
12. Click **Apply Prior Data**.
13. Validate:

- Student flight hours increased by `2.5`.
- Student simulator hours increased by `1.0`.
- Enrollment activity hours increased.
- Mission completion is marked completed with Source = `Prior Experience`.

---

## 15. Quick Reference Checklist

Before applying a prior experience record, confirm:

1. [ ] Correct person type and person selected.
2. [ ] Source organization and reference entered.
3. [ ] Date range is valid.
4. [ ] Hour lines are detailed and non-negative.
5. [ ] Enrollment selected where progression should change.
6. [ ] Activity selected where enrollment hours should change.
7. [ ] Syllabus progression lines have enrollment, mission, and completion date.
8. [ ] Manager reviewed the record.
9. [ ] Record is approved.
10. [ ] Post-apply validation is completed.
