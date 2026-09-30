# State Inspection, Management, and Refactoring

## Outcomes

- Inspect state snapshots and query outputs using terraform show and terraform output
- Refactor resource addresses and state bindings using terraform state mv and moved blocks
- Force resource recreations and handle state updates safely without configuration drift

## Lessons

- [Inspecting State and Output Extraction](u4-l1-inspecting-state-and-output-extraction/README.md)
- [Modifying State Bindings and Refactoring Resources](u4-l2-modifying-state-bindings-and-refactoring-resourc/README.md)

## Project

Perform a zero-downtime state migration on the multi-module AWS stack. Use `terraform state list` to catalog current addresses. Move a standalone S3 storage resource into the child module `module.storage` using `terraform state mv`, verifying state backups are created automatically. Run `terraform plan` to confirm zero resources will be destroyed or recreated, and extract the final state snapshot using `terraform show -json`.
