# Candidate Improvement Journey Upgrade

This frontend upgrade keeps the research rule that candidate-facing outputs do not display model confidence, communication percentages, or numeric communication sub-scores.

The progress bar represents only factual completion of practice activities.

## Added candidate experience

- Personalised current focus areas from the latest weaknesses returned by the backend
- Next recommended practice task
- Factual task-completion progress bar
- Practice-day count
- Consecutive practice-day streak
- Tasks completed today
- 7-day practice path
- Professional-English sentence patterns selected from the current weaknesses
- Mock interview practice
- Motivational coaching notes based on practice completion only
- Browser localStorage persistence
- Reset checklist option
- Re-record prompt after completing a practice cycle

## Integration

`App.jsx` now passes these props to `PracticePlan`:

- `activities`
- `mockInterviewPrompts`
- `weaknesses`
- `communicationLevel`

No backend API change is required.
