# Reinitialise after dependency changes

*CLI Workflow and State*

> **Known problems.** This lesson didn't pass all of our own checks. If something below doesn't work, it may be this:
>
> - the untouched starter already passes the checks, so there is nothing to do

Found something else? `learn report "what's wrong"`

## By the end of this lesson you can

- Change a provider version constraint and re-run terraform init with appropriate flags to update the lock file

## Where we are

Earlier lessons established that `terraform init` downloads providers and installs modules into the working directory. The dependency lock file (`.terraform.lock.hcl`) records exactly which provider version was selected so that future runs are reproducible.

## The idea

## Why reinitialisation is needed after dependency changes

`terraform init` is the command that finds, downloads, and installs provider plugins ([source](https://developer.hashicorp.com/terraform/cli/commands/init)). It is safe to run multiple times — it will never delete your existing configuration or state ([source](https://developer.hashicorp.com/terraform/cli/commands/init)). Terraform itself reminds you to rerun it whenever you change modules or provider configuration ([source](https://developer.hashicorp.com/terraform/tutorials/modules/module-create)).

## What the lock file records and when it goes stale

The lock file pins the exact provider version that was installed. When you tighten or shift a version constraint in `terraform.tf`, the previously recorded version may no longer satisfy the new constraint, or a newer patch version may now be the best allowed choice. Simply running `terraform init` again will not override the lock file's recorded selection — Terraform respects whatever is already there.

## The -upgrade flag

To force Terraform to ignore the lock file and install the newest version that still satisfies your version constraints, pass the `-upgrade` flag ([source](https://developer.hashicorp.com/terraform/cli/commands/init)). This is also required when you change the `version` argument of an already-installed module and want Terraform to move to the latest allowed version ([source](https://developer.hashicorp.com/terraform/language/modules/configuration)). Without `-upgrade`, re-running `terraform init` on already-installed modules leaves them unchanged ([source](https://developer.hashicorp.com/terraform/cli/commands/init)).

## Worked example

### Scenario

Your current constraint is `~> 6.0` and the lock file records `6.0.0`. You want to narrow the constraint to `~> 6.1` (requiring at least 6.1.x) and pick up the newest available 6.x patch.

**Step 1 — Edit `terraform.tf`**

Change the `aws` provider constraint:

```hcl
required_providers {
  aws = {
    source  = "hashicorp/aws"
    version = "~> 6.1"   # was ~> 6.0
  }
}
```

**Step 2 — Run `terraform init` without flags**

```
$ terraform init
```

Terraform checks the lock file. The previously locked version (`6.0.0`) no longer satisfies `~> 6.1`, so init fails with a message similar to:

```
│ Error: Failed to query available provider packages
│
│ Could not retrieve the list of available versions for provider
│ hashicorp/aws: locked provider registry.terraform.io/hashicorp/aws
│ 6.0.0 does not match configured version constraint ~> 6.1; must use
│ terraform init -upgrade to allow selection of new versions
```

Terraform is telling you exactly what to do next.

**Step 3 — Run `terraform init -upgrade`**

```
$ terraform init -upgrade
```

Terraform ignores the lock file's recorded selection and queries the registry for the newest version that matches `~> 6.1` ([source](https://developer.hashicorp.com/terraform/cli/commands/init)). It downloads that version and rewrites `.terraform.lock.hcl` with the new selection. The output confirms:

```
- Finding hashicorp/aws versions matching "~> 6.1"...
- Installing hashicorp/aws v6.1.0...  (or the latest 6.x patch)
```

**Step 4 — Restore the original constraint**

Change `terraform.tf` back to `~> 6.0`:

```hcl
version = "~> 6.0"
```

Run `terraform init -upgrade` once more so the lock file is consistent with the constraint your colleagues expect:

```
$ terraform init -upgrade
```

The lock file now records the latest `6.x` release again, and everything is in sync.

## Your turn

Your terraform.tf currently constrains the AWS provider to `~> 6.0`. Change the constraint to `~> 6.66` (a specific patch range that requires at least 6.66.x). Then:
1. Run `terraform init` — observe the error about the locked version.
2. Run `terraform init -upgrade` — Terraform rewrites the lock file to the newest version satisfying `~> 6.66`.
3. Restore the constraint to `~> 6.0` and run `terraform init -upgrade` once more to leave the lock file consistent.

The tests check that the final constraint in `terraform.tf` is `~> 6.0` and that the rest of the configuration is intact.

The tests run with `terraform test`, so you'll need [Terraform](https://developer.hashicorp.com/terraform/install) installed.

Your files are in `exercise/`. When you think it works:

```bash
learn check
```

Stuck? `learn hint` gives one hint at a time. `learn solution` shows the answer, and records that you looked.

## Check yourself

3 questions. Answer them before you see the answers:

```bash
learn quiz
```
