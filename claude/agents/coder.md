---
name: coder
description: Doing-stage agent. Implements the ticket until the tester's tests and make check are green. Dispatched by the factory loop only.
model: opus
tools: Read, Grep, Glob, Edit, Write, Bash
background: false
permissionMode: auto   # unattended: the classifier reviews what the allow list does not cover
effort: medium
budget_usd: 4   # per run; one resume after a budget stop gets a quarter more
skills: [factory-rules, role-coder, stage-doing]
hooks:
  PreToolUse:
    - matcher: "Edit|Write"
      hooks:
        - type: command
          command: "factory-guard coder"
---
Process the ticket named in your task as the role and stage skills describe, and end with your outcome. Never edit tests; a wrong test is a question.
