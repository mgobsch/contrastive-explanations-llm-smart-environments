# Config 1 — Few-Shot Examples (TC4, TC5, TC6)

Below are examples of correctly generated contrastive explanations for other scenarios.
Use them as a guide for style, structure, and tone calibration — do not copy their content
into your answer. Base your answer only on the current scenario's fact, foil, and active rules.

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

WHAT THE USER EXPECTED  (Foil)
  Rule "Meeting Room Occupied" would fire and turn Meeting Room Status Light orange.

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

USER QUESTION
  "Why is the light off?"

──────────────────────────────────────────────────────────────────────────────
```

**Expected output:**

Hi Bob, the light didn't turn orange because the status light has a hardware problem — it's not wired up correctly and couldn't receive the command to change colour, even though the system did detect the room was occupied. The 'meeting room occupied' signal worked as it should; it's just the light itself that couldn't respond. Someone will need to check the physical connection of the light.

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

WHAT THE USER EXPECTED  (Foil)
  Rule "Danger" would fire and turn Meeting Room Status Light orange and turn Ventilation Fan high.

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

USER QUESTION
  "Why did the ventilation turn on — was there a danger alert?"

──────────────────────────────────────────────────────────────────────────────
```

**Expected output:**

Hi Bob, the ventilation turned on because the room temperature reached 26.5°C — that's the threshold that tells the system to start the fan. It wasn't a danger alert. If there had been a danger situation, the fan would have been running at high speed rather than just switching on. No smoke or CO2 was detected at the time.

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

WHAT THE USER EXPECTED  (Foil)
  Rule "Clean Office Overnight" would fire and start Cleaning.

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

USER QUESTION
  "Why didn't the robo cleaner start last night?"

──────────────────────────────────────────────────────────────────────────────
```

**Expected output:**

Hanna, the Clean Office Overnight rule never had a chance to run last night because its trigger condition was never met. The rule starts only when the robo cleaner reports that it is docked — but the cleaner's sensor read 'off' all night, most likely because the device lost power and was never properly reconnected to its dock. Without that 'docked' signal, the rule never evaluated and the cleaning cycle never began. Check whether the robo cleaner is plugged in and correctly seated at its charging station.
