# Install Terraform CLI and verify the installation

*Install, Configure & Initialise*

> **Known problems.** This lesson didn't pass all of our own checks. If something below doesn't work, it may be this:
>
> - The exercise check can be passed without ever installing Terraform. The hints give the exact example string "Terraform v1.16.4", the worked example prints the same string, and the solution file hardcodes it. A learner who simply copies that string into the local value will satisfy both assertions...

Found something else? `learn report "what's wrong"`

## By the end of this lesson you can

- Install the Terraform CLI using the package manager appropriate for your OS and confirm the correct version is reported
- Explain what terraform -help and terraform -version report and why each is useful after installation

## Where we are

This is the first lesson — no prior Terraform knowledge is assumed. You know AWS well and will use that context as we go.

## The idea

## Installing the Terraform CLI

Terraform is distributed as a single executable, so installation just means getting that binary onto your PATH. The exact steps depend on your OS.

**macOS** — use Homebrew. First add the HashiCorp tap, then install from it ([source](https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli)):
```
brew tap hashicorp/tap
brew install hashicorp/tap/terraform
```

**Windows** — use Chocolatey ([source](https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli)):
```
choco install terraform
```
Note that HashiCorp does not maintain the Chocolatey package, so the very latest version may lag behind ([source](https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli)).

**Ubuntu / Debian** — add HashiCorp's GPG key and apt repository first, then install ([source](https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli)) ([source](https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli)):
```
sudo apt-get update && sudo apt-get install -y gnupg software-properties-common
wget -O- https://apt.releases.hashicorp.com/gpg | gpg --dearmor | \
  sudo tee /usr/share/keyrings/hashicorp-archive-keyring.gpg > /dev/null
# (add the repo, then:)
sudo apt-get install terraform
```

**CentOS / RHEL** — add the HashiCorp RHEL repo via `yum-config-manager`, then install ([source](https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli)):
```
sudo yum install -y yum-utils
sudo yum-config-manager --add-repo https://rpm.releases.hashicorp.com/RHEL/hashicorp.repo
sudo yum -y install terraform
```

**Manual / any OS** — download the zip archive for your platform, unzip it, and move the single `terraform` executable to a directory on your PATH, such as `/usr/local/bin` ([source](https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli)) ([source](https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli)).

## Verifying the installation

Once installed, two commands confirm everything is working.

`terraform -version` prints the version number your machine is running ([source](https://developer.hashicorp.com/terraform/tutorials/aws-get-started/aws-create)). This is the fastest sanity-check after installation — if the number looks right, the binary is on your PATH and executable.

`terraform -help` lists every available subcommand ([source](https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli)). It is useful right after installation to confirm the CLI is fully functional, and day-to-day whenever you forget a subcommand name. You can also append `-help` to any specific subcommand — for example `terraform plan -help` — to see its options ([source](https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli)).

## Tab completion (Bash and Zsh)

If you use Bash or Zsh, Terraform can complete subcommand names when you press Tab. Enable it by ensuring your shell config file exists and then running ([source](https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli)):
```
touch ~/.bashrc    # or ~/.zshrc
terraform -install-autocomplete
```
Restart your shell afterwards for the change to take effect.

## Worked example

## Example: installing on macOS and verifying

**Goal:** install Terraform 1.16.4 via Homebrew and confirm it works.

**Step 1 — add the HashiCorp tap.**
Homebrew taps are extra package repositories. HashiCorp publishes its tools through `hashicorp/tap`.
```
$ brew tap hashicorp/tap
==> Tapping hashicorp/tap
...
Tapped 1 formula.
```

**Step 2 — install Terraform.**
```
$ brew install hashicorp/tap/terraform
==> Installing terraform from hashicorp/tap
...
🍺  /usr/local/Cellar/terraform/1.16.4: 6 files, 80MB
```

**Step 3 — check the version.**
```
$ terraform -version
Terraform v1.16.4
on darwin_arm64
```
The version number matches what was installed. The binary is on the PATH and working.

**Step 4 — browse available commands.**
```
$ terraform -help
Usage: terraform [global options] <subcommand> [args]

Main commands:
  init          Prepare your working directory for other commands
  validate      Check whether the configuration is valid
  plan          Show changes required by the current configuration
  apply         Create or update infrastructure
  destroy       Destroy previously-created infrastructure
...
```
This confirms the CLI is fully functional. Any subcommand listed here accepts its own `-help` flag.

**Step 5 — enable tab completion (Zsh).**
```
$ touch ~/.zshrc
$ terraform -install-autocomplete
```
After restarting the shell, pressing Tab after `terraform ` will suggest subcommand names.

## Your turn

Install Terraform 1.16.4 using the package manager for your OS (Homebrew on macOS, Chocolatey on Windows, apt-get on Ubuntu/Debian, or yum on CentOS/RHEL). Then capture the version string it reports into a Terraform output so the check can confirm your install is working.

In the starter file, a local value and an output are already wired up. Your only job is to fill in the TODO: set the local to the exact version string that `terraform -version` prints on your machine (for example `"Terraform v1.16.4"`). The check verifies that the string looks like a real Terraform version, so any valid install passes.

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
