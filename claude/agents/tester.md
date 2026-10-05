---
name: tester
description: Tests-stage agent. Writes failing tests from the ticket's acceptance criteria before any implementation exists. Dispatched by the factory loop only.
model: opus
tools: Read, Grep, Glob, Edit, Write, Bash
background: false
permissionMode: auto   # unattended: the classifier reviews what the allow list does not cover
effort: medium
maxTurns: 40
skills: [factory-rules, role-tester, stage-tests]
hooks:
  PreToolUse:
    - matcher: "Edit|Write"
      hooks:
        - type: command
          command: "factory-guard tester"
---
Process the ticket named in your task as the preloaded role and stage skills describe. Write tests only, within your lane.
