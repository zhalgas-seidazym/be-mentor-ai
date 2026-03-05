# User Flows

This document describes the main user flows (business logic) for the MentorAI platform.
It is intentionally higher-level than the per-route API docs.

## Auth & Session

1. **Send OTP**: user requests an OTP code to email.
2. **Verify OTP & Register**: user submits OTP and credentials, receives access/refresh tokens.
3. **Login**: user can log in with email/password and receive tokens.
4. **Token Refresh**: refresh token returns a new access token.

## Onboarding (Profile Creation)

1. User completes profile with:
   - name
   - city
   - direction
   - skills
   - timezone
2. Profile creation:
   - verifies city and direction exist
   - stores timezone (used for streak logic)
   - attaches selected skills
   - generates additional `to_learn` modules via AI
   - seeds theoretical questions for new skills if needed

## Learning Modules (To Learn)

1. AI-generated modules are stored as `user_skills` with `to_learn=True`.
2. Modules are used to build interview sessions and recommendations.

## Interview Flow

1. **Start interview**:
   - only one active interview allowed
   - selects 10 random main questions from user modules
2. **Answer**:
   - validates current question (main or follow-up)
   - transcribes audio
   - evaluates answer
   - may generate follow-up (max 2)
3. **Completion**:
   - when all main questions answered, session is marked `COMPLETED`
   - streak is updated in the same transaction:
     - same day: no change
     - yesterday: current_streak += 1
     - older/no previous day: current_streak = 1
   - updates `last_interview_day` and `longest_streak`

## Learning Recommendations

1. Endpoint is protected (requires auth).
2. Recommendations can be requested for a skill only if:
   - the skill exists in user modules (`to_learn=True`).
3. Flow:
   - if recommendations already exist in DB, return them
   - otherwise generate via OpenAI (web search), store, and return

## Streak

1. Streak values:
   - `current_streak`
   - `longest_streak`
   - `last_interview_day`
2. Streak can be retrieved separately via `/user/profile/streak`.

## Edge Cases

- Interview start fails if no modules or insufficient questions.
- Interview answer fails if session is inactive or question is not current.
- Recommendations request fails if skill is not in user modules.
