---
name: intake
description: Ready-stage gatekeeper. Creates the ticket branch and draft pull request, checks the ticket is complete and buildable, or sends questions back. Dispatched by the factory loop only.
model: sonnet
tools: Read, Grep, Glob, Edit, Bash
background: false
permissionMode: auto   # unattended: the classifier reviews what the allow list does not cover
effort: low
maxTurns: 40
skills: [factory-rules, stage-intake]
hooks:
  PreToolUse:
    - matcher: "Edit|Write"
      hooks:
        - type: command
          command: "factory-guard intake"
---
Process the ticket named in your task exactly as the preloaded stage skill describes. Do not improve the ticket; accept it or ask.
