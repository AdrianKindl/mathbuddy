# 014 Only your own history: Trainer sessions and ✓ marks

## Why
Bug: other players could see what you did.
- "Recent sessions" in the Trainer showed the newest sessions of **all**
  players. If one player trained Multiplication, every other player saw it.
- The ✓ next to a trick (Knowledge) or an article (Textbook) appeared as soon
  as **any** player had completed a round of it. You saw ticks for things you
  never practised.

Since spec 011 every player has an account, so this history must be private.

## What
- New reads for one player, newest / oldest first like the existing ones:
  `trainer_db.list_sessions_for(user_id, limit)`,
  `knowledge_db.list_rounds_for(user_id)` and
  `textbook_db.list_rounds_for(user_id)`. The owner comes from
  `activity_owners` (spec 012), the same table the Profile uses.
- Sessions and rounds without an owner (saved before spec 012) belong to
  nobody and are not shown.
- The Trainer screen ("Recent sessions") and the Knowledge and Textbook lists
  (✓ marks) use them for the signed-in player. With no own sessions the Trainer
  shows the existing caption "No finished sessions yet…".
- The existing `list_sessions()` and `list_rounds()` stay as they are (all
  players), so the reviewed tests of specs 002, 009 and 010 keep their
  assertions.
- Two test helpers that save a completed Tricks round directly
  (`save_completed_trick_round` in `tests/test_textbook_ui.py` and
  `tests/test_textbook_practice_ui.py`) now also record the signed-in test
  player as owner, like a real round. Their assertions are unchanged.

## Out of scope
Anything else on the screens, the Profile and the leaderboard (already per
player or public by design).

## Done when
- `uv run pytest` passes, including `tests/test_own_history.py`.
- Manual check with two accounts: each finishes a Trainer session and a
  Tricks round; each sees only their own row under "Recent sessions" and only
  their own ✓.
