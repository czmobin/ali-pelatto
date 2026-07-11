# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A single-file Telegram bot (`seler bot (19) (3).py`, ~4270 lines) for **Platoyar**, a Persian-language marketplace for buying/selling game accounts. Built on `python-telegram-bot` (v20+ async API) with `requests` for SMS. The entire application — config, persistence, handlers, and `main()` — lives in that one module. All user-facing text and much of the code's comments are in Persian (Farsi).

## Running & environment

There is no `requirements.txt`, README, tests, or lint config. Install deps and run manually:

```bash
pip install python-telegram-bot requests
python "seler bot (19) (3).py"   # note: filename has spaces + parens, must be quoted
```

The bot uses long polling (`app.run_polling`), so it just needs network access to Telegram — no webhook/server setup.

**Two things break out-of-the-box on non-Windows machines** and are worth fixing before running locally:
- `DATA_FOLDER = r"C:\Users\Adminstarter\Desktop\bot\data"` (top of file) is a hardcoded Windows path. All JSON persistence writes here; it must exist and be writable, or every `load_*`/`save_*` call fails.
- `TOKEN`, `KAVENEGAR_API_KEY`, `ADMIN_ID`, `CARD_NUMBER`, channel IDs, and pricing constants are all hardcoded literals near the top of the file — there is no `.env` or config file. Editing config means editing those literals.

## Architecture

The whole app is a **flag-driven state machine** over `python-telegram-bot`'s `context.user_data`. There is no `ConversationHandler` and no `'step'` key — instead, multi-step flows set/read ad-hoc boolean/id flags (e.g. `agahi_step`, `profile_step`, `waiting_payment_receipt`, `set_price_ad_id`, `waiting_group_link`).

Only **four** handlers are registered in `main()`:
- `CommandHandler("start")` → `start`
- `CommandHandler("searchadmin")` → `search_admin_command`
- `CallbackQueryHandler` → `handle_callbacks` — the single router for **every** inline button
- Three `MessageHandler`s (TEXT, PHOTO, VIDEO) → `handle_message` — the single router for **every** non-command message

Because of this, adding a feature almost always means editing one or both dispatchers:

- **`handle_callbacks`** (~line 3949): routes inline-button presses. Prefix-matched buttons (`price_set_`, `copy_link_`, `voice_call_`, `reject_*_ad_`, `confirm_charge_`, …) are checked first with `data.startswith(...)`, then an `elif` chain handles exact-match `data` strings. New buttons need a branch here.
- **`handle_message`** (~line 4107): routes text/photo/video by checking `context.user_data` flags **in order**, dispatching to the matching step handler and `return`ing. Order matters — the first matching flag wins. New multi-step input flows need a flag check here plus code to set/clear that flag.

### Persistence layer

State is JSON files in `DATA_FOLDER`, each with a `load_X()`/`save_X()` pair (e.g. `load_wallet`/`save_wallet`, `load_profiles`, `load_agahi`, `load_pending_ads`, `load_blacklist`, `load_price_requests`, `load_rejected_ads`, `load_referrals`). There is no DB and no locking — every read is a full file load, every write a full dump. Keys are Telegram user IDs (as strings). A `counter.json` (`get_next_ad_id`) issues sequential ad IDs. Some transient state lives only in module-level dicts (`otp_cache`, `temp_purchase_data`, `temp_group_links`, `voice_call_cooldown`) and is lost on restart.

### Core domain flows

- **Ad submission (`agahi`)**: profile-complete check → terms → multi-step form (`handle_normal_agahi_form` / `handle_price_only_form` gated by `price_only_mode`) → invoice → payment (wallet and/or card-to-card with receipt photo) → pending ad awaiting admin.
- **Admin review**: admin (identified by `ADMIN_ID`) approves/prices/sets button color and `publish_ad` posts to the Telegram channels (`MAIN_CHANNEL_ID`, `GAME_CHANNEL_ID`, `NEW_CHANNEL_ID`), or rejects with a reason (reject-reason buttons + free-text "other").
- **Buying**: buyer taps a channel button → `process_buy_from_channel` → confirm → receipt → admin confirms sale → seller submits group/account link → delivery.
- **Wallet**: charge (receipt → admin confirm) and withdraw (card + admin approval, `MIN_WITHDRAW_AMOUNT` floor).
- **Referrals & discounts**: `referral.json` tracks counts/bonuses; sellers can request discounts on live ads, admin approves.
- **OTP / SMS**: `send_*_via_kavenegar` call the Kavenegar HTTP API using the `KAVENEGAR_TEMPLATE_*` template names.

## Conventions

- Messages are sent with `parse_mode="HTML"`; user-supplied text must go through `escape_html()` before interpolation.
- Dates are Jalali (Persian calendar) via `now_jalali()`.
- Admin-only actions are gated by comparing the sender's id against `ADMIN_ID`.
- When adding a step handler, remember to **clear its `user_data` flag** at the end of the flow, or `handle_message` will keep routing the user back into it.
