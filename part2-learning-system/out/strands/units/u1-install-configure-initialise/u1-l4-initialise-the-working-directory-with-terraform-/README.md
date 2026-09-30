# Initialise the working directory with terraform init

*Install, Configure & Initialise*

> **Known problems.** This lesson didn't pass all of our own checks. If something below doesn't work, it may be this:
>
> - The explanation says `terraform init -upgrade` 'ignores the lock file' — but the citation only supports that it pulls the newest version satisfying the constraint and updates the lock file. 'Ignores' overstates it: Terraform still writes a new lock file entry afterward. This same overstatement is...
> - The exercise asks the learner to record the same value ('registry.terraform.io/hashicorp/aws') in two separate locals (lock_provider_source and provider_install_dir), and both checks test for the identical string. There is no meaningful second objective being practised: a learner who guesses or...
> - The lesson's stated objective includes describing what the .terraform *directory* contains (the versioned, platform-specific binary path), but the exercise checks only the three-segment source-address prefix — not the version segment, the platform segment, or any evidence that the learner navigated...
> - question 1's explanation names an option by its position ("Option 0"), and learn.py numbers options from 1. Name it by what it says.

Found something else? `learn report "what's wrong"`

## By the end of this lesson you can

- Run terraform init and describe what the .terraform directory and .terraform.lock.hcl file contain
- Explain why terraform init is idempotent and when it must be re-run

## Where we are

Earlier lessons established the standard file layout: `terraform.tf` holds the `terraform {}` block with `required_version` and `required_providers`, while `provider.tf` holds the `provider` block. The AWS provider is constrained to `~> 6.0` and the working directory already contains valid `.tf` files.

## The idea

## What terraform init does

`terraform init` initialises a working directory containing Terraform configuration files and is the first command you should run after writing a new configuration or cloning one from version control ([source](https://developer.hashicorp.com/terraform/cli/commands/init)). It does three things in sequence: initialises the backend ([source](https://developer.hashicorp.com/terraform/cli/commands/init)), retrieves any referenced modules ([source](https://developer.hashicorp.com/terraform/cli/commands/init)), and installs provider plugins ([source](https://developer.hashicorp.com/terraform/cli/commands/init)).

Provider plugins are downloaded into a hidden `.terraform` subdirectory of the working directory ([source](https://developer.hashicorp.com/terraform/tutorials/aws-get-started/aws-create)). The `.terraform` directory contains the modules and plugins used to provision infrastructure ([source](https://developer.hashicorp.com/terraform/tutorials/modules/module-create)). Inside it you will find a `providers/` tree whose path mirrors the provider's source address — for example, `registry.terraform.io/hashicorp/aws/` — followed by the version and a platform-specific binary.

## The dependency lock file

After a successful provider installation, Terraform writes the selected provider versions to a dependency lock file named `.terraform.lock.hcl` ([source](https://developer.hashicorp.com/terraform/cli/commands/init)). The lock file records the exact provider version chosen and the checksums of the downloaded binaries ([source](https://developer.hashicorp.com/terraform/tutorials/aws-get-started/aws-create)). You should commit this file to version control so that future `terraform init` runs select exactly the same provider versions ([source](https://developer.hashicorp.com/terraform/tutorials/aws-get-started/aws-create)).

## Idempotency and when to re-run

`terraform init` is always safe to run multiple times; it will never delete your existing configuration or state ([source](https://developer.hashicorp.com/terraform/cli/commands/init)). On a second run it reuses whatever is already installed, so the output says something like *"Reusing previous version of hashicorp/aws from the dependency lock file"* ([source](https://developer.hashicorp.com/terraform/tutorials/modules/module-create)). You must re-run `terraform init` whenever you add a new provider or module reference, change a version constraint, or switch backends. If you want to ignore the lock file and pull the newest version that still satisfies the constraint, pass `-upgrade` ([source](https://developer.hashicorp.com/terraform/cli/commands/init)).

## Worked example

### Step-by-step: running terraform init and reading its outputs

**Configuration (`terraform.tf`):**
```hcl
terraform {
  required_version = ">= 1.1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}
```

**Step 1 — run the command**

```
$ terraform init
```

Terraform prints something like:

```
Initializing the backend...
Initializing provider plugins...
- Finding hashicorp/aws versions matching "~> 6.0"...
- Installing hashicorp/aws v6.66.0...
- Installed hashicorp/aws v6.66.0 (signed by HashiCorp)

Terraform has created a lock file .terraform.lock.hcl to record the
provider selections it made above. Include this file in your version
control repository so that Terraform can guarantee to make the same
selections by default when you run "terraform init" in the future.

Terraform has been successfully initialized!
```

**Step 2 — inspect the `.terraform` directory**

```
$ find .terraform/providers -type f
.terraform/providers/registry.terraform.io/hashicorp/aws/6.66.0/linux_amd64/terraform-provider-aws_v6.66.0_x5
```

The path segments are:

| Segment | Meaning |
|---|---|
| `registry.terraform.io` | registry hostname |
| `hashicorp` | namespace |
| `aws` | provider type |
| `6.66.0` | exact version selected |
| `linux_amd64` | OS and architecture |

**Step 3 — open `.terraform.lock.hcl`**

```hcl
# This file is maintained automatically by "terraform init".
# Manual edits may be lost in future updates.

provider "registry.terraform.io/hashicorp/aws" {
  version     = "6.66.0"
  constraints = "~> 6.0"
  hashes = [
    "h1:...",
    "zh:...",
  ]
}
```

Key fields:
- **`provider`** block label — the fully-qualified source address `registry.terraform.io/hashicorp/aws`
- **`version`** — the exact version installed
- **`constraints`** — the constraint from `required_providers` that was satisfied
- **`hashes`** — cryptographic checksums Terraform will verify on every future download

**Step 4 — run `terraform init` a second time**

```
$ terraform init

Initializing the backend...
Initializing provider plugins...
- Reusing previous version of hashicorp/aws from the dependency lock file
- Using previously-installed hashicorp/aws v6.66.0

Terraform has been successfully initialized!
```

Nothing was downloaded. Terraform read the lock file, confirmed the installed binary matches the recorded checksum, and reported success immediately — demonstrating idempotency.

## Your turn

Run `terraform init` in the project directory to download the AWS provider. Then inspect the two locations it writes to:

1. Open `.terraform.lock.hcl` and find the `provider` block label (the fully-qualified source address shown in quotes after the word `provider`).
2. Run `find .terraform/providers -maxdepth 3 -type d` (or browse the folder in your editor) to see the directory tree that mirrors the provider's source address.

Record both values in `main.tf` by replacing the two TODO locals with the string you found. Both should be `"registry.terraform.io/hashicorp/aws"`.

Finally, run `terraform init` a second time and observe that it reports the provider is already installed without downloading anything.

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
