# Basic Test Cases (Aligned with what-next.md v0.1.0)

## 1) Main Page (Candidate Details)
- **TC-01**: Submit with valid required fields (name, email, role, branch/department from defined list) → details saved and confirmation shown.
- **TC-02**: Missing required field → inline validation error displayed.
- **TC-03**: Invalid email format → validation error displayed.
- **TC-04**: Duplicate email → system prevents duplicate and shows message.
- **TC-05**: Branch/Department uses a controlled input (dropdown/autocomplete) → free-text not allowed or normalized to predefined values.
- **TC-06**: Cancel/Back from details page → data not saved.

## 2) Live Interview Flow
- **TC-07**: Start interview from candidate profile → interview session created.
- **TC-08**: Live interview timer starts on session begin → visible and updates in real time.
- **TC-09**: End interview action available → confirmation shown and session marked completed.
- **TC-10**: Attempt to end interview without required responses (if enforced) → warning shown.

## 3) Questions Section (Navigation & Notes)
- **TC-11**: Questions grouped by skill → sections render with correct grouping.
- **TC-12**: Large question bank → navigation remains usable (collapsible groups or pagination works).
- **TC-13**: Answer question and move to next → response saved and next question shown.
- **TC-14**: Asked question includes interviewer note field → note saved per question.
- **TC-15**: Notes persist on refresh/reopen interview → previously entered notes shown.

## 4) Notes Section (Skills)
- **TC-16**: Skills dropdown shows existing skills list.
- **TC-17**: Selecting `other` allows custom skill entry → custom value saved.

## 5) Recent Interviews Section
- **TC-18**: Filter by role → list updates to matching role.
- **TC-19**: Filter by recommendation (Hire/No Hire/Borderline) → list updates correctly.
- **TC-20**: Sort by skill level (High on top) → ordering correct.
- **TC-21**: Skill score displayed beside candidate name → matches stored score.

## 6) Question Bank Editor
- **TC-22**: Select existing skill name when creating/editing a question → saved with selected skill.
- **TC-23**: Enter new skill name when not in list → new skill saved and appears in list.

## 7) Summary Generation
- **TC-24**: Summary shows only asked questions → unasked questions excluded.
- **TC-25**: Summary includes interviewer note per asked question.
- **TC-26**: Attempt summary before interview completion → blocked with message.

## 8) Interview State on Main Page
- **TC-27**: Completed interviews appear in a read-only section (no resume, no edit).
- **TC-28**: Ongoing interviews appear in a separate section with resume controls.

## 9) End-to-End Flow
- **TC-29**: Add candidate → start interview → answer questions with notes → end interview → summary reflects asked questions and notes.