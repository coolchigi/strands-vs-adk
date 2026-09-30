# CLI Workflow and State

## Outcomes

- Read a terraform plan output and identify every symbol, count, and forced-replacement indicator
- Apply and destroy infrastructure against LocalStack using the standard interactive workflow
- Explain what terraform.tfstate contains and why Terraform cannot function without it
- Inspect and make safe modifications to state using terraform state subcommands
- Explain why local state is dangerous for teams and describe the remote-backend alternative

## Lessons

- [Read and interpret terraform plan output](u3-l1-read-and-interpret-terraform-plan-output/README.md)
- [Apply and destroy infrastructure](u3-l2-apply-and-destroy-infrastructure/README.md)
- [Understand the state file](u3-l3-understand-the-state-file/README.md)
- [Inspect and modify state with terraform state commands](u3-l4-inspect-and-modify-state-with-terraform-state-co/README.md)
- [Remote state: risks, backends, and locking](u3-l5-remote-state-risks-backends-and-locking/README.md)
- [Reinitialise after dependency changes](u3-l6-reinitialise-after-dependency-changes/README.md)

## Project

Using the configuration built in Unit 2, run the full workflow: terraform plan -out=tfplan (read and annotate the plan output), terraform apply tfplan (confirm state file is updated), terraform state list and terraform state show for two resources, terraform state rm one resource and observe the next plan, then terraform destroy. Write a short explanation of what the state file contains and why it must not be committed to version control.
