# SmartEx User Study – Smart Office

This repository contains the online user study for my bachelor's thesis at the University of Cologne. The thesis looks at **LLM-generated contrastive explanations** for a smart office: explanations that answer questions like *"Why is the status light orange and not green?"*

The whole study is **one web page** (`index.html`). Participants do not play a role: they follow Alice and Bob, two employees, through three situations in a small smart office (stories in third person) and judge SmartEx's explanations for them.

**Study link:** https://mgobsch.github.io/contrastive-explanations-llm-smart-environments/study/
**Preview link (nothing is saved):** https://mgobsch.github.io/contrastive-explanations-llm-smart-environments/study/?preview=1
**LimeSurvey (part 1, optional):** https://survey.uni-koeln.de/index.php/326863?

---

## Two ways to run the study

| Mode | Setting | Flow |
|---|---|---|
| **Standalone** (default) | `LIMESURVEY_MODE: false` | Participants open the study link. Consent and "About you" happen on the page. |
| **With LimeSurvey** | `LIMESURVEY_MODE: true` | Participants start in LimeSurvey (consent, demographics, CAPTCHA). LimeSurvey forwards them to the page with their response ID (`?ls={SAVEDID}`). The page skips its own consent and "About you" and saves the ID as `ls_id`. |

In LimeSurvey mode, the page only starts with a code. Without one, it shows "Please start the study here" with a link to LimeSurvey (`LIMESURVEY_URL`). In `TEST_MODE` it also runs without a code, so you can keep testing.

**LimeSurvey settings used:** anonymised responses on, IP address off, timings on, CAPTCHA on, End URL `https://mgobsch.github.io/thesis-study/?ls={SAVEDID}` with "Automatically load end URL" on. The language of the link (`lang=de` / `lang=en`) is passed on to the page. (At the time of the study, the repository was called `thesis-study`.)

**Matching the data:** `ls_id` in the Google Sheet = response ID in LimeSurvey. Rows without a matching LimeSurvey ID should be excluded.

---

## What participants do

About 15–20 minutes, in English or German (switch at the top right). Every screen has a "What to do" box. On the "Ask SmartEx" page it shows the steps bit by bit (before asking, after asking, after locking in). SmartEx is always described in the third person.

1. **Welcome and consent** *(standalone mode only)*
2. **About you:** age, familiarity with smart devices, technical background *(standalone mode only)*
3. **The smart office:** the meeting room, the status light, the smart office system and SmartEx (the note that the rules were created by different people comes later, on the rules page). A yellow note above the clock (and the "Times" section of the office note) shows office hours 08:00–18:00, lunchtime 11:00–13:00 and closing time 18:00–23:00
4. **The smart devices:** click on 7 devices (door sensor, motion sensor, status light, forecast, clock, smoke/CO₂ detector, fan)
5. **The office rules:** all 6 rules that change the status light, each with its owner ("Created by: Alice/Bob"), with a note that some rules may seem confusing and that this is normal. From here on, the yellow **office note** is available. It starts closed (a tab at the edge) and a red hint shows where to open it. In the office note, each rule is a card with a coloured stripe (the light colour), like on the rules page.
6. **Alice and Bob:** the two employees and their technical level. In each situation, one of them asks SmartEx something.
7. **Quick check:** 3 questions (answer order shuffled per participant)
8. **Three situations (random order),** each with three steps:
   - **Story:** what Alice or Bob sees at that moment (third person)
   - **Ask SmartEx:** Alice/Bob asks SmartEx. The participant first chooses **which colour they think Alice/Bob expected** instead, then places the **two rules they think Alice/Bob expected most** (all rules except the one that is currently active) on places 1 and 2, and locks them in. Rules the person created carry a **"Created by Alice" / "Created by Bob"** tag as a hint.
   - **Rate the explanations:** two or three explanations (A, B, C), each rated **with Alice/Bob in mind** (Alice: knows a bit about technology; Bob: not technical, prefers short, everyday language): two statements on a 1–5 scale (*"This explanation is easy for Alice to understand"*, *"This explanation is helpful for Alice"*), then **which explanation is best for Alice/Bob** and a comprehension question. Above the explanations, a short note says that they do not always compare with the same alternative (e.g. "not green" vs. "not blue").
9. **Final questions:** three optional feedback boxes (anything unclear, what would make the explanations better, anything else). The attention check is part of LimeSurvey, not of this page.
10. **End:** answers are sent to the Google Sheet

### The three situations

| Situation | Persona | What happens | Status light |
|---|---|---|---|
| TC1 | Alice | 12:08, rain. A meeting just ended, people are standing in the hallway. The door is closed (shown in the picture, not in the story). | orange |
| TC2 | Bob | 12:10, rain, lunchtime. A meeting just ended, people are standing in front of the meeting room. The door is closed (shown in the picture, not in the story). | orange |
| TC3 | Alice | 08:00, sunny. Alice is the first one in the office (so nobody is in the meeting room). The door is slightly open (shown in the picture, not in the story). | off |

### The explanations

Participants rate the explanations in random order (they only see "A", "B" and "C"):

- **C0:** the SmartEx baseline explanation (reworded for readability)
- **C2:** GPT-OSS + prompt P1 (zero-shot) + configuration C2 (LLM-weighted TOPSIS)
- **C3:** GPT-OSS + prompt P1 (zero-shot) + configuration C3 (LLM foil selection)

| `VARIANT` | Explanations per situation |
|---|---|
| `"C2_C3"` (default) | C0 + C2 + C3 (three) |
| `"C2"` | C0 + C2 (two) |

The same trial is used for every participant (only trials without hallucinations):

| Situation | C2 | C3 |
|---|---|---|
| TC1 | Trial 2 | Trial 1 |
| TC2 | Trial 2 | Trial 1 |
| TC3 | Trial 1 | Trial 3 |

The German explanations are DeepL translations of the English originals (with small corrections).

---

## Testing

| Mode | How | What happens |
|---|---|---|
| **Preview** | link with `?preview=1`, or `PREVIEW_MODE: true` | Click through freely: nothing is saved, no answers are required, the LimeSurvey note is skipped. A purple bar shows "Preview mode – nothing is saved" and a **"Jump to"** menu with every screen. |
| **Test mode** | `TEST_MODE: true` | Everything works as for real and **is saved** to the sheet. The end screen shows the collected data. **Set to `false` before the real study.** |

Tip: `?preview=1&lang=de` opens the preview in German. Always test in a **private window**, so no saved session is resumed.

---

## Files

| File | What it is |
|---|---|
| `index.html` | The complete study: design, texts, logic and saving |
| `README.md` | This file |

The Google Apps Script (`Code.gs`) lives in the Google Sheet under **Extensions → Apps Script**.

---

## How the answers are saved

```
Participant's browser  ──►  Google Apps Script (web app)  ──►  Google Sheet
     (index.html)             receives the answers             stores one row per person
```

- The page sends the answers to the web-app URL in `SAVE_URL`.
- A row is written **after each situation** and **updated at the end**.
- The Google Sheet has two tabs (names are set in `Code.gs`):
  - **Answers:** one row per participant, all values in columns
  - **Raw Data:** the complete raw data as JSON (backup)
- New columns are added automatically at the **right end** of the sheet.
- If a participant closes the tab, they can continue where they left off in the same browser.
- If sending fails at the end, a "Try again" button and a tip about Brave/ad blockers appear.

**After changing `Code.gs`:** Save → Deploy → **Manage deployments** → pencil icon → Version **"New version"** → Deploy. (Not "New deployment", which creates a new URL.)

### Bot protection and emergency stop

`Code.gs` protects the sheet against fake submissions sent directly to the web app:

- **Basic check:** submissions without a valid participant ID (`pid`), without the expected data, or larger than 300,000 characters are rejected.
- **Automatic stop:** if more than **30 new participants** arrive within one hour, the script stops accepting answers and sends an email to the Google account that owns the script (or to `ALERT_EMAIL`, if set).
- **By hand:** in Apps Script, run `pauseStudy` to stop accepting answers immediately, and `resumeStudy` to continue (this also resets the hourly counter). The web-app URL stays the same.
- While paused, participants still see the normal end screen, but their answers are not saved.
- **Full stop:** Deploy → Manage deployments → **Archive**. To resume, a new deployment (and a new `SAVE_URL` in `index.html`) is needed.
- **New participants in LimeSurvey:** deactivate the survey or set an end date.

### Hourly backup

`Code.gs` also makes an hourly copy of the whole sheet into the Google Drive folder **"SmartEx study backups"**. Backups older than 7 days are moved to the Drive trash.

- **Switch on (once):** in Apps Script, choose `startHourlyBackup` in the function menu → **Run** → allow access to Google Drive. It makes the first backup right away.
- **Switch off** (after data collection): run `stopHourlyBackup`.
- **Restore:** open the backup with the right time in the Drive folder and copy the rows you need. Alternatively, the sheet's own **File → Version history** also works.
- The backup does not change the web app, so **no new deployment** is needed for it.

To analyse in Excel: Google Sheet → **File → Download → Microsoft Excel (.xlsx)**.

### Important columns (tab "Answers")

| Column | Meaning |
|---|---|
| `pid` | anonymous participant ID |
| `ls_id`, `limesurvey_mode` | LimeSurvey response ID (empty in standalone mode) and whether LimeSurvey mode was on |
| `finished` | TRUE = completed the whole study |
| `order` | order of the situations, e.g. "TC2 TC1 TC3" |
| `age`, `smarthome_familiarity`, `tech_background` | only in standalone mode (in LimeSurvey mode, this is in LimeSurvey) |
| `quiz_correct` | correct answers in the quick check (0–3) |
| `feedback_unclear`, `feedback_improve`, `feedback_other` | the three optional feedback boxes |
| `TC1_expected_colour` | colour the participant expected instead (green, orange, blue, off) |
| `TC1_rank_locked` | the two rules placed, e.g. "notoccupied > rain" |
| `TC1_rank_first` | the rule placed first (the expected foil) |
| `TC1_rank_moves` | how often tiles were moved |
| `TC1_A_is`, `TC1_B_is`, `TC1_C_is` | which explanation was shown as A, B and C |
| `TC1_C2_trial`, `TC1_C3_trial` | GPT-OSS trials used (C3 empty in variant "C2") |
| `variant`, `model` | which variant was running, and the model (GPT-OSS P1) |
| `TC1_preferred` | explanation chosen as best for Alice/Bob: C0, C2 or C3 |
| `TC1_C0_underst`, `TC1_C0_helpful` … `TC1_C3_helpful` | ratings 1–5 (easy to understand for Alice/Bob, helpful for Alice/Bob), mapped to C0, C2 and C3 |
| `TC1_mcq_correct` | comprehension question correct (TRUE/FALSE) |
| `total_time_min` | total duration in minutes |

The same columns exist for TC2 and TC3.

**Rule IDs:** `notoccupied` = Meeting Room Not Occupied, `occupied` = Meeting Room Occupied, `rain` = Rain at Lunch, `sunny` = Sunny at Lunch, `danger` = Danger, `closing` = Closing Time.

---

## Quality and bot checks

The page measures the time on each screen and adds warning flags to every row. **Nobody is excluded automatically.**

| Column | Meaning |
|---|---|
| `time_<screen>_s` | seconds on each screen, e.g. `time_devices_s`, `time_TC1_rank_s`, `time_TC1_rate_s` |
| `TC1_rate_min_reading_s` | minimum time needed to read the explanations at `READING_WPM` |
| `TC1_straightlining` | TRUE = all 1–5 ratings in this situation have the same value (the length choice is not included) |
| `flag_too_fast` | whole study faster than `MIN_TOTAL_MINUTES`, or a rating page faster than its reading time |
| `flag_straightlining` | straightlining in at least one situation |
| `flag_no_pointer` | no mouse, touch or scroll activity at all |
| `flag_webdriver` | the browser reports that it is remote-controlled |
| `flag_honeypot` | an invisible field on "The smart office" page was filled in |
| `pointer_moves` | number of mouse/touch/scroll events |
| `bot_score` | number of flags that apply (0 = unremarkable) |

Decide before data collection which rule leads to exclusion (for example: attention check in LimeSurvey failed or `bot_score` ≥ 2) and report it in the method section.

---

## How to change things

All content is in clearly marked blocks at the top of the `<script>` part of `index.html`. Edit on GitHub: open `index.html` → **pencil icon** → change → **Commit changes**. The page updates after about 1 minute.

| Block | What you can change there |
|---|---|
| `SETTINGS` | all switches (see below) |
| `STATS` | how often each rule was fired / explained (only shown with `CONTEXT_MODE: "all"`) |
| `EXPLANATION_TRIALS` | which trials are recorded in the sheet |
| `RANK_PLACES` | how many rules participants place (currently 2) |
| `RULES` | rule names, "Starts when" / "Only if" texts, owners |
| `SCENARIOS` | stories, situation details, candidate rules, explanations, comprehension questions |
| `T` | every other text, in English (`en`) and German (`de`) |

### Settings

| Setting | Values | Meaning |
|---|---|---|
| `TEST_MODE` | `true` / `false` | shows the collected data at the end; **`false` for the real study** |
| `PREVIEW_MODE` | `true` / `false` | preview for everyone (nothing saved); usually use `?preview=1` instead |
| `SAVE_URL` | web-app URL | where answers are sent |
| `LIMESURVEY_MODE` | `true` / `false` | start via LimeSurvey (see above) |
| `LIMESURVEY_URL` | URL | LimeSurvey link shown when the page is opened without a code |
| `VARIANT` | `"C2_C3"` / `"C2"` | three or two explanations |
| `MIN_TOTAL_MINUTES` | number (5) | faster → `flag_too_fast` |
| `READING_WPM` | number (300) | reading speed for the rating-page check |
| `CONTEXT_MODE` | `"basic"` / `"all"` / `"split"` | rule context in the office note |
| `SURVEY_RETURN_URL` | URL or `""` | optional button on the end screen |

### Editing tips

- Only change text **inside the quotation marks** `"…"`. Keep every comma, quote mark and bracket.
- Quotation marks inside a text must be typographic („…“ or “…”), not plain `"`.
- Don't edit the file in TextEdit's formatted mode; use GitHub or a code editor.
- After every change, check it with the preview link.
- Avoid changing texts during data collection. If you have to, note the date.

---

## Before the real study (checklist)

- [ ] Google Sheet and Apps Script set up, web-app access **"Anyone"**, tab names in `Code.gs` match the sheet
- [ ] One complete test run (`TEST_MODE: true`), row appears in the sheet
- [ ] Decide: standalone or LimeSurvey mode, and set `LIMESURVEY_MODE`
- [ ] Test rows deleted from both tabs (keep the header row)
- [ ] `TEST_MODE` set to `false`
- [ ] Data protection and consent text checked with the supervisor
- [ ] Exclusion rule decided (attention check in LimeSurvey, `bot_score`)
- [ ] Pilot with 1–2 people, feedback included
- [ ] Link sent, with the note: laptop or PC, Chrome, Firefox, Safari or Edge (not Brave / ad blockers)

---

## Randomisation

The order of the three situations is **fully random** (all 6 orders possible).

Per participant, and saved with the answers:

- which explanation is shown as A, B and C
- the starting order of the rule tiles
- the answer order in the quick check and in the comprehension questions

---

## Data protection

- No names, e-mail addresses or IP addresses are collected by the page. Each participant gets a random ID.
- Answers are stored in a Google Sheet (Google servers). This must be mentioned in the consent text (in LimeSurvey or on the page).
- In LimeSurvey mode, part 1 runs on the University of Cologne's LimeSurvey server with anonymised responses.
- The page is hosted on GitHub Pages and loads its font from Google Fonts.

---

## Technical notes

- One self-contained HTML file: plain HTML, CSS and JavaScript, no build step.
- Works in current Chrome, Firefox, Safari and Edge, on laptops and phones.
- The office drawing is inline SVG, so no image files are needed.
- Progress is stored in `localStorage` and removed after the study is finished (not in preview mode).
