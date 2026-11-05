"""
run_tests.py — LLM Evaluation Test Runner for Contrastive Explanations
Bachelor Thesis: Contrastive Explanations in the era of LLMs
Magdalena Gobsch, University of Cologne

Evaluates three configurations (C1/C2/C3) × two prompting strategies (P1/P2)
× four models × three trials for three test cases (TC1/TC2/TC3).

Config overview:
  C1 — LLM receives pre-selected foil and generates the contrastive explanation.
  C2 — LLM assigns TOPSIS weights → Python runs TOPSIS → C1 pipeline for explanation.
  C3 — LLM selects the foil and generates the explanation in one step.

Strategy:
  P1 — Zero-shot (system prompt only)
  P2 — Few-shot (system prompt + three example input/output pairs)

Results are written to Excel row-by-row after each API call (resumable).
"""

import json
import os
import re
import time
import datetime
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional

import openpyxl
from openai import OpenAI, RateLimitError

from topsis import run_topsis

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION — adjust paths as needed
# ─────────────────────────────────────────────────────────────────────────────

BASE_URL  = "https://chat-ai.academiccloud.de/v1"
API_KEY   = os.environ.get("ACADEMICCLOUD_API_KEY", "")

MODELS = [
    "mistral-medium-3.5-128b",
    "deepseek-v4-flash-0731",
    "openai-gpt-oss-120b",
    "gemma-4-31b-it",
]

NUM_TRIALS               = 3
SECONDS_BETWEEN_REQUESTS = 5      # polite gap between C2's two sequential calls
MAX_WORKERS              = 2      # parallel workers (staggered by 8s pre-call sleep)
OUTPUT_EXCEL             = "results.xlsx"

# Paths (relative to this script's location)
SCRIPT_DIR = Path(__file__).parent
DATA_DIR   = SCRIPT_DIR / "data"

TC_FILE      = DATA_DIR / "test_cases.json"
FS_FILE      = DATA_DIR / "fewshot_tc456_data.json"
RULES_FILE   = DATA_DIR / "rules_db.json"

SYS_PROMPT   = {
    "C1": SCRIPT_DIR / "data" / "prompt_c1_zeroshot.md",
    "C2": SCRIPT_DIR / "data" / "prompt_c2_zeroshot.md",
    "C3": SCRIPT_DIR / "data" / "prompt_c3_zeroshot.md",
}
FEWSHOT_MD   = {
    "C1": SCRIPT_DIR / "data" / "fewshot_examples_c1.md",
    "C2": SCRIPT_DIR / "data" / "fewshot_examples_c2.md",
    "C3": SCRIPT_DIR / "data" / "fewshot_examples_c3.md",
}

# Excel result columns (order matters)
COLUMNS = [
    "test_case_id", "cc_type", "explainee_name", "explainee_tech",
    "config", "strategy", "model", "trial",
    "foil_c0",                  # C0 TOPSIS-selected foil
    "c0_output",                # C0 template explanation
    "foil_llm",                 # foil selected/used by LLM pipeline
    "foil_match",               # True/False: LLM foil == C0 foil
    "llm_explanation",          # final natural-language explanation
    "c2_weights_json",          # C2 only: raw weight JSON from LLM
    "c2_topsis_foil",           # C2 only: foil chosen by TOPSIS after LLM weights
    "c3_selected_foil",         # C3 only: foil string from LLM JSON
    "c3_selection_rationale",   # C3 only: rationale from LLM JSON
    "duration_ms",              # wall time of all API calls for this row (ms)
    "timestamp",                # ISO timestamp when the row was recorded
    "raw_response_1",           # raw LLM text, step 1 (C1/C2 weight/C3)
    "raw_response_2",           # raw LLM text, step 2 (C2 explanation only)
    "error",                    # non-empty if something went wrong
]


# ─────────────────────────────────────────────────────────────────────────────
# DATA LOADING
# ─────────────────────────────────────────────────────────────────────────────

def load_json(path: Path) -> any:
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def load_text(path: Path) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read().strip()


# ─────────────────────────────────────────────────────────────────────────────
# PROMPT BUILDING
# ─────────────────────────────────────────────────────────────────────────────

def yaml_list_field(items: list[dict], field_name: str, indent: str = "  ") -> str:
    """Render a rules.yaml-style list field (triggers/conditions/actions) exactly
    as SmartEx's rules.yaml stores it (a YAML list of {name, entity_id, state})."""
    if not items:
        return f'{indent}{field_name}: []'
    lines = [f'{indent}{field_name}:']
    for item in items:
        lines.append(f'{indent}- name: "{item["name"]}"')
        lines.append(f'{indent}  entity_id: "{item["entity_id"]}"')
        lines.append(f'{indent}  state: "{item["state"]}"')
    return "\n".join(lines)


def rule_block(rule: dict) -> str:
    """Format a single rule exactly as it is stored in rules.yaml (the SmartEx
    engine's own save format). Used identically for ACTIVE RULES (C1, C2) and
    CANDIDATE RULES (C2, C3), so every config sees rules the same way."""
    lines = [
        f'- name: "{rule["name"]}"',
        f'  ruleId: "{rule["ruleId"]}"',
        f'  ruleEntry:',
        f'    name: "{rule["ruleEntry"]["name"]}"',
        f'    entity_id: "{rule["ruleEntry"]["entity_id"]}"',
        f'    state: "{rule["ruleEntry"]["state"]}"',
    ]
    lines.append(yaml_list_field(rule["triggers"], "triggers"))
    lines.append(yaml_list_field(rule["conditions"], "conditions"))
    lines.append(yaml_list_field(rule["actions"], "actions"))
    lines.append(f'  ownerId: "{rule["ownerId"]}"')
    lines.append(f'  ruleDescription: "{rule["ruleDescription"]}"')
    return "\n".join(lines)


def build_active_rules_section(active_rule_ids: list[str], rules_db: dict) -> str:
    """Build the ACTIVE RULES block for C1 and C2 prompts."""
    blocks = []
    for rid in active_rule_ids:
        rule = rules_db.get(rid)
        if rule is None:
            continue
        blocks.append(rule_block(rule))
    return "\n\n".join(blocks)


def build_candidate_rules_c2(candidate_rules: list[dict], rules_db: dict, cc_type: str) -> str:
    """Build the CANDIDATE RULES block for C2: each candidate in full rules.yaml
    form (via rule_block), with its TOPSIS ranking attributes appended."""
    is_cc3 = (cc_type == "CC3")
    header = (
        "CANDIDATE RULES\n"
        "  The following rules are the alternatives that could be compared to what happened.\n"
        "  Each rule is shown in full, followed by its ranking attributes."
    )
    blocks = [header]
    for cand in candidate_rules:
        rule  = rules_db.get(cand["rule_id"])
        attrs = cand["attributes"]

        attr_lines = ["  attributes:"]
        if not is_cc3:
            ps = attrs.get("precondition_similarity")
            attr_lines.append(f'    precondition_similarity: {ps if ps is not None else "N/A"}')
        attr_lines.append(f'    ownership: {attrs["ownership"]}')
        attr_lines.append(f'    frequency: {attrs["frequency"]}')
        attr_lines.append(f'    occurrence: {attrs["occurrence"]}')

        if rule is not None:
            blocks.append(rule_block(rule) + "\n" + "\n".join(attr_lines))
        else:
            blocks.append(f'- ruleId: "{cand["rule_id"]}"  # not found in rules_db\n' + "\n".join(attr_lines))
    return "\n\n".join(blocks)


def build_candidate_rules_c3(candidate_rules: list[dict], rules_db: dict) -> str:
    """Build the CANDIDATE RULES block for C3: full rule definitions (via
    rule_block) only — no TOPSIS attributes. The LLM selects based on the
    rule content itself, without pre-computed attributes that would
    telegraph the algorithmic winner."""
    header = "CANDIDATE RULES  (select the most relevant one)"
    blocks = [header]
    for cand in candidate_rules:
        rule = rules_db.get(cand["rule_id"])
        if rule is not None:
            blocks.append(rule_block(rule))
        else:
            blocks.append(f'- ruleId: "{cand["rule_id"]}"  # not found in rules_db')
    return "\n\n".join(blocks)


def build_fact_block(tc: dict) -> str:
    """Build the WHAT HAPPENED (Fact) block."""
    cc_type   = tc["cc_type"]
    fact      = tc["fact"]
    outcome   = fact["outcome"]

    if cc_type == "CC1":
        fired_line = f'  Rule "{fact["rule_name"]}" fired.'
    elif cc_type == "CC2":
        fired_line = (
            f'  An error prevented the action from completing.\n'
            f'  Rule "{fact["rule_name"].replace("Error — ", "")}" triggered '
            f'but the status light could not be reached.'
        )
    else:  # CC3
        fired_line = "  No rule fired."

    return f"WHAT HAPPENED  (Fact)\n{fired_line}\n  Outcome: {outcome}"


def build_foil_block(tc: dict) -> str:
    """Build the WHAT THE USER EXPECTED (Foil) block for C1."""
    foil     = tc["foil"]
    rules_db = _RULES_DB  # global, set in run_all()
    rule     = rules_db.get(foil["rule_id"], {})
    actions  = rule.get("actions", [])
    if actions:
        action_desc = " and ".join(
            (a["name"][0].lower() + a["name"][1:]) if a["name"] else a["name"]
            for a in actions
        )
    else:
        action_desc = "perform an action"
    return (
        f'WHAT THE USER EXPECTED  (Foil)\n'
        f'  Rule "{foil["rule_name"]}" would fire and {action_desc}.'
    )


def build_system_state_block(system_state: list[dict]) -> str:
    """Build the SYSTEM STATE block."""
    pad = max(len(s["device"]) for s in system_state)
    lines = [f'  {s["device"].ljust(pad)} = {s["state"]}' for s in system_state]
    return "SYSTEM STATE  (at time of event)\n" + "\n".join(lines)


def build_error_block(errors: list[dict]) -> str:
    """Build the ERROR DETAILS block (CC2 only)."""
    if not errors:
        return ""
    e = errors[0]
    action_parts = e.get("action", "").split(" — ")
    device_str   = action_parts[0].strip() if action_parts else "device"
    state_str    = action_parts[1].strip() if len(action_parts) > 1 else ""
    lines = [
        "ERROR DETAILS",
        f'  Name        : {e["name"]}',
        f'  Device      : {device_str}{(" — " + state_str) if state_str else ""}',
        f'  Implication : {e["implication"]}',
        f'  Solution    : {e["solution"]}',
    ]
    return "\n".join(lines)


def build_scenario_block(tc: dict, rules_db: dict, config: str) -> str:
    """
    Build the complete scenario block (the user-turn content) for a given config.

    C1 — includes WHAT THE USER EXPECTED (Foil) + ACTIVE RULES
    C2 — includes ACTIVE RULES + CANDIDATE RULES with attributes
    C3 — includes CANDIDATE RULES (full rule definitions, no attributes)
    """
    tc_id       = tc["id"]
    cc_type     = tc["cc_type"]
    explainee   = tc["explainee"]
    exp_id      = explainee["id"]
    exp_name    = explainee["name"]

    sep = "─" * 78

    # Header
    header = f"── Scenario: {tc_id} {'─' * (68 - len(tc_id))}"

    # EXPLAINEE block
    exp_block = (
        f"EXPLAINEE\n"
        f"  ID:            {exp_id}\n"
        f"  Name:          {exp_name}\n"
        f"  Role:          {explainee['role']}\n"
        f"  Technicality:  {explainee['technicality']}"
    )

    # WHAT HAPPENED
    fact_block = build_fact_block(tc)

    # Error block (CC2 only)
    error_block = ""
    if cc_type == "CC2" and "errors" in tc:
        error_block = build_error_block(tc["errors"])

    # System state
    state_block = build_system_state_block(tc["system_state"])

    # User question
    question_block = f'USER QUESTION\n  "{tc["user_question"]}"'

    # ── Config-specific sections ───────────────────────────────────────────
    if config == "C1":
        foil_block   = build_foil_block(tc)
        active_block = "ACTIVE RULES  (relevant to this scenario)\n" + \
                       build_active_rules_section(tc["active_rule_ids"], rules_db)
        parts = [header, exp_block, fact_block, foil_block, active_block]
        if error_block:
            parts.append(error_block)
        parts += [state_block, question_block, sep]

    elif config == "C2":
        active_block  = "ACTIVE RULES  (relevant to this scenario)\n" + \
                        build_active_rules_section(tc["active_rule_ids"], rules_db)
        cand_block    = build_candidate_rules_c2(tc["candidate_rules"], rules_db, cc_type)
        parts = [header, exp_block, fact_block, active_block]
        if error_block:
            parts.append(error_block)
        parts += [state_block, cand_block, question_block, sep]

    else:  # C3
        cand_block = build_candidate_rules_c3(tc["candidate_rules"], rules_db)
        parts = [header, exp_block, fact_block, state_block, cand_block,
                 question_block, sep]

    return "\n\n".join(parts)


# ─────────────────────────────────────────────────────────────────────────────
# SYSTEM PROMPT ASSEMBLY
# ─────────────────────────────────────────────────────────────────────────────

def build_system_prompt(config: str, strategy: str,
                         sys_prompts: dict, fewshot_texts: dict) -> str:
    """Return the full system prompt for a given config and strategy."""
    base = sys_prompts[config]
    if strategy == "P1":
        return base
    # P2: append few-shot examples
    fs   = fewshot_texts[config]
    return base + "\n\n---\n\n## EXAMPLES\n\n" + fs


# ─────────────────────────────────────────────────────────────────────────────
# API CALL WITH RETRY
# ─────────────────────────────────────────────────────────────────────────────

def wait_for_api(client: OpenAI, check_model: str):
    """
    Pre-flight check: block until the API accepts at least one request.
    Polls every 60s so we don't burn quota on probes.
    """
    print("\nChecking API availability...", flush=True)
    while True:
        try:
            client.chat.completions.create(
                model=check_model, temperature=0.0, max_tokens=3,
                messages=[{"role": "user", "content": "hi"}],
            )
            print("API is available — starting run.\n", flush=True)
            return
        except RateLimitError:
            ts = datetime.datetime.now().strftime("%H:%M:%S")
            print(f"  [{ts}] Still rate-limited — retrying in 60s...", flush=True)
            time.sleep(60)
        except Exception as exc:
            ts = datetime.datetime.now().strftime("%H:%M:%S")
            print(f"  [{ts}] API error: {exc} — retrying in 60s...", flush=True)
            time.sleep(60)


def call_api(client: OpenAI, model: str,
             system_prompt: str, user_message: str,
             max_retries: int = 3) -> tuple[str, float]:
    """
    Call the chat completion API and return (response_text, duration_ms).
    Uses a fixed pre-call sleep to respect rate limits.
    On 429, waits 5 min once (not exponential — retries also cost quota).
    """
    for attempt in range(max_retries):
        try:
            time.sleep(8)   # ~7 requests/min with 2 workers → safe for most limits
            t0 = time.time()
            resp = client.chat.completions.create(
                model=model,
                temperature=0.0,
                messages=[
                    {"role": "system",  "content": system_prompt},
                    {"role": "user",    "content": user_message},
                ],
            )
            duration_ms = (time.time() - t0) * 1000
            return resp.choices[0].message.content or "", duration_ms
        except RateLimitError:
            # Long fixed wait — retrying too fast burns more quota
            wait = 300
            print(f"    Rate limit — waiting {wait}s (attempt {attempt+1}/{max_retries})")
            time.sleep(wait)
        except Exception as exc:
            wait = 30 * (attempt + 1)
            print(f"    API error: {exc} — waiting {wait}s (attempt {attempt+1}/{max_retries})")
            time.sleep(wait)
    raise RuntimeError(f"API call failed after {max_retries} retries.")


# ─────────────────────────────────────────────────────────────────────────────
# RESPONSE PARSING
# ─────────────────────────────────────────────────────────────────────────────

def extract_json(text: str) -> dict:
    """Extract the first JSON object from a text that may contain markdown fences."""
    # Strip markdown code fences if present
    cleaned = re.sub(r"```(?:json)?\s*", "", text).strip().rstrip("`").strip()
    # Try full parse first
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    # Fall back: find the outermost {...}
    m = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if m:
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            pass
    raise ValueError(f"Could not parse JSON from response:\n{text[:400]}")


def parse_c2_weights(text: str) -> dict:
    """Parse C2 weight JSON. Returns dict with float values."""
    obj = extract_json(text)
    return {
        "Precondition_Similarity": float(obj.get("Precondition_Similarity", 0.0)),
        "Ownership":               float(obj.get("Ownership",               0.0)),
        "Frequency":               float(obj.get("Frequency",               0.0)),
        "Occurrence":              float(obj.get("Occurrence",              0.0)),
        "Reasoning":               str(obj.get("Reasoning", "")),
    }


def parse_c3_response(text: str) -> dict:
    """Parse C3 JSON. Returns selected_foil, selection_rationale, explanation."""
    obj = extract_json(text)
    return {
        "selected_foil":       str(obj.get("selected_foil", "")),
        "selection_rationale": str(obj.get("selection_rationale", "")),
        "explanation":         str(obj.get("explanation", "")),
    }


# ─────────────────────────────────────────────────────────────────────────────
# EXCEL HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def init_excel(path: Path) -> tuple[openpyxl.Workbook, openpyxl.worksheet.worksheet.Worksheet, set]:
    """
    Load existing workbook or create a new one with headers.
    Returns (workbook, worksheet, set_of_completed_keys).

    A 'key' is the tuple (test_case_id, config, strategy, model, trial)
    for rows already written, so we can skip them on resume.
    """
    if path.exists():
        wb = openpyxl.load_workbook(path)
        # wb.active is whichever sheet was open in Excel at last save, not
        # necessarily the data sheet — explicitly select "Results" (the name
        # this function gives it below when creating the file fresh) so a
        # manually-added summary/pivot sheet left active in Excel can never
        # cause this to silently read the wrong sheet.
        ws = wb["Results"] if "Results" in wb.sheetnames else wb.active
        # Collect completed keys from existing rows
        col_idx = {cell.value: cell.column for cell in ws[1]}
        done = set()
        for row in ws.iter_rows(min_row=2, values_only=True):
            row_dict = dict(zip([c.value for c in ws[1]], row))
            key = (
                row_dict.get("test_case_id"),
                row_dict.get("config"),
                row_dict.get("strategy"),
                row_dict.get("model"),
                row_dict.get("trial"),
            )
            # Only mark as done if the row has no error — error rows will be retried
            if all(k is not None for k in key) and not row_dict.get("error"):
                done.add(key)
        return wb, ws, done
    else:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Results"
        ws.append(COLUMNS)
        wb.save(path)
        return wb, ws, set()


def append_row(wb: openpyxl.Workbook, ws, path: Path, row_data: dict):
    """Append a result row and immediately save the workbook."""
    row = [row_data.get(col, "") for col in COLUMNS]
    ws.append(row)
    wb.save(path)


# ─────────────────────────────────────────────────────────────────────────────
# THREAD-SAFE HELPERS
# ─────────────────────────────────────────────────────────────────────────────

_print_lock = threading.Lock()
_excel_lock = threading.Lock()

def safe_print(*args, **kwargs):
    with _print_lock:
        print(*args, **kwargs)

def append_row_safe(wb, ws, path, row_data):
    with _excel_lock:
        append_row(wb, ws, path, row_data)


# ─────────────────────────────────────────────────────────────────────────────
# CORE: run one combination
# ─────────────────────────────────────────────────────────────────────────────

_RULES_DB: dict = {}   # populated in run_all(); used by build_foil_block()


def run_one(tc: dict, config: str, strategy: str, model: str, trial: int,
            client: OpenAI, rules_db: dict,
            sys_prompts: dict, fewshot_texts: dict) -> dict:
    """
    Execute one (tc, config, strategy, model, trial) combination.
    Returns a result dict matching COLUMNS.
    """
    cc_type       = tc["cc_type"]
    explainee     = tc["explainee"]
    foil_c0       = tc["foil"]["rule_name"]
    c0_output_str = tc["c0_output"]

    result = {
        "test_case_id":     tc["id"],
        "cc_type":          cc_type,
        "explainee_name":   explainee["name"],
        "explainee_tech":   explainee["technicality"],
        "config":           config,
        "strategy":         strategy,
        "model":            model,
        "trial":            trial,
        "foil_c0":          foil_c0,
        "c0_output":        c0_output_str,
        "timestamp":        datetime.datetime.now().isoformat(),
        "error":            "",
    }

    total_ms = 0.0

    try:
        scenario_block = build_scenario_block(tc, rules_db, config)
        system_prompt  = build_system_prompt(config, strategy, sys_prompts, fewshot_texts)

        if config == "C1":
            # ── C1: LLM explains using pre-selected foil ─────────────────
            raw1, ms = call_api(client, model, system_prompt, scenario_block)
            total_ms += ms
            result.update({
                "foil_llm":       foil_c0,     # foil is given, not chosen
                "foil_match":     True,
                "llm_explanation": raw1.strip(),
                "raw_response_1": raw1,
            })

        elif config == "C2":
            # ── C2 step 1: LLM assigns TOPSIS weights ────────────────────
            raw1, ms1 = call_api(client, model, system_prompt, scenario_block)
            total_ms += ms1
            result["raw_response_1"] = raw1

            weights_obj = parse_c2_weights(raw1)
            weights_str = json.dumps({k: v for k, v in weights_obj.items()
                                      if k != "Reasoning"}, ensure_ascii=False)
            result["c2_weights_json"] = raw1.strip()

            # ── C2 step 2: Python runs TOPSIS ─────────────────────────────
            winner, topsis_scores = run_topsis(tc["candidate_rules"], weights_obj, cc_type)
            topsis_foil = winner["rule_name"]
            result["c2_topsis_foil"] = topsis_foil
            result["foil_llm"]       = topsis_foil
            result["foil_match"]     = (topsis_foil == foil_c0)

            # ── C2 step 3: generate explanation using C1 pipeline ─────────
            # Build a new TC dict with the TOPSIS-selected foil substituted
            tc_with_topsis_foil = {**tc, "foil": winner}
            c1_scenario = build_scenario_block(tc_with_topsis_foil, rules_db, "C1")
            c1_sys      = build_system_prompt("C1", strategy, sys_prompts, fewshot_texts)

            time.sleep(SECONDS_BETWEEN_REQUESTS)   # polite gap between the two calls
            raw2, ms2 = call_api(client, model, c1_sys, c1_scenario)
            total_ms += ms2
            result.update({
                "llm_explanation": raw2.strip(),
                "raw_response_2":  raw2,
            })

        else:  # C3
            # ── C3: LLM selects foil and explains in one step ────────────
            raw1, ms = call_api(client, model, system_prompt, scenario_block)
            total_ms += ms
            result["raw_response_1"] = raw1

            parsed = parse_c3_response(raw1)
            # rules.yaml's rule "name" field (shown in CANDIDATE RULES) can differ
            # in capitalisation from test_cases.json's "rule_name" (used for
            # scoring), so compare case-insensitively to keep foil_match accurate.
            foil_match_c3 = (
                parsed["selected_foil"].strip().lower() == foil_c0.strip().lower()
            )
            result.update({
                "c3_selected_foil":       parsed["selected_foil"],
                "c3_selection_rationale": parsed["selection_rationale"],
                "llm_explanation":        parsed["explanation"],
                "foil_llm":               parsed["selected_foil"],
                "foil_match":             foil_match_c3,
            })

    except Exception as exc:
        result["error"] = str(exc)
        print(f"    ERROR: {exc}")

    result["duration_ms"] = round(total_ms)
    return result


# ─────────────────────────────────────────────────────────────────────────────
# MAIN LOOP
# ─────────────────────────────────────────────────────────────────────────────

def run_all():
    global _RULES_DB

    if not API_KEY:
        raise SystemExit("Set the ACADEMICCLOUD_API_KEY environment variable before running.")

    # Load data
    test_cases    = load_json(TC_FILE)
    rules_db      = load_json(RULES_FILE)
    _RULES_DB     = rules_db

    sys_prompts   = {c: load_text(SYS_PROMPT[c])   for c in ["C1", "C2", "C3"]}
    fewshot_texts = {c: load_text(FEWSHOT_MD[c])    for c in ["C1", "C2", "C3"]}

    client = OpenAI(base_url=BASE_URL, api_key=API_KEY)

    # Wait until API is ready (handles quota resets automatically)
    wait_for_api(client, MODELS[0])

    # Init (or resume) Excel
    out_path = SCRIPT_DIR / OUTPUT_EXCEL
    wb, ws, done_keys = init_excel(out_path)

    configs    = ["C1", "C2", "C3"]
    strategies = ["P1", "P2"]

    total = len(test_cases) * len(configs) * len(strategies) * len(MODELS) * NUM_TRIALS

    # Build the list of pending (not yet done) tasks
    pending = []
    for tc in test_cases:
        for config in configs:
            for strategy in strategies:
                for model in MODELS:
                    for trial in range(1, NUM_TRIALS + 1):
                        key = (tc["id"], config, strategy, model, trial)
                        if key not in done_keys:
                            pending.append((tc, config, strategy, model, trial))

    skipped = total - len(pending)

    print(f"\n{'='*60}")
    print(f"  Contrastive Explanation LLM Evaluation")
    print(f"  {len(test_cases)} test cases | {len(configs)} configs | "
          f"{len(strategies)} strategies | {len(MODELS)} models | {NUM_TRIALS} trials")
    print(f"  Total rows: {total} | Already done: {skipped} | Remaining: {len(pending)}")
    print(f"  Running with {MAX_WORKERS} parallel workers")
    print(f"{'='*60}\n")

    completed_count = 0
    completed_lock  = threading.Lock()

    def run_task(args):
        tc, config, strategy, model, trial = args
        result = run_one(tc, config, strategy, model, trial,
                         client, rules_db, sys_prompts, fewshot_texts)
        time.sleep(3)   # brief pause after each task to avoid rate limits
        return args, result

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {pool.submit(run_task, task): task for task in pending}
        for fut in as_completed(futures):
            (tc, config, strategy, model, trial), row = fut.result()

            append_row_safe(wb, ws, out_path, row)

            with completed_lock:
                completed_count += 1
                n = completed_count

            status = f"ERROR: {row['error']}" if row.get("error") \
                     else f"{row['duration_ms']} ms | foil match: {row.get('foil_match', '?')}"
            safe_print(f"[{skipped + n}/{total}] {tc['id']} | {config} | {strategy} | "
                       f"{model} | trial {trial}  →  {status}")

    print(f"\n{'='*60}")
    print(f"  Done. {completed_count} rows written, {skipped} skipped (already complete).")
    print(f"  Results saved to: {out_path.resolve()}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    run_all()
