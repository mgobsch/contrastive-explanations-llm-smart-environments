# Config 2 — Few-Shot Examples (TC4, TC5, TC6)

Below are examples of correctly assigned TOPSIS weights for other scenarios.
Use them as a guide for weight reasoning and JSON format — do not copy their content
into your answer. Assign weights based only on the current scenario's context and candidate rules.

---

## Test Case 4  |  CC2  |  Bob  |  Ntch

**Input:**

```
── Scenario: Test Case 4 ─────────────────────────────────────────────────────────

EXPLAINEE
  ID:            2
  Name:          Bob
  Role:          COWORKER
  Technicality:  Ntch

WHAT HAPPENED  (Fact)
  An error prevented the action from completing.
  Rule "Meeting Room Occupied" triggered but the status light could not be reached.
  Outcome: The status light did not change. A device error prevented the action from completing.

ACTIVE RULES  (relevant to this scenario)
- name: "Meeting room occupied"
  ruleId: "2"
  ruleEntry:
    name: "Rule: Meeting Room Occupied"
    entity_id: "automation.rule_meeting_room_occupied"
    state: "null"
  triggers:
  - name: "Contact Sensor Meeting Room Opening"
    entity_id: "binary_sensor.lumi_lumi_sensor_magnet_aq2_opening_2"
    state: "off"
  conditions:
  - name: "Occupancy of meeting room"
    entity_id: "binary_sensor.lumi_lumi_sensor_motion_aq2_motion_2"
    state: "Detected"
  actions:
  - name: "Turn Meeting Room Status Light orange"
    entity_id: "light.meeting_room_status_light"
    state: "orange"
  ownerId: "1"
  ruleDescription: "Rule_2: turns the meeting room status light orange if the room is occupied"

- name: "Meeting room not occupied"
  ruleId: "1"
  ruleEntry:
    name: "Rule: Meeting Room Not Occupied"
    entity_id: "automation.rule_meeting_room_not_occupied"
    state: "null"
  triggers:
  - name: "Contact Sensor Meeting Room Opening"
    entity_id: "binary_sensor.lumi_lumi_sensor_magnet_aq2_opening_2"
    state: "on"
  conditions:
  - name: "No Motion in meeting room"
    entity_id: "binary_sensor.lumi_lumi_sensor_motion_aq2_motion_2"
    state: "clear"
  actions:
  - name: "Turn Meeting Room Status Light green"
    entity_id: "light.meeting_room_status_light"
    state: "green"
  ownerId: "1"
  ruleDescription: "Rule_1: turns the meeting room status light green if the room is not occupied"

ERROR DETAILS
  Name        : Incorrect installation error
  Device      : status light (light.meeting_room_status_light) — state: error
  Implication : Light is not connected correctly.
  Solution    : Check wiring and connection.

SYSTEM STATE  (at time of event)
  status_light        = error
  meeting_room_door   = closed
  meeting_room_motion = detected
  weather             = cloudy
  clock               = 09:31
  ventilation         = off
  robo_cleaner        = off
  robo_cleaner_sensor = docked
  temperature_sensor  = 22.8°C
  workday_sensor      = on
  desk_lamp           = on
  coffee_machine      = on
  co2_sensor          = 620 ppm
  office_window       = closed
  thermostat          = 21.5°C
  printer_sensor      = 78%
  front_door_lock     = unlocked
  hallway_motion      = detected
  blinds              = open
  desk_occupancy      = occupied

CANDIDATE RULES
  The following rules are the alternatives that could be compared to what happened.
  Each rule is shown in full, followed by its ranking attributes.

- name: "Meeting room occupied"
  ruleId: "2"
  ruleEntry:
    name: "Rule: Meeting Room Occupied"
    entity_id: "automation.rule_meeting_room_occupied"
    state: "null"
  triggers:
  - name: "Contact Sensor Meeting Room Opening"
    entity_id: "binary_sensor.lumi_lumi_sensor_magnet_aq2_opening_2"
    state: "off"
  conditions:
  - name: "Occupancy of meeting room"
    entity_id: "binary_sensor.lumi_lumi_sensor_motion_aq2_motion_2"
    state: "Detected"
  actions:
  - name: "Turn Meeting Room Status Light orange"
    entity_id: "light.meeting_room_status_light"
    state: "orange"
  ownerId: "1"
  ruleDescription: "Rule_2: turns the meeting room status light orange if the room is occupied"
  attributes:
    precondition_similarity: null
    ownership: null
    frequency: null
    occurrence: null

USER QUESTION
  "Why is the light off?"

──────────────────────────────────────────────────────────────────────────────
```

**Expected output:**

```json
{
  "Precondition_Similarity": 0.25,
  "Ownership": 0.25,
  "Frequency": 0.25,
  "Occurrence": 0.25,
  "Reasoning": "CC2 — an error blocked the action of a rule that had already triggered. Per the framework, CC2 skips the expectation measures and TOPSIS entirely: the foil is deterministically the last rule that fired on the device before the error occurred, not a rule selected by ranking. No precondition similarity, ownership, frequency, or occurrence scores are computed for this candidate, so the weights assigned here are equal and have no effect on the outcome — Meeting Room Occupied is the foil because it is the only candidate, not because it wins a weighted comparison."
}
```

---

## Test Case 5  |  CC1  |  Bob  |  Ntch

**Input:**

```
── Scenario: Test Case 5 ─────────────────────────────────────────────────────────

EXPLAINEE
  ID:            2
  Name:          Bob
  Role:          COWORKER
  Technicality:  Ntch

WHAT HAPPENED  (Fact)
  Rule "Ventilation On" fired.
  Outcome: The ventilation turned on.

ACTIVE RULES  (relevant to this scenario)
- name: "Ventilation on"
  ruleId: "7"
  ruleEntry:
    name: "Rule: Ventilation On"
    entity_id: "automation.rule_ventilation_on"
    state: "null"
  triggers:
  - name: "Temperature High"
    entity_id: "sensor.meeting_room_temperature"
    state: "26.5"
  conditions: []
  actions:
  - name: "Turn Ventilation Fan on"
    entity_id: "fan.meeting_room_ventilation"
    state: "on"
  ownerId: "2"
  ruleDescription: "Rule_7: Turns on ventilation if temperature > 26C"

- name: "Danger"
  ruleId: "5"
  ruleEntry:
    name: "Rule: Danger"
    entity_id: "automation.danger"
    state: "null"
  triggers:
  - name: "Smoke detected"
    entity_id: "binary_sensor.smoke_detector"
    state: "on"
  - name: "CO2 detected"
    entity_id: "binary_sensor.co2_detector"
    state: "on"
  - name: "Fire alarm"
    entity_id: "binary_sensor.fire_alarm"
    state: "on"
  conditions:
  - name: "Time between 8 am and 6 pm"
    entity_id: "sensor.worldclock_sensor"
    state: "08:00-18:00"
  actions:
  - name: "Turn Meeting Room Status Light orange"
    entity_id: "light.meeting_room_status_light"
    state: "orange"
  - name: "Turn Ventilation Fan high"
    entity_id: "fan.meeting_room_ventilation"
    state: "high"
  ownerId: "1"
  ruleDescription: "Rule_5: turns the meeting room status light orange if danger occurs"

SYSTEM STATE  (at time of event)
  status_light        = green
  meeting_room_door   = closed
  meeting_room_motion = clear
  weather             = sunny
  clock               = 13:15
  ventilation         = on
  robo_cleaner        = off
  robo_cleaner_sensor = docked
  temperature_sensor  = 26.5°C
  workday_sensor      = on
  desk_lamp           = on
  coffee_machine      = off
  co2_sensor          = 550 ppm
  office_window       = open
  thermostat          = 24.0°C
  printer_sensor      = 70%
  front_door_lock     = unlocked
  hallway_motion      = detected
  blinds              = closed
  desk_occupancy      = occupied
  smoke_detector      = off
  co2_detector        = off
  fire_alarm          = off

CANDIDATE RULES
  The following rules are the alternatives that could be compared to what happened.
  Each rule is shown in full, followed by its ranking attributes.

- name: "Danger"
  ruleId: "5"
  ruleEntry:
    name: "Rule: Danger"
    entity_id: "automation.danger"
    state: "null"
  triggers:
  - name: "Smoke detected"
    entity_id: "binary_sensor.smoke_detector"
    state: "on"
  - name: "CO2 detected"
    entity_id: "binary_sensor.co2_detector"
    state: "on"
  - name: "Fire alarm"
    entity_id: "binary_sensor.fire_alarm"
    state: "on"
  conditions:
  - name: "Time between 8 am and 6 pm"
    entity_id: "sensor.worldclock_sensor"
    state: "08:00-18:00"
  actions:
  - name: "Turn Meeting Room Status Light orange"
    entity_id: "light.meeting_room_status_light"
    state: "orange"
  - name: "Turn Ventilation Fan high"
    entity_id: "fan.meeting_room_ventilation"
    state: "high"
  ownerId: "1"
  ruleDescription: "Rule_5: turns the meeting room status light orange if danger occurs"
  attributes:
    precondition_similarity: 0.0
    ownership: 0
    frequency: 1
    occurrence: 0

USER QUESTION
  "Why did the ventilation turn on — was there a danger alert?"

──────────────────────────────────────────────────────────────────────────────
```

**Expected output:**

```json
{
  "Precondition_Similarity": 0.30,
  "Ownership": 0.15,
  "Frequency": 0.15,
  "Occurrence": 0.40,
  "Reasoning": "CC1 with a single candidate — TOPSIS yields an undefined (NaN) score since there is no contrast to compute. Danger was nominated as the foil based on Bob's explicit question about a danger alert. Occurrence is weighted highest to reflect that the most meaningful discriminator in CC1 is usually how often the user has personally experienced a candidate rule; here it is 0, but in a richer candidate set it would identify Bob's most familiar alternatives. Precondition similarity is moderate: it would normally identify which alternative rule's conditions most closely match the current state, but Danger's triggers (smoke, CO2, fire alarm) were all inactive (prec_sim = 0.0). Ownership and frequency are down-weighted — Bob does not own Danger and it fires very rarely (freq = 1). The foil selection reflects Bob's explicitly expressed concern, not TOPSIS discrimination."
}
```

---

## Test Case 6  |  CC3  |  Hanna  |  Med

**Input:**

```
── Scenario: Test Case 6 ─────────────────────────────────────────────────────────

EXPLAINEE
  ID:            3
  Name:          Hanna
  Role:          COWORKER
  Technicality:  Med

WHAT HAPPENED  (Fact)
  No rule fired.
  Outcome: No automation rule fired. The robo cleaner did not start.

ACTIVE RULES  (relevant to this scenario)
- name: "Clean Office Overnight"
  ruleId: "8"
  ruleEntry:
    name: "Rule: Clean Office Overnight"
    entity_id: "automation.rule_clean_office"
    state: "null"
  triggers:
  - name: "Robo Cleaner Docked"
    entity_id: "binary_sensor.robo_cleaner_docked"
    state: "on"
  conditions:
  - name: "Time is Night"
    entity_id: "sensor.worldclock_sensor"
    state: "02:00-04:00"
  - name: "Day is Weekday"
    entity_id: "binary_sensor.workday_sensor"
    state: "on"
  actions:
  - name: "Start Cleaning"
    entity_id: "switch.robo_cleaner_switch"
    state: "on"
  ownerId: "3"
  ruleDescription: "Rule_8: Starts cleaning if robot is docked at night on a weekday"

SYSTEM STATE  (at time of event)
  status_light        = off
  meeting_room_door   = closed
  meeting_room_motion = clear
  weather             = cloudy
  clock               = 07:30
  ventilation         = off
  robo_cleaner        = off
  robo_cleaner_sensor = off
  temperature_sensor  = 19.5°C
  workday_sensor      = on
  desk_lamp           = off
  coffee_machine      = off
  co2_sensor          = 400 ppm
  office_window       = closed
  thermostat          = 19.0°C
  printer_sensor      = 88%
  front_door_lock     = locked
  hallway_motion      = clear
  blinds              = closed
  desk_occupancy      = clear

CANDIDATE RULES
  The following rules are the alternatives that could be compared to what happened.
  Each rule is shown in full, followed by its ranking attributes.

- name: "Clean Office Overnight"
  ruleId: "8"
  ruleEntry:
    name: "Rule: Clean Office Overnight"
    entity_id: "automation.rule_clean_office"
    state: "null"
  triggers:
  - name: "Robo Cleaner Docked"
    entity_id: "binary_sensor.robo_cleaner_docked"
    state: "on"
  conditions:
  - name: "Time is Night"
    entity_id: "sensor.worldclock_sensor"
    state: "02:00-04:00"
  - name: "Day is Weekday"
    entity_id: "binary_sensor.workday_sensor"
    state: "on"
  actions:
  - name: "Start Cleaning"
    entity_id: "switch.robo_cleaner_switch"
    state: "on"
  ownerId: "3"
  ruleDescription: "Rule_8: Starts cleaning if robot is docked at night on a weekday"
  attributes:
    ownership: 1
    frequency: 64
    occurrence: 3

USER QUESTION
  "Why didn't the robo cleaner start last night?"

──────────────────────────────────────────────────────────────────────────────
```

**Expected output:**

```json
{
  "Precondition_Similarity": 0.00,
  "Ownership": 0.25,
  "Frequency": 0.40,
  "Occurrence": 0.35,
  "Reasoning": "CC3 — no rule fired, so precondition similarity cannot be computed and its weight is set to 0.0, with its share redistributed to the remaining attributes. With only one candidate (Clean Office Overnight), TOPSIS cannot discriminate and yields an undefined score. Ownership is weighted highest because Hanna set up this rule herself (ownership = 1) — it is her own routine that she expects to run, so personal ownership is the strongest signal of expectation here. Occurrence is weighted strongly as it confirms Hanna's familiarity: the rule has appeared in her context 3 times (occ = 3), reinforcing that she has personally witnessed it run before. Frequency is moderate: with 88 executions the rule is a reliable nightly routine, but it is less informative than ownership and occurrence in identifying Hanna's specific expectation."
}
```
