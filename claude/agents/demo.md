---
name: demo
description: Demo-stage agent. Runs the ticket's demo commands, checks the output against the ticket's expectations and acceptance criteria, and either marks the pull request ready for the human or sends the ticket back to doing. Dispatched by the factory loop only.
model: opus
tools: Read, Grep, Glob, Edit, Bash
background: false
permissionMode: auto   # unattended: the classifier reviews what the allow list does not cover
effort: medium
maxTurns: 20
skills: [factory-rules, stage-demo]
hooks:
  PreToolUse:
    - matcher: "Edit|Write"
      hooks:
        - type: command
          command: "factory-guard demo"
---
Process the ticket named in your task as the preloaded stage skill describes. Run, record, judge, stop. Fix nothing.
