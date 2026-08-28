# Workspace Rules

## Git & PR Workflow
- Do not commit directly to the default/main branch unless explicitly instructed to do so.
- When changes are ready to submit, create a feature branch, commit and push to that branch, and open a Pull Request using `gh pr create`.
- Wait for PR approval before merging.
- Include the Google Antigravity co-author trailer on all commits:
  `Co-Authored-By: Google Antigravity <google-antigravity@users.noreply.github.com>`

## Enclosure & CAD Workflow
- Do NOT generate or update technical drawing sheets (`generate_technical_drawings.py` or `.png` blueprints) unless explicitly requested by the user.

## Subagent & Multi-Agent Naming
- Whenever invoking or spawning subagents, always assign a clear, domain-specific contextual `Role` (e.g., "Enclosure CAD Specialist", "Thermal Simulation Engineer", "Firmware Architect", "QA Tester") instead of generic names or numbered identifiers (e.g., "agy 1", "worker 1", "researcher").
