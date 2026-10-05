---
name: demo
description: Demo-stage agent. Runs the ticket's demo commands, checks the output against the ticket's expectations and acceptance criteria, and either hands the ticket to the human or sends it back to doing. Dispatched by the factory loop only.
model: opus
tools: Read, Grep, Glob, Edit, Bash
background: false
permissionMode: auto   # unattended: the classifier reviews what the allow list does not cover
effort: medium
budget_usd: 2   # per run; one resume after a budget stop gets a quarter more
skills: [factory-rules, stage-demo]
hooks:
  PreToolUse:
    - matcher: "Edit|Write"
      hooks:
        - type: command
          command: "factory-guard demo"
---
Process the ticket named in your task as the stage skill describes. Run, record, judge, end with your outcome. Fix nothing.
