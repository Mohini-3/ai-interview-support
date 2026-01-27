# Basic Test Cases

## 1) Add Candidate Details
- **TC-01**: Submit with valid required fields (name, email, role) → details saved and confirmation shown.
- **TC-02**: Missing required field → inline validation error displayed.
- **TC-03**: Invalid email format → validation error displayed.
- **TC-04**: Duplicate email → system prevents duplicate and shows message.
- **TC-05**: Cancel/Back from details page → data not saved.

## 2) Interview Flow
- **TC-06**: Start interview from candidate profile → interview session created.
- **TC-07**: Answer question and move to next → response saved and next question shown.
- **TC-08**: Attempt to continue without answering (if required) → validation warning.
- **TC-09**: Pause and resume interview → progress and answers preserved.
- **TC-10**: Complete interview → session marked completed and summary available.

## 3) Question Bank
- **TC-11**: Create new question with required fields → question saved.
- **TC-12**: Missing question text → validation error.
- **TC-13**: Edit existing question → changes persist.
- **TC-14**: Delete question → removed from list and cannot be used in interview.
- **TC-15**: Search/filter by topic/difficulty → correct results shown.

## 4) Report Generation
- **TC-16**: Generate report after completed interview → report created.
- **TC-17**: Report includes candidate info, answers, and scores.
- **TC-18**: Regenerate report after updating answers → updated data shown.
- **TC-19**: Export/download report (if supported) → file downloads successfully.
- **TC-20**: Attempt report before interview completion → blocked with message.

## 5) End-to-End Flow
- **TC-21**: Add candidate → start interview → complete → generate report → all steps succeed.
- **TC-22**: Question bank update → new question appears in interview pool.
- **TC-23**: New candidate created with role-specific questions → correct questions used.

## 6) Access & Errors
- **TC-24**: Unauthorized access to interview/report → access denied.
- **TC-25**: Network/API failure during save → error message and retry option.