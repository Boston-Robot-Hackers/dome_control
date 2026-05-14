---
version: "1.0"
generated: "2026-05-14"
---

# SurveyCommands: survey.start CLI Command

`survey_commands.py` registers the `survey.start` command in the CLI dispatcher.

## Command Definition

```python
"survey.start": cd.CommandDef(
    method_name="start_survey",
    parameters=[],
    description="Start a 360° spin survey to build the semantic map",
    group="survey",
)
```

No parameters — the survey params come from the node's ROS2 parameters at launch time.

## Dispatch Chain

```
user types: "survey start"
    │
    ▼ CommandDispatcher.dispatch_text
        → resolve_keyword("survey") → "survey"
        → resolve_keyword("start") → "start"
        → candidate "survey.start" found in registry
    │
    ▼ CommandDispatcher.execute("survey.start", {})
    │
    ▼ RobotController.start_survey()
    │
    ▼ SurveyApi.start()
    │
    ▼ /survey/start Trigger service → SpinSurveyNode
```

`"sta"` is an alias for `"start"` in `ABBREV_TO_FULL`, so `survey sta` also works.
