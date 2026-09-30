# Sources

Every claim a lesson teaches, the words it rests on, and where they are.

## [https://developer.hashicorp.com/terraform/language/modules](https://developer.hashicorp.com/terraform/language/modules)

official, fetched 2026-09-28

- Every Terraform workspace has configuration files in its root directory, which Terraform calls the root module.  
  > Every Terraform workspace includes configuration files in its root directory. Terraform refers to this configuration as the root module.
- Modules configured using module blocks are called child modules, and when a configuration is applied, the root module calls the child module.  
  > Modules you configure using module blocks are called child modules. When you apply a configuration, the root module calls the child module.
- Terraform adds a child module's resources to the workspace and manages them as part of the configuration when the root module calls it.  
  > As a result, Terraform adds the child module's resources to your workspace and manages them as part of the configuration.
- The root module can be configured to call child modules multiple times within the same configuration.  
  > You can configure the root module to call child modules multiple times within the same configuration.
- Terraform can load modules from multiple sources, including the local file system, a Terraform registry, and VCS repositories.  
  > Terraform can load modules from multiple sources, including the local file system, a Terraform registry, and VCS repositories.
- Module consumers use the module block in their configurations to call modules from supported sources.  
  > Module consumers can use the module block in their configurations to call modules published to one of the supported kinds of sources.
- A module is a collection of resources that Terraform manages together, and reusable modules should be written when you repeatedly provision collections of resources with similar configuration.  
  > When you repeatedly provision collections of resources with similar configuration, such as networking resources for new development environments, you should write reusable modules to codify them.
- Modularizing and sharing configurations helps standardize infrastructure provisioning and enables quick, predictable resource provisioning.  
  > Modularizing and sharing configurations helps you standardize how you provision infrastructure and lets you quickly and predictably provision the resources you need.
- A root module can also call a child module that itself calls its own nested child module.  
  > The root module can also call a child module that calls its own nested child module.

## [https://developer.hashicorp.com/terraform/cli/run](https://developer.hashicorp.com/terraform/cli/run)

official, fetched 2026-09-28

- The three core CLI commands for basic provisioning tasks are terraform plan, terraform apply, and terraform destroy.  
  > the following commands provide basic provisioning tasks:
terraform plan
terraform apply
terraform destroy
- All three core provisioning commands require an initialized working directory.  
  > All of these commands require an initialized working directory, and all of them act
only upon the currently selected workspace.
- terraform plan determines the desired state of all declared resources, compares it to real infrastructure using state data, and checks current resource state via the provider's API.  
  > The terraform plan command evaluates a Terraform configuration to determine
the desired state of all the resources it declares, then compares that desired
state to the real infrastructure objects being managed with the current working
directory and workspace. It uses state data to determine which real objects
correspond to which declared resources, and checks the current state of each
resource using the relevant infrastructure provider's API.
- terraform plan does not make any actual changes to real infrastructure; it only presents a description of the changes needed to reach the desired state.  
  > It does not perform any actual changes to real
world infrastructure objects; it only presents a plan for making changes.
- terraform plan can save its output as a runnable artifact (plan file) that terraform apply can later use to carry out exactly those changes.  
  > terraform plan can also save its
plan as a runnable artifact, which terraform apply can use to carry out those
exact changes.
- terraform apply performs a plan and then actually carries out the planned changes to each resource using the provider's API.  
  > The terraform apply command performs a plan just like terraform plan does,
but then actually carries out the planned changes to each resource using the
relevant infrastructure provider's API.
- terraform apply asks for user confirmation before making any changes, unless explicitly told to skip approval.  
  > It asks for confirmation from the user
before making any changes, unless it was explicitly told to skip approval.
- By default, terraform apply performs a fresh plan immediately before applying changes and displays that plan to the user when asking for confirmation.  
  > By default, terraform apply performs a fresh plan right before applying
changes, and displays the plan to the user when asking for confirmation.
- terraform apply can accept a plan file produced by terraform plan instead of running a new plan, allowing exact pre-approved changes to be applied reliably even if configuration or infrastructure state has changed since the plan was created.  
  > it can also accept a plan file produced by terraform plan in lieu of
running a new plan. You can use this to reliably perform an exact set of
pre-approved changes, even if the configuration or the state of the real
infrastructure has changed in the minutes since the original plan was created.
- terraform destroy destroys all resources managed by the current working directory and workspace, using state data to identify which real-world objects correspond to managed resources.  
  > The terraform destroy command destroys all of the resources being managed by
the current working directory and workspace, using state data to determine which
real world objects correspond to managed resources.
- Like terraform apply, terraform destroy asks for confirmation before proceeding.  
  > Like terraform apply, it
asks for confirmation before proceeding.
- A terraform destroy behaves exactly like deleting every resource from the configuration and then running an apply, but does not require editing the configuration.  
  > A destroy behaves exactly like deleting every resource from the configuration
and then running an apply, except that it doesn't require editing the
configuration.
- Using terraform destroy is more convenient than manually removing resources from config when you intend to provision similar resources at a later date.  
  > This is more convenient if you intend to provision similar
resources at a later date.

## [https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli](https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli)

official, fetched 2026-09-28

- On macOS, Terraform can be installed via Homebrew by first tapping the HashiCorp tap and then installing from it.  
  > $ brew tap hashicorp/tap

Now, install Terraform from hashicorp/tap/terraform.

$ brew install hashicorp/tap/terraform
- On Windows, Terraform can be installed via the Chocolatey package manager using a single command.  
  > $ choco install terraform
- HashiCorp does not maintain the Chocolatey package for Terraform, so the latest version may not always be available through it.  
  > HashiCorp does not maintain Chocolatey or the Terraform package. The latest version of Terraform is always available for you to download and install manually.
- On Ubuntu/Debian, installing Terraform requires adding HashiCorp's GPG key and repository, then installing via apt-get.  
  > $ sudo apt-get update && sudo apt-get install -y gnupg software-properties-common

Install HashiCorp's GPG key.

$ wget -O- https://apt.releases.hashicorp.com/gpg | \
gpg --dearmor | \
sudo tee /usr/share/keyrings/hashicorp-archive-keyring.gpg > /dev/null
- The final step to install Terraform on Ubuntu/Debian after adding the repository is to run sudo apt-get install terraform.  
  > $ sudo apt-get install terraform
- On CentOS/RHEL, Terraform is installed by adding the HashiCorp RHEL repository via yum-config-manager and then installing with yum.  
  > $ sudo yum install -y yum-utils

Use yum-config-manager to add the official HashiCorp RHEL repository.

$ sudo yum-config-manager --add-repo https://rpm.releases.hashicorp.com/RHEL/hashicorp.repo

Install Terraform from the new repository.

$ sudo yum -y install terraform
- Terraform can be installed manually by downloading a pre-compiled zip archive for your system and unzipping it; it runs as a single executable named terraform.  
  > To install Terraform, download the appropriate zip archive for your system and unzip it.

Terraform runs as a single executable named terraform. Any other files in the archive can be safely removed and Terraform will still function.
- After a manual installation on macOS or Linux, the terraform executable must be moved to a directory on the system PATH, such as /usr/local/bin.  
  > $ mv ~/Downloads/terraform /usr/local/bin/
- Terraform can also be compiled from source by cloning the HashiCorp repository and running go install, which places the binary in $GOPATH/bin/terraform.  
  > $ git clone https://github.com/hashicorp/terraform

Navigate to the new directory.

$ cd terraform

Next, compile the binary. The following command compiles the binary and stores it in $GOPATH/bin/terraform.

$ go install
- After installation, you can verify Terraform is working by running terraform -help to list all available subcommands.  
  > $ terraform -help
Usage: terraform [global options] <subcommand> [args]

The available commands for execution are listed below.
- You can get help for any specific Terraform subcommand by appending -help to it.  
  > Add -help to any Terraform command to learn more about what it does and available options.

$ terraform plan -help
- Terraform supports tab completion for Bash and Zsh shells, enabled by running terraform -install-autocomplete after ensuring the shell config file exists.  
  > $ touch ~/.bashrc

$ touch ~/.zshrc

Then install the autocomplete package.

$ terraform -install-autocomplete
- HashiCorp maintains compatibility between Terraform versions, meaning a configuration written for one version should continue to work with any later minor version update.  
  > HashiCorp maintains compatibility between Terraform versions, so a Terraform configuration written for one version of Terraform should continue to work with any later minor version update.

## [https://developer.hashicorp.com/terraform/cli/commands/init](https://developer.hashicorp.com/terraform/cli/commands/init)

official, fetched 2026-09-28

- The terraform init command initializes a working directory containing Terraform configuration files and is the first command you should run after writing a new configuration or cloning one from version control.  
  > The terraform init command initializes a working directory containing Terraform configuration files. This is the first command you should run after writing a new Terraform configuration or cloning an existing configuration from version control.
- It is safe to run terraform init multiple times; it will never delete existing configuration or state.  
  > This command is always safe to run multiple times, to bring the working directory up to date with changes in the configuration. Though subsequent runs may give errors, this command will never delete your existing configuration or state.
- During init, Terraform searches the configuration for direct and indirect provider references and automatically finds, downloads, and installs the necessary provider plugins from the public Terraform Registry or a third-party registry.  
  > During init, Terraform searches the configuration for both direct and indirect references to providers and attempts to install the plugins for those providers. For providers that are published in either the public Terraform Registry or in a third-party provider registry, terraform init will automatically find, download, and install the necessary provider plugins.
- After successful provider installation, Terraform writes the selected provider versions to a dependency lock file, which should be committed to version control so future terraform init runs select the exact same versions.  
  > After successful installation, Terraform writes information about the selected providers to the dependency lock file. You should commit this file to your version control system to ensure that when you run terraform init again in future Terraform will select exactly the same provider versions.
- The -upgrade flag causes terraform init to ignore the dependency lock file and install the newest provider version that still satisfies the configured version constraints.  
  > -upgrade Upgrade all previously-selected plugins to the newest version that complies with the configuration's version constraints. This will cause Terraform to ignore any selections recorded in the dependency lock file, and to take the newest available version matching the configured version constraints.
- During init, Terraform reads the root configuration directory for backend configuration and initializes the chosen backend with the given settings.  
  > During init, the root configuration directory is consulted for backend configuration and the chosen backend is initialized using the given configuration settings.
- During init, Terraform searches the configuration for module blocks and retrieves the source code for referenced modules from the locations given in their source arguments.  
  > During init, Terraform searches the configuration for module blocks, and retrieves the source code for referenced modules from the locations given in their source arguments.
- The -lockfile=readonly mode suppresses changes to the dependency lock file during init but verifies checksums against already-recorded information; it conflicts with the -upgrade flag.  
  > readonly: suppress the lockfile changes, but verify checksums against the information already recorded. It conflicts with the -upgrade flag.
- The -plugin-dir=PATH option forces terraform init to install plugins only from the specified local directory, overriding registry downloads for that run.  
  > -plugin-dir=PATH — Force plugin installation to read plugins only from the specified directory, as if it had been configured as a filesystem_mirror in the CLI configuration.
- To reinitialize with a changed backend configuration, you must supply either -reconfigure (discard existing state migration) or -migrate-state (copy existing state to the new backend).  
  > Re-running init with an already-initialized backend will update the working directory to use the new backend settings. Either -reconfigure or -migrate-state must be supplied to update the backend configuration.
- terraform init is the first command you should run after writing a new Terraform configuration or cloning an existing one from version control.  
  > This is the first command you should run after writing a new Terraform configuration or cloning an existing configuration from version control.
- terraform init is safe to run multiple times; it will never delete your existing configuration or state.  
  > This command will never delete your existing configuration or state.
- Re-running terraform init after modules have already been installed will install sources for any newly added modules but will not change already-installed modules.  
  > Re-running init with modules already installed will install the sources for any modules that were added to configuration since the last init, but will not change any already-installed modules.
- Use the -upgrade flag with terraform init to update all modules to the latest available source code, overriding the default behavior of leaving already-installed modules unchanged.  
  > Use -upgrade to override this behavior, updating all modules to the latest available source code.
- During terraform init, Terraform automatically finds, downloads, and installs the necessary provider plugins from the public Terraform Registry or a third-party registry.  
  > For providers that are published in either the public Terraform Registry or in a third-party provider registry, terraform init will automatically find, download, and install the necessary provider plugins.

## [https://developer.hashicorp.com/terraform/tutorials/aws-get-started/aws-create](https://developer.hashicorp.com/terraform/tutorials/aws-get-started/aws-create)

official, fetched 2026-09-28

- Terraform configuration files are plain text files written in HCL (HashiCorp Configuration Language) with file names ending in .tf  
  > Terraform configuration files are plain text files in HashiCorp's configuration language, HCL,  with file names ending with .tf.
- When the Terraform CLI runs, it loads all .tf configuration files in the current working directory and automatically resolves dependencies  
  > When you perform operations with the Terraform CLI, Terraform loads all of the configuration files in the current working directory and automatically resolves dependencies within your configuration.
- The required_providers block is placed inside the terraform {} block and is used to declare providers with their source and version constraints  
  > terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.92"
    }
  }

  required_version = ">= 1.2"
}
- The source argument for a provider specifies hostname (optional), namespace, and provider name; hashicorp/aws is shorthand for registry.terraform.io/hashicorp/aws  
  > The source argument specifies a hostname (optional), namespace, and provider name. In the example configuration, the aws provider's source is hashicorp/aws, which is a shortened form of registry.terraform.io/hashicorp/aws, the address of the provider in the Terraform Registry.
- If no version constraint is specified in required_providers, Terraform defaults to installing the most recent version of the provider  
  > If you do not specify a version constraint, Terraform defaults to the most recent version of the provider.
- The version constraint string ~> 5.92 means the configuration supports any provider version with major version 5 and minor version greater than or equal to 92  
  > The string ~> 5.92 means your configuration supports any version of the provider with a major version of 5 and a minor version greater than or equal to 92.
- The required_version field in the terraform block constrains which versions of Terraform itself are acceptable; >= 1.2 means any Terraform version 1.2 or higher  
  > The string >= 1.2 means your configuration supports any version of Terraform greater than or equal to 1.2.
- You can check your installed Terraform version by running the terraform -version command  
  > You can check your current Terraform version by running the terraform -version command.
$ terraform -version
Terraform v1.12.0
on darwin_arm64
- The provider block for AWS requires at minimum a region argument; the recommended convention is to place it in main.tf  
  > provider "aws" {
  region = "us-west-2"
}
- Terraform's AWS provider uses the same authentication methods as the AWS CLI; credentials can be supplied via the AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables  
  > To use your IAM credentials to authenticate the Terraform AWS provider, set the AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables.
$ export AWS_ACCESS_KEY_ID=
$ export AWS_SECRET_ACCESS_KEY=
- You can verify AWS credentials are correctly configured by running aws configure list  
  > Use the AWS CLI to verify your credentials.
$ aws configure list
      Name                    Value             Type    Location
      ----                    -----             ----    --------
   profile                <not set>             None    None
access_key     ****************ZJZK              env
secret_key     ****************St8S              env
    region                <not set>             None    None
- Running terraform init downloads and installs the providers defined in the configuration into a hidden .terraform subdirectory of the working directory  
  > Terraform downloaded the aws provider and installed it in a hidden .terraform subdirectory of your current working directory.
- terraform init must be run before applying any configuration; it initializes the workspace and downloads providers  
  > Before you can apply your configuration, you must initialize your Terraform workspace with the terraform init command. As part of initialization, Terraform downloads and installs the providers defined in your configuration in your current working directory.
- After terraform init, a .terraform.lock.hcl lock file is created that records the exact provider versions selected, ensuring consistency across future runs  
  > Terraform also created a file named .terraform.lock.hcl which specifies the exact provider versions used with your workspace, ensuring consistency between runs.
- The .terraform.lock.hcl file should be included in version control so that terraform init makes the same provider selections by default in the future  
  > Terraform has created a lock file .terraform.lock.hcl to record the provider selections it made above. Include this file in your version control repository so that Terraform can guarantee to make the same selections by default when you run "terraform init" in the future.
- The recommended convention is to place the terraform {} block (including required_providers) in a dedicated terraform.tf file and provider/resource blocks in main.tf  
  > Using a consistent file structure makes maintaining your Terraform projects easier, so we recommend configuring your Terraform block in a dedicated terraform.tf file.
- Multiple provider blocks can be used in one configuration to handle multiple providers or multiple instances of the same provider with different settings such as different regions  
  > You can use multiple provider blocks in your Terraform configuration to configure multiple providers or multiple instances of the same provider with different configurations, such as a different region.
- The terraform fmt command automatically reformats all .tf files in the current directory to HashiCorp's recommended style and prints the names of any files it modifies  
  > The terraform fmt command automatically reformats all configuration files in the current directory according to HashiCorp's recommended style.
In your terminal, use Terraform to format your configuration files.
$ terraform fmt
main.tf
Terraform prints the names of the files it modified, if any.

## [https://developer.hashicorp.com/terraform/language/providers/requirements](https://developer.hashicorp.com/terraform/language/providers/requirements)

official, fetched 2026-09-28

- Provider requirements are declared inside a required_providers block, which must be nested inside the top-level terraform block.  
  > The required_providers block must be nested inside the top-level
terraform block (which can also contain other settings).
- Each entry in required_providers takes a local name as the key, and an object with a source and version as the value.  
  > terraform {
  required_providers {
    mycloud = {
      source  = "mycorp/mycloud"
      version = "~> 1.0"
    }
  }
}
- The source argument specifies the global source address for the provider (e.g., hashicorp/aws), and the version argument constrains which versions Terraform may install.  
  > source - the global source address for the
provider you intend to use, such as hashicorp/aws.
version - a version constraint specifying
which subset of available provider versions the module is compatible with.
- Running terraform init installs the declared providers and updates the dependency lock file to the latest version matching the configured version constraint.  
  > Running terraform init locally installs a provider and updates the Dependency lock file with the latest version matching the version string you configured in your required_providers block.
- The version argument in required_providers is optional, but it is strongly recommended to always specify a version constraint.  
  > The version argument is optional; if omitted, Terraform will accept any
version of the provider as compatible. However, we strongly recommend specifying
a version constraint for every provider your module depends on.
- The ~> operator pins the rightmost version component, allowing only patch releases within a specific minor release; for example ~> 1.0.4 allows patch updates but not minor version bumps.  
  > The ~> operator is a convenient
shorthand for allowing the rightmost component of a version to increment. The
following example uses the operator to allow only patch releases within a
specific minor release:
terraform {
  required_providers {
    mycloud = {
      source  = "hashicorp/aws"
      version = "~> 1.0.4"
    }
  }
}
- Root modules (where you run terraform apply) should specify both a minimum and maximum provider version to prevent accidental upgrades to incompatible versions.  
  > A module intended to be used as the root of a configuration — that is, as the
directory where you'd run terraform apply — should also specify the
maximum provider version it is intended to work with, to avoid accidental
upgrades to incompatible new versions.
- Each module should at minimum declare the minimum provider version it is known to work with, using the >= constraint syntax.  
  > Each module should at least declare the minimum provider version it is known
to work with, using the >= version constraint syntax:
terraform {
  required_providers {
    mycloud = {
      source  = "hashicorp/aws"
      version = ">= 1.0"
    }
  }
}
- A provider's source address consists of up to three slash-delimited parts: an optional hostname (defaulting to registry.terraform.io), a namespace, and a type.  
  > Source addresses consist of three parts delimited by slashes (/), as
follows:
[<HOSTNAME>/]<NAMESPACE>/<TYPE>
- If the hostname is omitted from a provider source address, it defaults to registry.terraform.io (the public Terraform Registry).  
  > Hostname (optional): The hostname of the Terraform registry that
distributes the provider. If omitted, this defaults to
registry.terraform.io, the hostname of
the public Terraform Registry.
- The provider's local name is used everywhere in the module except the required_providers block itself; outside that block, provider blocks and resources reference providers by local name.  
  > Outside of the required_providers block, Terraform configurations always refer
to providers by their local names.
- A provider block is added separately from required_providers to configure provider-specific settings such as authentication and region.  
  > Add a top-level provider block to your configuration to configure a provider with authentication, a region, and other provider-specific arguments.
- Using a provider's preferred local name (matching the 'type' portion of its source address, e.g., 'aws' for hashicorp/aws) allows Terraform to automatically associate resources with the correct provider without needing an explicit provider meta-argument.  
  > If a resource doesn't specify which
provider configuration to use, Terraform interprets the first word of the
resource type as a local provider name.
- You can upgrade a provider version in the lock file by changing the version constraint in required_providers and re-running terraform init.  
  > You can upgrade a provider version in your lock file by changing the version in the required_providers block and re-running terraform init.
- To ensure reproducible installs, create a dependency lock file with Terraform CLI and commit it to version control alongside your configuration.  
  > To ensure Terraform always installs the same provider versions for a given
configuration, you can use Terraform CLI to create a
dependency lock file
and commit it to version control along with your configuration.

## [https://developer.hashicorp.com/terraform/language/block/resource](https://developer.hashicorp.com/terraform/language/block/resource)

official, fetched 2026-09-28

- To reference a resource in configuration, use the syntax <TYPE>.<LABEL>.  
  > To reference the resource in your configuration, you must refer to it using <TYPE>.<LABEL> syntax.
- A minimal AWS instance resource block sets the ami and instance_type arguments.  
  > resource "aws_instance" "web" {
  ami           = "ami-a1b2c3d4"
  instance_type = "t2.micro"
}
- The count meta-argument instructs Terraform to provision multiple instances of the same resource; it accepts a number.  
  > The count meta-argument instructs Terraform to provision multiple instances of the same resource with identical or similar configuration. You cannot use both a count and  for_each argument in the same block.
- count is best suited for nearly identical resource instances, while for_each is best suited when instances differ based on a map or set of values.  
  > The count argument is most suitable for creating multiple instances that are identical or nearly identical. The for_each argument is most suitable for creating multiple similar instances based on attributes defined in a map or set.
- Using count with the built-in length() function and an input variable creates one resource instance per element in the variable list, with each instance accessible via count.index.  
  > count = length(var.subnet_ids)

  ami           = "ami-a1b2c3d4"
  instance_type = "t2.micro"
  subnet_id     = var.subnet_ids[count.index]
- for_each accepts either a map of key-value pairs or a set of strings.  
  > for_each   map or set of strings | mutually exclusive with count
- When using for_each with tomap(), each resource instance can reference each.key and each.value to access the map entries.  
  > resource "azurerm_resource_group" "rg" {
  for_each = tomap({
    a_group       = "eastus"
    another_group = "westus2"
  })
  name     = each.key
  location = each.value
}
- When using for_each with toset(), each resource instance uses each.key to reference the current set element.  
  > resource "aws_iam_user" "the-accounts" {
  for_each = toset(["Todd", "James", "Alice", "Dottie"])
  name     = each.key
}
- Resource attributes from another resource block are referenced using the expression <TYPE>.<LABEL>.<ATTRIBUTE>, as shown by aws_iam_role.example.name.  
  > resource "aws_iam_instance_profile" "example" {
  role = aws_iam_role.example.name
}
- The depends_on meta-argument explicitly declares that Terraform must complete all operations on the listed upstream resource before operating on the current resource.  
  > The depends_on meta-argument specifies an upstream resource that the resource depends on. Terraform must complete all operations on the upstream resource before performing operations on the resource containing the depends_on argument.
- depends_on takes a list of resource references as its value.  
  > depends_on = [
    aws_iam_role_policy.example
  ]
- The lifecycle block is a meta-argument that controls how Terraform creates, updates, and destroys a resource, and can only use literal values because Terraform processes it before evaluating other expressions.  
  > Configurations defined in the lifecycle block affect how Terraform constructs and traverses the dependency graph. You can only use literal values in the lifecycle block because Terraform processes them before it evaluates arbitrary expressions for a run.
- The lifecycle ignore_changes directive takes a list of resource attributes that Terraform should ignore when planning updates.  
  > resource "aws_instance" "example" {
   # ...

   lifecycle {
      ignore_changes = [tags]
   }
}
- The lifecycle create_before_destroy directive causes Terraform to create the replacement resource before destroying the existing one.  
  > create_before_destroy: Terraform creates a replacement resource before destroying the current resource.
- The lifecycle prevent_destroy directive causes Terraform to return an error when a plan would destroy the resource, but does not prevent destruction if the resource block is removed from configuration.  
  > prevent_destroy: Terraform rejects operations to destroy the resource and returns an error. This rule doesn't prevent Terraform from destroying the resource if you remove the resource configuration.
- The lifecycle replace_triggered_by directive replaces the resource whenever any of the referenced resources or attributes change.  
  > resource "aws_appautoscaling_target" "ecs_target" {
   ...
   lifecycle {
   replace_triggered_by = [
      aws_ecs_service.svc.id
     ]
   }
}
- A precondition block inside lifecycle specifies an expression that must evaluate to true before Terraform operates on the resource; if false, Terraform prints the error_message.  
  > precondition {
      condition     = data.aws_ami.example.architecture == "x86_64"
      error_message = "The selected AMI must be for the x86_64 architecture."
    }
- A postcondition block inside lifecycle specifies an expression that must evaluate to true after Terraform operates on the resource; the self object refers to the resource's own attributes.  
  > postcondition {
      condition     = self.public_dns != ""
      error_message = "EC2 instance must be in a VPC that has public DNS hostnames enabled."
    }
- The provider meta-argument selects an alternate provider configuration (alias) for a specific resource block.  
  > resource "google_compute_instance" "example" {
  provider = google.europe
  # ...
}
- Inside connection blocks, the self object must be used instead of the resource's own name to avoid creating a dependency cycle.  
  > Expressions in connection blocks cannot refer to their parent resource by name. References create dependencies, and referring to a resource by name within its own block would create a dependency cycle. Instead, use the self object in expressions to refer to the connection block's parent block, including all of its attributes. For example, use self.public_ip to reference the public_ip attribute in an aws_instance.
- A module can use for_each to create one instance of that module per element in a set, and each.key is used to differentiate the instances.  
  > module "bucket" {
  for_each = toset(["assets", "media"])
  source   = "./publish_bucket"
  name     = "${each.key}_bucket"
}

## [https://developer.hashicorp.com/terraform/language/values/variables](https://developer.hashicorp.com/terraform/language/values/variables)

official, fetched 2026-09-28

- A variable block can declare the type, description, and default arguments for an input variable.  
  > variable "instance_type" {
  type        = string
  description = "EC2 instance type for the web server"
  default     = "t2.micro"
}
- A variable block without a default argument causes Terraform to prompt the user for a value before generating a plan.  
  > If a module defines a variable without a default argument, Terraform prompts the user to supply a value for that variable before it generates a plan.
- A variable block can include an optional validation block with a condition expression and an error_message to enforce allowed values.  
  > variable "environment" {
  type        = string
  description = "Deployment environment name"
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}
- Input variable values are referenced in configuration using the var.<NAME> syntax.  
  > To reference a variable in other parts of your configuration, use var.<NAME> syntax.
- Variable references can be used inside string templates and as direct argument values within resource blocks.  
  > instance_type = var.instance_type
  subnet_id     = var.subnet_id

  tags = {
    Environment = var.environment
    Name        = "${var.environment}-web-server"
  }
- Setting the sensitive argument to true on a variable prevents Terraform from displaying its value in CLI output.  
  > variable "database_password" {
  type        = string
  description = "Password for the RDS database instance"
  sensitive   = true
}
- Variables can be assigned on the command line using the -var flag with the syntax -var="NAME=VALUE".  
  > terraform apply -var="instance_type=t3.medium" -var="environment=prod"
- Variable definition files use a .tfvars or .auto.tfvars extension and assign multiple variable values in one file.  
  > You can assign values directly to variable names in files with a .tfvars or .auto.tfvars extension.
- Terraform automatically loads files named terraform.tfvars, terraform.tfvars.json, or any file ending in .auto.tfvars or .auto.tfvars.json.  
  > Terraform automatically loads variable definition files if it detects any of the following:
File names ending in .auto.tfvars or .auto.tfvars.json
A file named terraform.tfvars.json
A file named terraform.tfvars
- A specific .tfvars file can be passed to the CLI using the -var-file flag.  
  > terraform apply -var-file="production.auto.tfvars"
- Environment variables prefixed with TF_VAR_ followed by the variable name are used to set Terraform input variable values.  
  > export TF_VAR_instance_type=t3.medium
export TF_VAR_environment=staging
terraform apply
- The order of precedence for variable values, from highest to lowest, ends with the default argument of the variable block being the lowest precedence.  
  > Values defined in HCP Terraform and on the command line take precedence over other ways of assigning variable values. The variable's default argument is at the lowest level of precedence.
- Terraform errors if you attempt to assign a value for an undeclared variable using -var on the command line, but only warns for undeclared variables in variable definition files and silently ignores them when set as environment variables.  
  > Terraform ignores any assigned environment variables that do not have a matching variable block.
Terraform warns you if you assign an undeclared variable in a variable definition file, letting you catch accidental misspellings in your configuration or definition files.
Terraform errors if you attempt to assign a value for an undeclared variable with -var on the command line.
- Complex variable values passed via environment variables or command-line flags must use proper JSON syntax.  
  > export TF_VAR_complex_config='{"key": "value", "list": ["a", "b"]}'

## [https://developer.hashicorp.com/terraform/language/values/locals](https://developer.hashicorp.com/terraform/language/values/locals)

official, fetched 2026-09-28

- Local values assign names to expressions so you can use the name multiple times within a module instead of repeating that expression.  
  > Local values assign names to expressions, letting you use the name multiple times within a module instead of repeating that expression.
- A locals block can be defined in any module, and any valid Terraform expression can be assigned as its value.  
  > You can define the locals block in any module and can assign any valid Terraform expression as its value.
- Within a locals block, you can reference variables, resource attributes, function outputs, and other local values.  
  > You can reference the following constructs:
Variables
Resource attributes
Function outputs
Other local values
- A local value can be built from string interpolation of input variables, such as combining a project name and environment.  
  > resource_name = "${var.project_name}-${var.environment}"
- The built-in function length can be used inside a locals block, for example to count the number of items in a subnet list.  
  > subnet_count          = length(var.subnet_ids)
- A local value can reference another local value using the local.<NAME> syntax, for example to combine a flag with a variable.  
  > monitoring_enabled = var.monitoring || local.is_production
- To reference a local value defined in a locals block, use the singular local.<NAME> syntax (not locals).  
  > Use the local.<NAME> syntax to reference values from a locals block in your configuration. The locals block defines local values, but you must use the singular local keyword to reference the individual values.
- Local values can be used to set resource arguments such as subnet_id, monitoring, and tags inside a resource block.  
  > subnet_id     = local.primary_public_subnet
  monitoring    = local.monitoring_enabled

  tags = {
    Name        = local.resource_name
    Environment = var.environment
  }
- Local values can be interpolated into strings when setting resource arguments, such as when naming a security group.  
  > name = "${local.resource_name}-sg"
- Local values are scoped to the module where they are defined and cannot be accessed from other modules directly, but can be passed to a child module as an argument.  
  > You can access local values in the module where you define them, but not in other modules. However, you can pass a local value to a child module as an argument.
- Local values are best used when a single value is reused in many places (to allow changing it in one place) or when the value is the result of a complex expression.  
  > Use local values in situations where you either reuse a single value in many places to let you change a value in a single place or when the value is the result of a complex expression.

## [https://developer.hashicorp.com/terraform/language/expressions/references](https://developer.hashicorp.com/terraform/language/expressions/references)

official, fetched 2026-09-28

- A managed resource is referenced in expressions using the syntax <RESOURCE TYPE>.<NAME>  
  > <RESOURCE TYPE>.<NAME> represents a managed resource of
the given type and name.
- If a resource does not use count or for_each, its reference resolves to a single object whose attributes are accessible with dot or square-bracket notation.  
  > If the resource doesn't use count or for_each, the reference's value is an
object. The resource's attributes are elements of the object, and you can
access them using dot or square bracket notation.
- When a resource uses the count meta-argument, its reference resolves to a list of objects representing its instances.  
  > If the resource has the count argument set, the reference's value is a
list of objects representing its instances.
- When a resource uses the for_each meta-argument, its reference resolves to a map of objects representing its instances.  
  > If the resource has the for_each argument set, the reference's value is a
map of objects representing its instances.
- Input variable values are referenced in expressions using the syntax var.<NAME>.  
  > var.<NAME> is the value of the input variable of the given name.
- When a variable has a type constraint declared, Terraform automatically converts the caller's provided value to conform to that type, so var.<NAME> always produces a value matching the declared type.  
  > If the variable has a type constraint (type argument) as part of its
declaration, Terraform will automatically convert the caller's given value
to conform to the type constraint.
For that reason, you can safely assume that a reference using var. will
always produce a value that conforms to the type constraint, even if the caller
provided a value of a different type that was automatically converted.
- If an input variable is declared with an object type constraint, only the attributes listed in that constraint are available in expressions; additional attributes passed by the caller are not accessible.  
  > if you define a variable as being of an object type
with particular attributes then only those specific attributes will be
available in expressions elsewhere in the module, even if the caller actually
passed in a value with additional attributes. You must define in the type
constraint all of the attributes you intend to use elsewhere in your module.
- Local values are referenced in expressions using the syntax local.<NAME>.  
  > local.<NAME> is the value of the local value of the given name.
- Local values can reference other local values, even within the same locals block, as long as there are no circular dependencies.  
  > Local values can refer to other local values, even within the same locals
block, as long as you don't introduce circular dependencies.
- Output values are referenced by callers using the syntax module.<MODULE NAME>.<OUTPUT NAME>.  
  > To access one of the module's
output values, use module.<MODULE NAME>.<OUTPUT NAME>.
- A resource argument set in the configuration can be referenced elsewhere using the dot-separated path, e.g. aws_instance.example.ami.  
  > The ami argument set in the configuration can be used elsewhere with
the reference expression aws_instance.example.ami.
- An exported attribute of a resource (such as id) is accessed with the same dot-notation syntax as arguments, e.g. aws_instance.example.id.  
  > The id attribute exported by this resource type can be read using the
same syntax, giving aws_instance.example.id.
- Attributes of repeated nested blocks can be collected into a list using a splat expression, e.g. aws_instance.example.ebs_block_device[*].device_name.  
  > The arguments of the ebs_block_device nested blocks can be accessed using
a splat expression. For example, to obtain a list of
all of the device_name values, use
aws_instance.example.ebs_block_device[*].device_name.
- When a resource uses count, all instance ids can be retrieved as a list with a splat expression, e.g. aws_instance.example[*].id, or a single instance accessed by index, e.g. aws_instance.example[0].id.  
  > aws_instance.example[*].id returns a list of all of the ids of each of the
instances.
aws_instance.example[0].id returns just the id of the first instance.
- When a resource uses for_each, a specific instance is accessed by its key using index syntax, e.g. aws_instance.example["a"].id, or all ids can be collected with a for expression.  
  > aws_instance.example["a"].id returns the id of the "a"-keyed resource.
[for value in aws_instance.example: value.id] returns a list of all of the ids
of each of the instances.
- Splat expressions cannot be used directly on for_each resources (which are maps, not lists); the values() function must be used first to extract instances as a list.  
  > Note that unlike count, splat expressions are not directly applicable to resources managed with for_each, as splat expressions must act on a list value. However, you can use the values() function to extract the instances as a list and use that list value in a splat expression:
values(aws_instance.example)[*].id
- Within a resource block that uses count, the special value count.index is available as a block-local reference.  
  > count.index, in resources that use
the count meta-argument.
- Within a resource block that uses for_each, the block-local values each.key and each.value are available.  
  > each.key / each.value, in resources that use
the for_each meta-argument.
- Referencing a named value from another resource in a block body creates an implicit dependency between the two resources, which Terraform uses to infer the correct apply order.  
  > an expression in a resource
argument that refers to another managed resource creates an implicit dependency
between the two resources.
- The count meta-argument value cannot be unknown at plan time; it must be resolvable during planning to determine how many instances to create.  
  > The count meta-argument for resources cannot be unknown, since it must
be evaluated during the plan phase to determine how many instances are to
be created.
- If a sensitive resource attribute is used in an output value, Terraform requires the output itself to also be marked sensitive.  
  > If you use a sensitive value from a resource attribute as part of an
output value then Terraform will require
you to also mark the output value itself as sensitive, to confirm that you
intended to export it.

## [https://developer.hashicorp.com/terraform/cli/commands/plan](https://developer.hashicorp.com/terraform/cli/commands/plan)

official, fetched 2026-09-28

- terraform plan does not carry out the proposed changes — it only previews them.  
  > The plan command alone does not actually carry out the proposed changes You can use this command to check whether the proposed changes match what you expected before you apply the changes or share your changes with your team for broader review.
- By default, terraform plan reads current remote state, compares it to configuration, and proposes change actions needed to make remote objects match the configuration.  
  > By default, Terraform performs the following operations when it creates a plan:
Reads the current state of any already-existing remote objects to make sure that the Terraform state is up-to-date.
Compares the current configuration to the prior state and noting any differences.
Proposes a set of change actions that should, if applied, make the remote objects match the configuration.
- If Terraform detects no changes are needed, terraform plan reports that no actions need to be taken.  
  > If Terraform detects that no changes are needed to resource instances or to root module output values, terraform plan will report that no actions need to be taken.
- The -out=FILE option saves the generated plan to a file that can later be passed to terraform apply to execute the planned changes.  
  > -out=FILENAME - Writes the generated plan to the given filename in an opaque file format that you can later pass to terraform apply to execute the planned changes, and to some other Terraform commands that can work with saved plan files.
- A plan run without -out=FILE is a speculative plan — it describes the effect of changes but has no intent to apply them.  
  > If you run terraform plan without the -out=FILE option then it will create a speculative plan, which is a description of the effect of the plan but without any intent to actually apply it.
- terraform apply automatically generates a new plan and prompts for approval when run interactively.  
  > By default, the "apply" command automatically generates a new plan and prompts for you to approve it.
- Destroy mode (-destroy flag) creates a plan whose goal is to destroy all remote objects, leaving an empty Terraform state — equivalent to running terraform destroy.  
  > Destroy mode: creates a plan whose goal is to destroy all remote objects that currently exist, leaving an empty Terraform state. It is the same as running terraform destroy.
- Destroy mode is activated by passing the -destroy command-line option to terraform plan or terraform apply.  
  > Activate destroy mode using the -destroy command line option.
- Terraform uses the symbol + to indicate a resource will be created, - to indicate destruction, ~ for an in-place update, and -/+ for destroy-then-recreate (replace).  
  > Symbol
Action
Description
+
Create
This resource does not currently exist. Terraform will create it.
-
Destroy
Terraform will destroy this resource.
~
In-place update
Terraform will update this resource without destroying and recreating it.
-/+
Replace
Terraform will destroy this resource and then recreate it.
- The plan summary line shows counts of resources to add, change, and destroy, e.g. 'Plan: 2 to add, 1 to change, 2 to destroy.'  
  > Plan: 2 to add, 1 to change, 2 to destroy.
- A plan output block annotated with -/+ shows which attribute change forces replacement, e.g. an AMI change forces replacement.  
  >   # aws_instance.web must be replaced
  -/+ resource "aws_instance" "web" {
      ~ ami                                  = "ami-02c98622c4c3f017d" -> "ami-0d7d6fe23ca71032d" # forces replacement
- The conventional filename for a saved plan file is tfplan; files must not use the .tf suffix because Terraform would try to parse them as configuration.  
  > Terraform will allow any filename for the plan file, but a typical convention is to name it tfplan. Do not name the file with a suffix that Terraform recognizes as another file format; if you use a .tf suffix then Terraform will try to interpret the file as a configuration source file, which will then cause syntax errors for subsequent commands.
- The -detailed-exitcode option makes terraform plan return exit code 0 for no changes, 1 for error, and 2 for changes present.  
  > -detailed-exitcode - Returns a detailed exit code when the command exits. When provided, this argument changes the exit codes and their meanings to provide more granular information about what the resulting plan contains:
0 = Succeeded with empty diff (no changes)
1 = Error
2 = Succeeded with non-empty diff (changes present)
- The -parallelism=n option limits the number of concurrent operations Terraform performs when walking the graph; it defaults to 10.  
  > -parallelism=n - Limit the number of concurrent operations as Terraform walks the graph. Defaults to 10.
- Input variable values can be passed on the command line with -var='NAME=VALUE', for example setting env to prod.  
  > $ terraform plan -var='env=prod'
- Input variable values can be loaded from a .tfvars file using the -var-file option.  
  > $ terraform plan -var-file='my-vars.tfvars'
- Terraform will error if there is a space before or after the equals sign in a -var argument.  
  > Warning: Terraform will error if you include a space before or after the equals sign (e.g., -var "length = 2").
- Refresh-only mode updates the Terraform state to match changes made to remote objects outside of Terraform, without proposing configuration changes.  
  > Refresh-only mode: creates a plan whose goal is only to update the Terraform state and any root module output values to match changes made to remote objects outside of Terraform.
- The terraform plan subcommand looks in the current working directory for the root module configuration.  
  > The plan subcommand looks in the current working directory for the root module configuration.

## [https://developer.hashicorp.com/terraform/cli/commands/apply](https://developer.hashicorp.com/terraform/cli/commands/apply)

official, fetched 2026-09-28

- The terraform apply command executes the operations proposed in a Terraform plan.  
  > The terraform apply command executes the operations proposed in a Terraform plan.
- When run without a saved plan file, terraform apply automatically creates a new execution plan, prompts you to approve it, and then performs the indicated operations.  
  > When you run terraform apply without passing a saved plan file, Terraform automatically creates a new execution plan as if you had run terraform plan, prompts you to approve that plan, and performs the indicated operations.
- The -auto-approve option instructs Terraform to apply the plan without asking for confirmation, including for destructive operations such as deleting resources.  
  > -auto-approve - Skips interactive approval of the plan before applying. Terraform ignores this option when you pass a previously-saved plan file. This is because Terraform interprets the act of passing the plan file as the approval. Note that this includes destructive operations such as deleting resources.
- When you pass a saved plan file to terraform apply, Terraform performs the operations in the saved plan without prompting for confirmation.  
  > When you pass a saved plan file to terraform apply, Terraform performs the operations in the saved plan without prompting you for confirmation.
- terraform apply supports a -destroy planning mode, which creates a plan to destroy all remote objects.  
  > Planning Modes: These include -destroy, which creates a plan to destroy all remote objects, and -refresh-only, which creates a plan to update Terraform state and root module output values.
- After a successful terraform apply, Terraform updates the state file with any changes to your resources.  
  > Updates the state file with any changes to your resources.
- The default concurrency for terraform apply is 10 parallel operations when walking the resource graph.  
  > -parallelism=n - Limit the number of concurrent operations as Terraform walks the graph. Defaults to 10.
- When Terraform encounters an error during an apply, it does not automatically roll back a partially-completed apply; you must resolve the error and run apply again.  
  > Terraform does not automatically roll back a partially-completed apply. After you resolve the error, you must apply your configuration again to update your infrastructure to the desired state.
- You can set an input variable value at apply time using the -var flag, for example: terraform apply -var='env=prod'.  
  > $ terraform apply -var='env=prod'
- You can supply a file of variable values to terraform apply using the -var-file flag, for example: terraform apply -var-file='my-vars.tfvars'.  
  > $ terraform apply -var-file='my-vars.tfvars'
- When a saved plan file is passed to terraform apply, no additional planning modes or options can be specified, because the plan file already contains the final decisions.  
  > When using a saved plan, you cannot specify any additional planning modes or options. These options only affect Terraform's decisions about which actions to take, and the plan file contains the final results of those decisions.
- The -replace option lets you specify a resource instance that Terraform should replace rather than update or leave unchanged.  
  > -replace=resource - Specifies a resource instance that Terraform plans to replace instead of performing an update or no-op operation.
- Passing a directory path to terraform apply was deprecated in v0.14 and removed in v0.15; the -chdir global option should be used instead.  
  > That usage was deprecated in Terraform v0.14 and removed in Terraform v0.15. If your workflow relies on overriding the root module directory, use the -chdir global option instead, which works across all commands.

## [https://developer.hashicorp.com/terraform/language/state/purpose](https://developer.hashicorp.com/terraform/language/state/purpose)

official, fetched 2026-09-28

- Terraform state maps configuration resource definitions to real-world objects, for example recording that resource "aws_instance" "foo" corresponds to instance ID i-abcd1234 on a remote system.  
  > when you have a resource resource "aws_instance" "foo" in your configuration, Terraform uses this mapping to know that the resource resource "aws_instance" "foo" represents a real world object with the instance ID i-abcd1234 on a remote system.
- Terraform state stores metadata about resource dependencies so that Terraform can determine the correct destruction order even when a resource has been removed from the configuration.  
  > To ensure correct operation, Terraform retains a copy of the most recent set of dependencies within the state. Now Terraform can still determine the correct order for destruction from the state when you delete one or more items from the configuration.
- Terraform state also stores a pointer to the provider configuration most recently used with each resource, which matters when multiple aliased providers are present.  
  > Terraform also stores other metadata for similar reasons, such as a pointer to the provider configuration that was most recently used with the resource in situations where multiple aliased providers are present.
- Terraform state caches the attribute values of all resources as a performance optimisation, so that Terraform does not have to query every provider on every plan or apply for large infrastructures.  
  > Terraform stores a cache of the attribute values for all resources in the state. This is the most optional feature of Terraform state and is done only as a performance improvement.
- By default, Terraform syncs all resources in state on every plan and apply, but large-infrastructure users work around slow API calls and rate limits using the -refresh=false flag and the -target flag, treating cached state as the record of truth.  
  > Larger users of Terraform make heavy use of the -refresh=false flag as well as the -target flag in order to work around this. In these scenarios, the cached state is treated as the record of truth.
- In the default configuration, Terraform stores state in a file in the current working directory where Terraform was run.  
  > In the default configuration, Terraform stores the state in a file in the current working directory where Terraform was run.
- Storing state locally (e.g. in version control) is risky for teams because all team members must work with the same state; a remote backend is the recommended solution.  
  > when using Terraform in a team it is important for everyone to be working with the same state so that operations will be applied to the same remote objects. Remote state is the recommended solution to this problem.
- A fully-featured remote state backend provides remote locking, which prevents two or more users from running Terraform simultaneously and ensures each run starts with the most recently updated state.  
  > With a fully-featured state backend, Terraform can use remote locking as a measure to avoid two or more different users accidentally running Terraform at the same time, and thus ensure that each Terraform run begins with the most recent updated state.
- Terraform requires a one-to-one mapping between remote objects and resource instances; binding a remote object to multiple resource instances makes the state mapping ambiguous and can cause unexpected behaviour.  
  > Terraform expects that each remote object is bound to only one resource instance in the configuration. If a remote object is bound to multiple resource instances, the mapping from configuration to the remote object in the state becomes ambiguous, and Terraform may behave unexpectedly.
- Terraform guarantees a one-to-one mapping between remote objects and resource instances in state; binding a remote object to multiple resource instances causes ambiguous behaviour.  
  > Terraform expects that each remote object is bound to only one resource instance in the configuration. If a remote object is bound to multiple resource instances, the mapping from configuration to the remote object in the state becomes ambiguous, and Terraform may behave unexpectedly. Terraform can guarantee a one-to-one mapping when it creates objects and records their identities in the state.
- A remote backend with remote locking is the recommended solution for teams, preventing two users from running Terraform simultaneously and ensuring each run starts with the most recent state.  
  > Remote state is the recommended solution to this problem. With a fully-featured state backend, Terraform can use remote locking as a measure to avoid two or more different users accidentally running Terraform at the same time, and thus ensure that each Terraform run begins with the most recent updated state.

## [https://developer.hashicorp.com/terraform/cli/commands/state](https://developer.hashicorp.com/terraform/cli/commands/state)

official, fetched 2026-09-28

- The terraform state commands are used to modify Terraform state instead of editing the state file directly.  
  > You can use the terraform state commands to modify the Terraform state instead modifying the state directly.
- The available terraform state subcommands include list, mv, pull, replace-provider, rm, and show.  
  > terraform state list
terraform state mv
terraform state pull
terraform state replace-provider
terraform state rm
terraform state show
- terraform state subcommands work with remote state the same way they work with local state.  
  > The Terraform state subcommands all work with remote state just as if it was local state.
- When using remote state, reads and writes take longer because each operation does a full network roundtrip.  
  > Reads and writes may take longer than normal as each read and each write do a full network roundtrip.
- All terraform state subcommands that modify state automatically write backup files, and this behaviour cannot be disabled.  
  > Note that backups for state modification can not be disabled. Due to the sensitivity of the state file, Terraform forces every state modification command to write a backup file.
- The path of backup files written by terraform state subcommands can be controlled with the -backup flag.  
  > The path of these backup file can be controlled with -backup.
- Read-only terraform state subcommands such as terraform state list do not write backup files because they do not modify state.  
  > Subcommands that are read-only (such as list) do not write any backup files since they aren't modifying the state.
- Backup files created by terraform state commands must be removed manually if they are not needed.  
  > You'll have to remove these files manually if you don't want to keep them around.

## [https://developer.hashicorp.com/terraform/language/state/remote](https://developer.hashicorp.com/terraform/language/state/remote)

official, fetched 2026-09-28

- By default, Terraform stores state locally in a file named terraform.tfstate.  
  > By default, Terraform stores state locally in a file named terraform.tfstate.
- Using a local state file in a team environment is problematic because every user must ensure they have the latest state data before running Terraform, and must ensure no one else runs Terraform simultaneously.  
  > each user must make sure they always have the latest state data before running Terraform and make sure that nobody else runs Terraform at the same time.
- With remote state, Terraform writes state data to a remote data store that can be shared among all team members.  
  > With remote state, Terraform writes the state data to a remote data store, which can then be shared between all members of a team.
- Terraform supports storing state in HCP Terraform, HashiCorp Consul, Amazon S3, Azure Blob Storage, Google Cloud Storage, Alibaba Cloud OSS, and more.  
  > Terraform supports storing state in HCP Terraform, HashiCorp Consul, Amazon S3, Azure Blob Storage, Google Cloud Storage, Alibaba Cloud OSS, and more.
- Remote state is implemented via a backend or HCP Terraform, both configured in the configuration's root module.  
  > Remote state is implemented by a backend or by HCP Terraform, both of which you can configure in your configuration's root module.
- For fully-featured remote backends, Terraform can use state locking to prevent concurrent runs of Terraform against the same state.  
  > For fully-featured remote backends, Terraform can also use state locking to prevent concurrent runs of Terraform against the same state.
- HCP Terraform offers an even stronger locking concept that can detect attempts to create a new plan when an existing plan is already awaiting approval, by queuing Terraform operations centrally.  
  > HCP Terraform by HashiCorp is a commercial offering that supports an even stronger locking concept that can also detect attempts to create a new plan when an existing plan is already awaiting approval, by queuing Terraform operations in a central location.

## [https://developer.hashicorp.com/terraform/language/state/backends](https://developer.hashicorp.com/terraform/language/state/backends)

official, fetched 2026-09-28

- The local (default) backend stores Terraform state in a local JSON file on disk.  
  > the local (default) backend stores state in a local JSON file on disk.
- When using a non-local (remote) backend, Terraform will not persist state anywhere on disk, which is a security benefit for sensitive values in state.  
  > When using a non-local backend, Terraform will not persist the state anywhere on disk except in the case of a non-recoverable error where writing the state to the backend failed. This behavior is a major benefit for backends: if sensitive values are in your state, using a remote backend allows you to use Terraform without that state ever being persisted to disk.
- Even when state is stored remotely, all terraform state commands continue to work as if the state were local.  
  > all Terraform commands such as terraform console, the terraform state operations, terraform taint, and more will continue to work as if the state was local.
- The `terraform state pull` command retrieves remote state and outputs it to stdout.  
  > You can still manually retrieve the state from the remote state using the terraform state pull command. This will load your remote state and output it to stdout.
- The `terraform state push` command manually overwrites remote state and is considered extremely dangerous.  
  > You can also manually write state with terraform state push. This is extremely dangerous and should be avoided if possible. This will overwrite the remote state.
- Terraform protects against pushing state with a differing lineage — a unique ID assigned at state creation — because it likely means you are modifying the wrong state.  
  > Differing lineage: The "lineage" is a unique ID assigned to a state when it is created. If a lineage is different, then it means the states were created at different times and its very likely you're modifying a different state. Terraform will not allow this.
- Every Terraform state has a monotonically increasing serial number; pushing state to a destination that has a higher serial is blocked by Terraform to prevent overwriting newer changes.  
  > Higher serial: Every state has a monotonically increasing "serial" number. If the destination state has a higher serial, Terraform will not allow you to write it since it means that changes have occurred since the state you're attempting to write.
- Both the lineage and higher-serial protections on `terraform state push` can be bypassed with the `-force` flag, but making a backup with `terraform state pull` first is recommended.  
  > Both of these protections can be bypassed with the -force flag if you're confident you're making the right decision. Even if using the -force flag, we recommend making a backup of the state with terraform state pull prior to forcing the overwrite.
- Backends are responsible for state locking, but not all backends support locking.  
  > Backends are responsible for supporting state locking if possible. Not all backends support locking. The documentation for each backend includes details about whether it supports locking or not.
- If Terraform fails to persist state to a remote backend due to an error, it writes state locally to prevent data loss, and the user must manually push it back once the error is resolved.  
  > In the case of an error persisting the state to the backend, Terraform will write the state locally. This is to prevent data loss. If this happens, the end user must manually push the state to the remote backend once the error is resolved.

## [https://developer.hashicorp.com/terraform/language/modules/develop/structure](https://developer.hashicorp.com/terraform/language/modules/develop/structure)

official, fetched 2026-09-28

- The only required element of the standard module structure is the root module — Terraform files must exist in the root directory of the repository.  
  > Root module. This is the only required element for the standard module structure. Terraform files must exist in the root directory of the repository.
- The recommended filenames for a minimal module are main.tf, variables.tf, and outputs.tf, even if they are empty.  
  > main.tf, variables.tf, outputs.tf. These are the recommended filenames for a minimal module, even if they're empty.
- main.tf should be the primary entrypoint of a module, and any nested module calls should be placed in that file.  
  > main.tf should be the primary entrypoint. For a simple module, this may be where all the resources are created. For a complex module, resource creation may be split into multiple files but any nested module calls should be in the main file.
- Input variable declarations belong in variables.tf and output value declarations belong in outputs.tf.  
  > variables.tf and outputs.tf should contain the declarations for variables and outputs, respectively.
- All variables and outputs should have one or two sentence descriptions explaining their purpose.  
  > Variables and outputs should have descriptions. All variables and outputs should have one or two sentence descriptions that explain their purpose.
- Nested (child) modules should be stored under the modules/ subdirectory of the root module.  
  > Nested modules. Nested modules should exist under the modules/ subdirectory.
- When the root module calls nested modules, it should use relative paths such as ./modules/consul-cluster so Terraform treats them as part of the same repository rather than downloading them separately.  
  > If the root module includes calls to nested modules, they should use relative paths like ./modules/consul-cluster so that Terraform will consider them to be part of the same repository or package, rather than downloading them again separately.
- Multiple nested modules within a package should ideally be composable by the caller rather than calling directly to each other, avoiding deeply-nested module trees.  
  > If a repository or package contains multiple nested modules, they should ideally be composable by the caller, rather than calling directly to each other and creating a deeply-nested tree of modules.
- The minimal recommended module structure consists of four files: README.md, main.tf, variables.tf, and outputs.tf.  
  > $ tree minimal-module/
.
├── README.md
├── main.tf
├── variables.tf
├── outputs.tf
- A complete module structure places nested modules under a modules/ subdirectory (each with their own variables.tf, main.tf, and outputs.tf) and usage examples under an examples/ subdirectory.  
  > $ tree complete-module/
.
├── README.md
├── main.tf
├── variables.tf
├── outputs.tf
├── ...
├── modules/
│   ├── nestedA/
│   │   ├── README.md
│   │   ├── variables.tf
│   │   ├── main.tf
│   │   ├── outputs.tf
│   ├── nestedB/
│   ├── .../
├── examples/
│   ├── exampleA/
│   │   ├── main.tf
│   ├── exampleB/
│   ├── .../
- The only required element in the standard module structure is the root module; everything else is optional.  
  > The standard module structure expects the layout documented below. The list may appear long, but everything is optional except for the root module.

## [https://developer.hashicorp.com/terraform/language/modules/develop](https://developer.hashicorp.com/terraform/language/modules/develop)

official, fetched 2026-09-28

- A module is a container for multiple resources that are used together.  
  > A module is a container for multiple resources that are used together.
- The .tf files in your working directory when you run terraform plan or terraform apply together form the root module.  
  > The .tf files in your working directory when you run terraform plan
or terraform apply together form the root
module.
- The root module can call other modules and connect them by passing output values from one to input values of another.  
  > That module may call other modules
and connect them together by passing output values from one to input values
of another.
- Modules commonly use input variables to accept values from the calling module.  
  > Input variables to accept values from
the calling module.
- Modules commonly use output values to return results to the calling module, which can then use them to populate arguments elsewhere.  
  > Output values to return results to the
calling module, which it can then use to populate arguments elsewhere.
- To define a module, create a new directory for it and place one or more .tf files inside, just as you would for a root module.  
  > To define a module, create a new directory for it and place one or more .tf
files inside just as you would do for a root module.
- Terraform can load modules from local relative paths or from remote repositories.  
  > Terraform can load modules
either from local relative paths or from remote repositories
- Modules can call other modules using a module block, but it is recommended to keep the module tree relatively flat and use module composition instead of deeply-nested trees.  
  > Modules can also call other modules using a module block, but we recommend
keeping the module tree relatively flat and using module composition
as an alternative to a deeply-nested tree of modules, because this makes
the individual modules easier to re-use in different combinations.
- Re-usable modules are defined using the same configuration language concepts used in root modules.  
  > Re-usable modules are defined using all of the same
configuration language concepts we use in root modules.

## [https://developer.hashicorp.com/terraform/language/modules/configuration](https://developer.hashicorp.com/terraform/language/modules/configuration)

official, fetched 2026-09-28

- A module block requires a source attribute that tells Terraform where to find the child module's configuration files.  
  > Add the module block to your configuration and configure the source argument, which tells Terraform where to get the child module's configuration files.
- A local subdirectory path can be used as the source for a module block, as shown with './app-cluster'.  
  > module "servers" {
  source = "./app-cluster"

  servers = 5
}
- Input variables exposed by a module author are passed as arguments inside the module block, allowing customization without modifying the module's source code.  
  > Module authors expose inputs that you can configure as arguments in the module block. Inputs let you customize the module's behavior without modifying the module's source code.
- Output values from a child module are referenced in the parent (root) module using the expression module.<MODULE-NAME>.<OUTPUT-NAME>.  
  > You can reference the values in the parent module using the module.<MODULE-NAME>.<OUTPUT-NAME> expression.
- A root module can consume a child module's output value in a resource argument, as demonstrated by referencing module.vpc.vpc_id inside an aws_subnet resource.  
  > resource "aws_subnet" "main" {
  vpc_id     = module.vpc.vpc_id
  cidr_block = "10.0.1.0/24"

  tags = {
    Name = "Main"
   }
 }
- The same module can be called multiple times from the root module by writing multiple module blocks, each with a different name and different input values.  
  > You can configure Terraform to provision multiple instances of the same module resources in one module block, instead of adding multiple blocks to your configuration.
- The 'count' meta-argument in a module block provisions a specified number of identical module instances.  
  > count: Use this argument to state how many instances of a module to provision. All instances have the same configuration.
- The 'for_each' meta-argument in a module block loops through a set of keys to provision similar but distinct module instances.  
  > for_each: Use this argument to loop through a set of keys so that Terraform provisions similar module instances.
- After adding or changing a module block's source in the root module, 'terraform init' must be run to download the module files into the local working directory.  
  > After configuring the module block in the root or calling module, run terraform init to download the module files into the local working directory.
- Terraform clones installed module source configurations into a hidden subdirectory of the workspace's working directory during initialization.  
  > Terraform clones the module source configurations into a hidden subdirectory of the workspace's working directory.
- If the source or version argument of an already-installed module changes, 'terraform init' must be rerun, and the -upgrade flag is needed to upgrade to the latest allowed version.  
  > If you change the source argument or change the version argument for a module in a registry, you must rerun terraform init. For modules that are already installed, include the -upgrade flag to upgrade the module to the latest version allowed by the version constraint.
- Resources defined in a module form a self-contained group, and module authors commonly define outputs to expose attribute values of those resources to the calling module.  
  > The resources defined in a module form a self-contained group of resources. Module authors commonly define outputs that expose attribute values for the resources created by the module.

## [https://developer.hashicorp.com/terraform/tutorials/modules/module-use](https://developer.hashicorp.com/terraform/tutorials/modules/module-use)

official, fetched 2026-09-28

- The `source` argument is required in every module block and can be a Terraform Registry path, a URL, or a local path.  
  > The source argument is required when you use a Terraform module. In the example configuration, Terraform will search for a module in the Terraform Registry that matches the given string. You could also use a URL or local module.
- The `version` argument is not required but is strongly recommended; without it Terraform loads the latest version of the module.  
  > The version argument is not required, but we highly recommend you include it when using a Terraform module. For supported sources, this argument specifies the module version Terraform will load. Without the version argument, Terraform will load the latest version of the module.
- All arguments in a module block other than `source` and `version` are treated as input variables for that module.  
  > Terraform treats other arguments in the module blocks as input variables for the module.
- The VPC module is invoked with input variables for name, CIDR block, availability zones, private subnets, public subnets, NAT gateway toggle, and tags.  
  > module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "3.18.1"

  name = var.vpc_name
  cidr = var.vpc_cidr

  azs             = var.vpc_azs
  private_subnets = var.vpc_private_subnets
  public_subnets  = var.vpc_public_subnets

  enable_nat_gateway = var.vpc_enable_nat_gateway

  tags = var.vpc_tags
}
- The EC2 instances module references the VPC module's outputs directly — `module.vpc.default_security_group_id` for the security group and `module.vpc.public_subnets[0]` for the subnet — expressing a cross-module dependency.  
  >   vpc_security_group_ids = [module.vpc.default_security_group_id]
  subnet_id              = module.vpc.public_subnets[0]
- Two EC2 instances are created inside the VPC by using the `count` meta-argument set to 2, with a dynamic name using `count.index`.  
  >   count = 2
  name  = "my-ec2-cluster-${count.index}"
- The EC2 instances module specifies `instance_type = "t3.micro"` as an input variable to the module.  
  >   ami                    = "ami-0c5204531f799e0c6"
  instance_type          = "t3.micro"
- Module outputs are referenced with the `module.MODULE_NAME.OUTPUT_NAME` convention, and must be explicitly re-exported in the root module's `outputs.tf` to be displayed.  
  > You can reference module outputs in other parts of your configuration. Terraform will not display module outputs by default. You must create a corresponding output in your root module and set it to the module's output.
- The root `outputs.tf` exposes the VPC's public subnet IDs and the EC2 instances' public IPs by referencing child module outputs.  
  > output "vpc_public_subnets" {
  description = "IDs of the VPC's public subnets"
  value       = module.vpc.public_subnets
}

output "ec2_instance_public_ips" {
  description = "Public IP addresses of EC2 instances"
  value       = module.ec2_instances[*].public_ip
}
- A common pattern is to define input variables in `variables.tf` with sensible defaults and pass them into module blocks, but not every module argument needs to be exposed as a variable.  
  > A common pattern is to identify which module arguments you may want to change in the future, and create matching variables in your configuration's variables.tf file with sensible default values. You can pass the variables to the module block as arguments.
You do not need to set all module input variables with variables.
- The VPC CIDR block variable defaults to `"10.0.0.0/16"`, availability zones default to `["us-west-2a", "us-west-2b", "us-west-2c"]`, private subnets default to `["10.0.1.0/24", "10.0.2.0/24"]`, and public subnets default to `["10.0.101.0/24", "10.0.102.0/24"]`.  
  > variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "vpc_azs" {
  description = "Availability zones for VPC"
  type        = list(string)
  default     = ["us-west-2a", "us-west-2b", "us-west-2c"]
}

variable "vpc_private_subnets" {
  description = "Private subnets for VPC"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "vpc_public_subnets" {
  description = "Public subnets for VPC"
  type        = list(string)
  default     = ["10.0.101.0/24", "10.0.102.0/24"]
}
- When using a module for the first time, `terraform init` or `terraform get` must be run to install it; modules are installed into the `.terraform/modules` directory.  
  > When using a new module for the first time, you must run either terraform init or terraform get to install the module. When you run these commands, Terraform will install any new modules in the .terraform/modules directory within your configuration's working directory.
- For local modules, Terraform creates a symlink rather than copying files, so changes to local modules take effect immediately without re-running `terraform init` or `terraform get`.  
  > For local modules, Terraform will create a symlink to the module's directory. Because of this, any changes to local modules will be effective immediately, without having to reinitialize or re-run terraform get.
- Running `terraform apply` on this combined VPC + EC2 stack creates 22 resources in total.  
  > Plan: 22 to add, 0 to change, 0 to destroy.
- After `terraform apply` completes, Terraform prints the declared root outputs — in this case the public subnet IDs and EC2 public IP addresses — directly in the terminal.  
  > Outputs:

ec2_instance_public_ips = [
  "54.245.140.252",
  "34.219.48.47",
]
vpc_public_subnets = [
  "subnet-0cb9ff659ba66a7dd",
  "subnet-0c2788b6ffb0611c0",
]

## [https://developer.hashicorp.com/terraform/tutorials/modules/module-create](https://developer.hashicorp.com/terraform/tutorials/modules/module-create)

official, fetched 2026-09-28

- A typical Terraform module file structure includes LICENSE, README.md, main.tf, variables.tf, and outputs.tf, but none of these files are required or have any special meaning to Terraform.  
  > A typical file structure for a new module is:
.
├── LICENSE
├── README.md
├── main.tf
├── variables.tf
├── outputs.tf
None of these files are required, or have any special meaning to Terraform when
it uses your module. You can create a module with a single .tf file, or use
any other file structure you like.
- In a module, variables.tf holds variable definitions; any variable without a default value becomes a required argument when the module is used.  
  > variables.tf will contain the variable definitions for your module. When
your module is used by others, the variables will be configured as arguments
in the module block. Since all Terraform values must be defined, any
variables that are not given a default value will become required arguments.
- outputs.tf holds output definitions for a module; module outputs are made available to the configuration using the module and are often used to pass information to other parts of the configuration.  
  > outputs.tf will contain the output definitions for your module. Module
outputs are made available to the configuration using the module, so they are
often used to pass information about the parts of your infrastructure defined
by the module to other parts of your configuration.
- terraform.tfstate, terraform.tfstate.backup, the .terraform directory, and *.tfvars files should not be distributed as part of a module.  
  > There are also some other files to be aware of, and ensure that you don't
distribute them as part of your module:
terraform.tfstate and terraform.tfstate.backup: These files contain your
Terraform state, and are how Terraform keeps track of the relationship between
your configuration and the infrastructure provisioned by it.
.terraform: This directory contains the modules and plugins used to
provision your infrastructure.
- A local submodule is placed inside a modules/ subdirectory of the root configuration; the directory name becomes the module name.  
  > Inside your existing configuration directory, create a
directory called modules, with a directory called
aws-s3-static-website-bucket inside of it.
- When Terraform processes a module block it inherits the provider from the enclosing configuration, so provider blocks should not be included inside modules.  
  > Notice that there is no provider block in this configuration. When Terraform
processes a module block, it will inherit the provider from the enclosing
configuration. Because of this, we recommend that you do not include provider
blocks in modules.
- Module input variables are set by passing arguments in the module block of the calling configuration, not via command-line flags or .tfvars files.  
  > When using a module, variables are set by
passing arguments to the module in your configuration. You will set some of
these variables when calling this module from your root module's main.tf.
- Variables declared in a module without a default value are required and must be set every time the module is used.  
  > Variables declared in modules that aren't given a default value are required, and
so must be set whenever you use the module.
- A module output is accessed from the calling configuration using the syntax module.<MODULE NAME>.<OUTPUT NAME>, and module outputs are read-only attributes.  
  > You can access a module's output
from the configuration that calls the module through the following syntax:
module.<MODULE NAME>.<OUTPUT NAME>. Module outputs are read-only attributes.
- The root module references a local child module using a relative path in the source argument of a module block.  
  > module "website_s3_bucket" {
  source = "./modules/aws-s3-static-website-bucket"

  bucket_name = "<UNIQUE BUCKET NAME>"

  tags = {
    Terraform   = "true"
    Environment = "dev"
  }
}
- The root module can expose outputs from child modules by referencing them with module.<MODULE NAME>.<OUTPUT NAME>, as shown when wiring VPC subnet IDs and EC2 IPs to root outputs.  
  > output "vpc_public_subnets" {
  description = "IDs of the VPC's public subnets"
  value       = module.vpc.public_subnets
}

output "ec2_instance_public_ips" {
  description = "Public IP addresses of EC2 instances"
  value       = module.ec2_instances[*].public_ip
}
- Both `terraform get` and `terraform init` install and update modules; `terraform init` additionally initialises backends and installs plugins.  
  > Both the terraform get and terraform init
commands will install and update modules. The terraform init command will also
initialize backends and install plugins.
- When installing a local module, Terraform refers directly to its source directory and automatically notices changes without needing to re-run terraform init or terraform get.  
  > When installing a remote module, Terraform will download it into
the .terraform directory in your configuration's root directory. When
installing a local module, Terraform will instead refer directly to the source
directory. Because of this, Terraform will automatically notice changes to
local modules without having to re-run terraform init or terraform get.
- After applying the full stack, you can verify S3 bucket outputs using `terraform output`, and the bucket domain name is shown in that output.  
  > The website domain was shown when you last ran terraform apply, or whenever
you run terraform output.
- Before running terraform destroy, any files uploaded to an S3 bucket must first be deleted (e.g. with the AWS CLI), otherwise destruction will fail.  
  > If you have uploaded files to your bucket, you will need to delete them before
the bucket can be destroyed. For example, you could run:
$ aws s3 rm s3://$(terraform output -raw website_bucket_name)/ --recursive
- The storage module's main.tf uses input variables (var.bucket_name, var.tags) to configure the S3 bucket resource, demonstrating how input variables wire the calling module's values into child module resources.  
  > resource "aws_s3_bucket" "s3_bucket" {
  bucket = var.bucket_name

  tags = var.tags
}
- The storage module exposes bucket ARN, name (id), and website domain as outputs so the root module and other modules can consume them.  
  > output "arn" {
  description = "ARN of the bucket"
  value       = aws_s3_bucket.s3_bucket.arn
}

output "name" {
  description = "Name (id) of the bucket"
  value       = aws_s3_bucket.s3_bucket.id
}

output "domain" {
  description = "Domain name of the bucket"
  value       = aws_s3_bucket_website_configuration.s3_bucket.website_domain
}
- The tags variable in the storage module has a default value of an empty map, making it optional when calling the module.  
  > variable "tags" {
  description = "Tags to set on the bucket."
  type        = map(string)
  default     = {}
}
- Outputs are the only supported way for users to get information about resources configured inside a module.  
  > You should also consider which values to add as outputs, since outputs are the
only supported way for users to get information about resources configured by
the module.
- A typical Terraform module file structure includes LICENSE, README.md, main.tf, variables.tf, and outputs.tf, though none of these files are required or have special meaning to Terraform.  
  > A typical file structure for a new module is:
.
├── LICENSE
├── README.md
├── main.tf
├── variables.tf
├── outputs.tf
None of these files are required, or have any special meaning to Terraform when
it uses your module.
- Terraform treats any local directory referenced in the source argument of a module block as a module.  
  > Terraform treats any local directory referenced in the source argument of a
module block as a module.
- The terraform.tfstate and terraform.tfstate.backup files contain Terraform state and are how Terraform keeps track of the relationship between configuration and provisioned infrastructure; they should not be distributed as part of a module.  
  > terraform.tfstate and terraform.tfstate.backup: These files contain your
Terraform state, and are how Terraform keeps track of the relationship between
your configuration and the infrastructure provisioned by it.
- The .terraform directory contains modules and plugins used to provision infrastructure and should not be distributed as part of a module.  
  > .terraform: This directory contains the modules and plugins used to
provision your infrastructure. These files are specific to a specific instance
of Terraform when provisioning infrastructure, not the configuration of the
infrastructure defined in .tf files.
- Both the terraform get and terraform init commands install and update modules; terraform init also initializes backends and installs plugins.  
  > Whenever you add a new module to a configuration, Terraform must install the
module before it can be used. Both the terraform get and terraform init
commands will install and update modules. The terraform init command will also
initialize backends and install plugins.
- The root module's outputs.tf can reference child module outputs to expose them, for example referencing module.website_s3_bucket.arn to surface the S3 bucket ARN.  
  > output "website_bucket_arn" {
  description = "ARN of the bucket"
  value       = module.website_s3_bucket.arn
}

output "website_bucket_name" {
  description = "Name (id) of the bucket"
  value       = module.website_s3_bucket.name
}

output "website_bucket_domain" {
  description = "Domain name of the bucket"
  value       = module.website_s3_bucket.domain
}
- An S3 static website module requires resources for the bucket itself, website configuration (index and error documents), ACL, and bucket policy to make objects publicly readable.  
  > resource "aws_s3_bucket" "s3_bucket" {
  bucket = var.bucket_name

  tags = var.tags
}

resource "aws_s3_bucket_website_configuration" "s3_bucket" {
  bucket = aws_s3_bucket.s3_bucket.id

  index_document {
    suffix = "index.html"
  }

  error_document {
    key = "error.html"
  }
}

resource "aws_s3_bucket_acl" "s3_bucket" {
  bucket = aws_s3_bucket.s3_bucket.id

  acl = "public-read"
}

resource "aws_s3_bucket_policy" "s3_bucket" {
  bucket = aws_s3_bucket.s3_bucket.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "PublicReadGetObject"
        Effect    = "Allow"
        Principal = "*"
        Action    = "s3:GetObject"
        Resource = [
          aws_s3_bucket.s3_bucket.arn,
          "${aws_s3_bucket.s3_bucket.arn}/*",
        ]
      },
    ]
  })
}
- Running terraform init on the example repository downloads named provider and module versions, including the AWS provider at v4.49.0.  
  > - Reusing previous version of hashicorp/aws from the dependency lock file
- Installing hashicorp/aws v4.49.0...
- Installed hashicorp/aws v4.49.0 (signed by HashiCorp)

Terraform has been successfully initialized!
- After running terraform apply and confirming the prompt with 'yes', resources including the S3 bucket are provisioned.  
  > Do you want to perform these actions?
  Terraform will perform the actions described above.
  Only 'yes' will be accepted to approve.

  Enter a value:
- Running terraform destroy removes all managed resources; it shows a plan of what will be destroyed and requires confirming with 'yes'.  
  > Do you really want to destroy all resources?
  Terraform will destroy all your managed infrastructure, as shown above.
  There is no undo. Only 'yes' will be accepted to confirm.

  Enter a value: yes
- The terraform destroy output lists all resources that will be removed, including their current attribute values, and ends with a count of destroyed resources.  
  > Plan: 0 to add, 0 to change, 26 to destroy.

Changes to Outputs:
  - ec2_instance_public_ips = [
      - "34.209.188.84",
      - "18.236.69.92",
    ] -> null
  - vpc_public_subnets      = [
      - "subnet-035b78336fdc48d7c",
      - "subnet-06b1eb0de498734e1",
    ] -> null
  - website_bucket_arn      = "arn:aws:s3:::robin-example-2021-01-25" -> null
  - website_bucket_domain   = "s3-website-us-west-2.amazonaws.com" -> null
  - website_bucket_name     = "robin-example-2021-01-25" -> null
- Secret information such as passwords or access keys may appear in terraform.tfstate, .tfvars, and related files, so committing them to a public version control system is a security risk.  
  > The files mentioned above will often include secret information
such as passwords or access keys, which will become public if those files are
committed to a public version control system such as GitHub.
- A local subdirectory module for S3 static website hosting is structured inside a modules/ subdirectory of the root configuration directory.  
  > .
├── LICENSE
├── README.md
├── main.tf
├── modules
│   └── aws-s3-static-website-bucket
├── outputs.tf
├── terraform.tfstate
├── terraform.tfstate.backup
└── variables.tf
- When Terraform is reinitialized after adding a module or changing backend/provider configuration, it downloads the updated dependencies; the output reminds users to rerun terraform init if they forget.  
  > If you ever set or change modules or backend configuration for Terraform,
rerun this command to reinitialize your working directory. If you forget, other
commands will detect it and remind you to do so if necessary.

## [https://developer.hashicorp.com/terraform/language/modules/develop/composition](https://developer.hashicorp.com/terraform/language/modules/develop/composition)

official, fetched 2026-09-28

- Module composition is the flat style of passing outputs from one module as inputs to another, rather than embedding dependencies inside a module.  
  > We call this flat style of module usage module composition, because it takes multiple composable building-block modules and assembles them together to produce a larger system.
- In a root module, outputs from a networking module (such as vpc_id and subnet_ids) are passed as input variables to dependent modules like a compute module.  
  > module "network" {
  source = "./modules/aws-network"

  base_cidr_block = "10.0.0.0/8"
}

module "consul_cluster" {
  source = "./modules/aws-consul-cluster"

  vpc_id     = module.network.vpc_id
  subnet_ids = module.network.subnet_ids
}
- Terraform strongly recommends keeping the module tree flat with only one level of child modules, using expressions to describe relationships between modules.  
  > in most cases we strongly recommend keeping the module tree flat, with only one level of child modules, and use a technique similar to the above of using expressions to describe the relationships between the modules
- The dependency inversion pattern means a module receives its dependencies (such as VPC and subnet IDs) from the root module rather than creating them itself, making the module reusable and flexible.  
  > Instead of a module embedding its dependencies, creating and managing its own copy, the module receives its dependencies from the root module, which can therefore connect the same modules in different ways to produce different results.
- A networking module's outputs (vpc_id and subnet_ids) can also be sourced from data sources instead of a sibling module, without changing the compute module that consumes them.  
  > data "aws_vpc" "main" {
  tags = {
    Environment = "production"
  }
}

data "aws_subnet_ids" "main" {
  vpc_id = data.aws_vpc.main.id
}

module "consul_cluster" {
  source = "./modules/aws-consul-cluster"

  vpc_id     = data.aws_vpc.main.id
  subnet_ids = data.aws_subnet_ids.main.ids
}
- A module input variable can be typed as an object using only the subset of attributes the module needs; Terraform will accept any object that has at least those attributes.  
  > variable "ami" {
  type = object({
    # Declare an object using only the subset of attributes the module
    # needs. Terraform will allow any object that has at least these
    # attributes.
    id           = string
    architecture = string
  })
}
- A precondition block inside an output can enforce guarantees about resources, such as requiring an EBS root volume to be encrypted, and returns a custom error_message if the condition is false.  
  > output "api_base_url" {
  value = "https://${aws_instance.example.private_dns}:8433/"

  # The EC2 instance must have an encrypted root volume.
  precondition {
    condition     = data.aws_ebs_volume.example.encrypted
    error_message = "The server's root volume is not encrypted."
  }
}
- Cross-module dependencies are expressed by referencing one module's outputs directly in another module's input arguments using the module.<name>.<output> syntax.  
  > subnet_ids = module.network.aws_subnet_ids
- A data-only module contains no resource blocks and only uses data sources to retrieve information about existing infrastructure, such as a shared VPC, for use by other modules.  
  > It may sometimes be useful to write modules that do not describe any new infrastructure at all, but merely retrieve information about existing infrastructure that was created elsewhere using data sources.
- A data-only network module can retrieve shared network information via aws_vpc and aws_subnet_ids data sources, consul_keys, or terraform_remote_state, and the source can change without updating every consuming module.  
  > it could query the AWS API directly using aws_vpc and aws_subnet_ids data sources, or it could read saved information from a Consul cluster using consul_keys, or it might read the outputs directly from the state of the configuration that manages the network using terraform_remote_state.
- cidrsubnet() can be used to derive a subnet CIDR block from a VPC's CIDR block when defining aws_subnet resources.  
  > cidr_block = cidrsubnet(aws_vpc.example.cidr_block, 4, 1)

## [https://docs.localstack.cloud/aws/connecting/infrastructure-as-code/terraform/](https://docs.localstack.cloud/aws/connecting/infrastructure-as-code/terraform/)

community, fetched 2026-09-28

- LocalStack supports Terraform via the AWS provider through custom service endpoints, allowing you to run Terraform against local AWS emulation.  
  > LocalStack supports Terraform via the AWS provider through custom service endpoints.
- The lstk terraform command (alias lstk tf) automatically configures AWS provider service endpoints by creating a temporary override file called localstack_providers_override.tf, then forwards arguments to the real terraform binary.  
  > lstk terraform (alias lstk tf) runs Terraform against LocalStack. It uses the Terraform Override mechanism and creates a temporary file localstack_providers_override.tf to configure the endpoints for the AWS provider section, then forwards your arguments to the real terraform binary.
- All LocalStack service endpoints are configured to point to http://localhost:4566 by default.  
  > The endpoints for all services are configured to point to the LocalStack API (http://localhost:4566 by default).
- A minimal Terraform S3 bucket resource block requires only the bucket name as an argument.  
  > resource "aws_s3_bucket" "test-bucket" {
  bucket = "my-bucket"
}
- When manually configuring the AWS provider for LocalStack, mock credential values (e.g. 'test') are used for access_key and secret_key, along with a chosen region.  
  > provider "aws" {
  access_key = "test"
  secret_key = "test"
  region     = "us-east-1"
}
- Setting skip_credentials_validation = true and skip_metadata_api_check = true in the AWS provider block prevents unnecessary routing and authentication checks when targeting LocalStack.  
  > provider "aws" {
  access_key                  = "test"
  secret_key                  = "test"
  region                      = "us-east-1"

  skip_credentials_validation = true
  skip_metadata_api_check     = true
}
- Service endpoints for the AWS provider can be configured inside an endpoints block within the provider block, pointing each service to the LocalStack URL.  
  > endpoints {
    s3 = "http://s3.localhost.localstack.cloud:4566"
  }
- The S3 endpoint should use the s3.localhost.localstack.cloud hostname to support virtual-hosted-style addressing; if that DNS cannot resolve, http://localhost:4566 with s3_use_path_style = true can be used as a fallback.  
  > If you cannot resolve this DNS record, you can use http://localhost:4566 as a fallback and enable path-style addressing by adding s3_use_path_style = true to the provider configuration.
- A complete minimal manual AWS provider configuration for LocalStack includes mock credentials, a region, skip flags, and an endpoints block pointing S3 to LocalStack.  
  > provider "aws" {
  access_key                  = "mock_access_key"
  secret_key                  = "mock_secret_key"
  region                      = "us-east-1"

  skip_credentials_validation = true
  skip_metadata_api_check     = true

  endpoints {
    s3 = "http://s3.localhost.localstack.cloud:4566"
  }
}

resource "aws_s3_bucket" "test-bucket" {
  bucket = "my-bucket"
}
- Provider endpoint configuration can be stored in a separate file named provider.tf, which Terraform will include automatically as part of the configuration.  
  > You can save the following configuration in a file named provider.tf and include it in your Terraform configuration.
- Many AWS services — including EC2, IAM, Lambda, S3, SQS, SNS, DynamoDB, RDS, and others — can each be pointed to LocalStack by listing them individually in the provider's endpoints block.  
  > endpoints {
    apigateway     = "http://localhost:4566"
    apigatewayv2   = "http://localhost:4566"
    cloudformation = "http://localhost:4566"
    cloudwatch     = "http://localhost:4566"
    dynamodb       = "http://localhost:4566"
    ec2            = "http://localhost:4566"
    es             = "http://localhost:4566"
    elasticache    = "http://localhost:4566"
    firehose       = "http://localhost:4566"
    iam            = "http://localhost:4566"
    kinesis        = "http://localhost:4566"
    lambda         = "http://localhost:4566"
    rds            = "http://localhost:4566"
    redshift       = "http://localhost:4566"
    route53        = "http://localhost:4566"
    s3             = "http://s3.localhost.localstack.cloud:4566"
    secretsmanager = "http://localhost:4566"
    ses            = "http://localhost:4566"
    sns            = "http://localhost:4566"
    sqs            = "http://localhost:4566"
    ssm            = "http://localhost:4566"
    stepfunctions  = "http://localhost:4566"
    sts            = "http://localhost:4566"
  }
- You can detect whether Terraform is running against LocalStack by checking if the AWS account ID equals 000000000000, which is LocalStack's default account ID.  
  > data "aws_caller_identity" "current" {}

output "is_localstack" {
  value = data.aws_caller_identity.current.id == "000000000000"
}
- Setting the LSTK_TF_DRY_RUN environment variable causes lstk terraform to generate the provider override file without actually running Terraform.  
  > LSTK_TF_DRY_RUN   -   When set, generate the override file but do not run Terraform
- The S3 endpoint for LocalStack should use the s3.localhost.localstack.cloud hostname to support virtual-hosted-style addressing; if that DNS record cannot be resolved, use http://localhost:4566 and add s3_use_path_style = true to the provider block.  
  > The S3 endpoint uses the s3.localhost.localstack.cloud hostname to support virtual-hosted-style addressing, which AWS recommends and some regions require.
If you cannot resolve this DNS record, you can use http://localhost:4566 as a fallback and enable path-style addressing by adding s3_use_path_style = true to the provider configuration.
- A complete minimal AWS provider block for LocalStack with manual configuration includes mock credentials, region, skip flags, and an endpoints block pointing S3 to the LocalStack virtual-hosted endpoint.  
  > provider "aws" {
  access_key                  = "mock_access_key"
  secret_key                  = "mock_secret_key"
  region                      = "us-east-1"

  skip_credentials_validation = true
  skip_metadata_api_check     = true

  endpoints {
    s3 = "http://s3.localhost.localstack.cloud:4566"
  }
}
- The LSTK_TF_CMD environment variable lets you specify an alternative Terraform binary (e.g., tofu for OpenTofu) that lstk terraform will invoke.  
  > LSTK_TF_CMD terraform Binary to invoke, e.g. tofu
- You can detect whether Terraform is running against LocalStack by checking if the AWS account ID equals 000000000000, which is LocalStack's default account ID.  
  > data "aws_caller_identity" "current" {}
output "is_localstack" {
  value = data.aws_caller_identity.current.id == "000000000000"
}
- OpenTofu is an open-source fork of Terraform compatible with Terraform versions 1.5.x and most of 1.6.x, and can be used as a drop-in replacement with LocalStack configurations.  
  > OpenTofu is an open-source fork of Terraform acting as a drop-in replacement for Terraform, as it's compatible with Terraform versions 1.5.x and most of 1.6.x.
- The LSTK_TF_DRY_RUN environment variable, when set, causes lstk terraform to generate the provider override file without actually running Terraform.  
  > LSTK_TF_DRY_RUN - When set, generate the override file but do not run Terraform
- The override file name used by lstk terraform defaults to localstack_providers_override.tf but can be changed via the LSTK_TF_OVERRIDE_FILE_NAME environment variable.  
  > LSTK_TF_OVERRIDE_FILE_NAME localstack_providers_override.tf Override file name

## [https://developer.hashicorp.com/terraform/language/functions/cidrsubnet](https://developer.hashicorp.com/terraform/language/functions/cidrsubnet)

official, fetched 2026-09-28

- The cidrsubnet function signature takes three arguments: a prefix in CIDR notation, newbits (additional bits to extend the prefix), and netnum (the subnet number to encode into the new bits).  
  > cidrsubnet(prefix, newbits, netnum)
- The newbits argument specifies how many additional bits are added to the prefix length; for example, a /16 prefix with newbits=4 produces a /20 subnet.  
  > newbits is the number of additional bits with which to extend the prefix. For example, if given a prefix ending in /16 and a newbits value of 4, the resulting subnet address will have length /20.
- The netnum argument must be representable as a binary integer with no more than newbits digits, and its value is encoded into the additional bits added to the prefix.  
  > netnum is a whole number that can be represented as a binary integer with no more than newbits binary digits, which will be used to populate the additional bits added to the prefix.
- cidrsubnet accepts both IPv4 and IPv6 prefixes, and the result always uses the same addressing scheme as the input prefix.  
  > This function accepts both IPv6 and IPv4 prefixes, and the result always uses the same addressing scheme as the given prefix.
- Calling cidrsubnet with a /24 prefix and newbits=4 produces a /28 subnet (24 + 4 = 28 bits).  
  > cidrsubnet("10.1.2.0/24", 4, 15)
10.1.2.240/28
- cidrsubnet with a /12 prefix, newbits=4, and netnum=2 returns 172.18.0.0/16.  
  > > cidrsubnet("172.16.0.0/12", 4, 2)
172.18.0.0/16
- cidrsubnet works with IPv6 prefixes; for example, a /56 prefix with newbits=16 and netnum=162 yields a /72 subnet.  
  > > cidrsubnet("fd00:fd12:3456:7890::/56", 16, 162)
fd00:fd12:3456:7800:a200::/72
- Unlike cidrsubnets, cidrsubnet lets you specify an explicit network number (netnum) for the subnet rather than automatically numbering from zero.  
  > Unlike the related function cidrsubnets, cidrsubnet allows you to give a specific network number to use. cidrsubnets can allocate multiple network addresses at once, but numbers them automatically starting with zero.
- cidrsubnet creates a new network prefix (subnet) within a given parent network prefix, whereas the related cidrhost function calculates a single host IP address within a network.  
  > While cidrhost allows calculating single host IP addresses, cidrsubnet on the other hand creates a new network prefix within the given network prefix. In other words, it creates a subnet.
- After using cidrsubnet to derive a subnet, you can use cidrhost to calculate individual host addresses within that subnet by passing a host number between 1 and the maximum usable hosts.  
  > You can thus use cidrhost function to calculate those host addresses by providing it a value between 1 and 14:
> cidrhost("10.1.2.240/28", 1)
10.1.2.241
> cidrhost("10.1.2.240/28", 14)
10.1.2.254
- IPv4 address octets with leading zeros are interpreted as decimal (not octal) by cidrsubnet; this is a preserved historical behaviour and relying on it is not recommended.  
  > this function interprets IPv4 address octets that have leading zeros as decimal numbers, which is contrary to some other systems which interpret them as octal. We have preserved this behavior for backward compatibility, but recommend against relying on this behavior.
- The prefix argument to cidrsubnet must be supplied in CIDR notation, as defined in RFC 4632 section 3.1.  
  > prefix must be given in CIDR notation, as defined in RFC 4632 section 3.1.
- Calling cidrsubnet with a /24 prefix and newbits=4 produces a /28 subnet because 24 + 4 = 28.  
  > in our example here we specified 4, which means that the resulting subnet will have a prefix length of 24 + 4 = 28 bits.
- Example: cidrsubnet("10.1.2.0/24", 4, 15) returns 10.1.2.240/28.  
  > > cidrsubnet("10.1.2.0/24", 4, 15)
10.1.2.240/28
- The related function cidrnetmask converts an IPv4 network prefix in CIDR notation into netmask notation.  
  > cidrnetmask converts an IPv4 network prefix in CIDR notation into netmask notation.
- The resulting subnet from cidrsubnet("10.1.2.0/24", 4, 15) has 4 bits for host numbering, yielding 14 usable host addresses (subtracting the network address and broadcast address).  
  > The new subnet has four bits available for host numbering, which means that there are 14 host addresses available for assignment once we subtract the network's own address and the broadcast address.

## [https://docs.aws.amazon.com/prescriptive-guidance/latest/secure-sensitive-data-secrets-manager-terraform/terraform-state-file.html](https://docs.aws.amazon.com/prescriptive-guidance/latest/secure-sensitive-data-secrets-manager-terraform/terraform-state-file.html)

community, fetched 2026-09-28

- The Terraform state file (tfstate) is typically a plain text file that contains data about Terraform deployments, including any sensitive and non-sensitive data about the deployed infrastructure.  
  > Typically, this is a plain text file that contains data about Terraform deployments, and it includes any sensitive and non-sensitive data about the deployed infrastructure.
- Sensitive data is visible in plain text in the Terraform state file, making it important to protect.  
  > Sensitive data is visible in plain text in the Terraform state file.
- A recommended way to protect the Terraform state file is to store it in an Amazon S3 bucket in a centralized AWS account, with bucket policies that restrict access to it.  
  > Store the Terraform state file in the centralized AWS account where you operate Secrets Manager. Store the file in an Amazon Simple Storage Service (Amazon S3) bucket, and configure policies that restrict access to it.
- The Terraform state can be locked to help prevent corruption, using the Amazon S3 backend.  
  > You can lock the Terraform state in order to help prevent corruption. For more information about locking the state and protecting the state file, see Amazon S3 backend in the Terraform documentation.

## [https://docs.aws.amazon.com/prescriptive-guidance/latest/terraform-aws-provider-best-practices/security.html](https://docs.aws.amazon.com/prescriptive-guidance/latest/terraform-aws-provider-best-practices/security.html)

community, fetched 2026-09-28

- The AWS provider block supports an assume_role sub-block where you can specify role_arn and session_name so Terraform authenticates by assuming an IAM role instead of using static credentials.  
  > provider "aws" {
  assume_role {
    role_arn     = "arn:aws:iam::111122223333:role/terraform-execution"
    session_name = "terraform-session-example"
  }
}
- When running Terraform locally, you can obtain short-lived credentials by running 'aws sts assume-role' with a role ARN and session name, and the output contains an AccessKeyId, SecretAccessKey, and SessionToken that expire after the session's maximum duration.  
  > aws sts assume-role --role-arn arn:aws:iam::111122223333:role/terraform-execution --role-session-name terraform-session-example
- The credentials returned by aws sts assume-role include a SecretAccessKey, SessionToken, Expiration timestamp, and AccessKeyId that can be used to authenticate Terraform to AWS.  
  > "Credentials": {
        "SecretAccessKey": " wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        "SessionToken": " AQoEXAMPLEH4aoAH0gNCAPyJxz4BlCFFxWNE1OPTgk5TthT+FvwqnKwRcOIfrRh3c/LTo6UDdyJwOOvEVPvLXCrrrUtdnniCEXAMPLE/IvU1dYUg2RVAJBanLiHb4IgRmpRV3zrkuWJOgQs8IZZaIv2BXIa2R4OlgkBN9bkUDNCJiBeb/AXlzBBko7b15fjrBs2+cTQtpZ3CYWFXG8C5zqx37wnOE49mRl/+OtkIKGO7fAE",
        "Expiration": "2024-03-15T00:05:07Z",
        "AccessKeyId": "ASIAIOSFODNN7EXAMPLE"
    }
- Terraform's state file keeps track of the resources provisioned by Terraform and their metadata, and is crucial for Terraform's ability to manage infrastructure.  
  > The state file is crucial because it keeps track of the resources that are provisioned by Terraform and their metadata.
- Failure to secure remote state can lead to loss of state data, inability to manage infrastructure, inadvertent resource deletion, and exposure of sensitive information that may be present in the state file.  
  > Failure to secure remote state can lead to serious issues such as loss of state data, inability to manage infrastructure, inadvertent resource deletion, and exposure of sensitive information that might be present in the state file.
- The recommended alternative to local state storage is remote state storage — storing the Terraform state file remotely rather than on the local machine where Terraform runs.  
  > Remote state storage refers to storing the Terraform state file remotely instead of locally on the machine where Terraform is running.
- Amazon S3 server-side encryption (SSE) should be used to encrypt remote Terraform state at rest.  
  > Use Amazon Simple Storage Service (Amazon S3) server-side encryption (SSE) to encrypt remote state at rest.
- Collaboration workflows for Terraform state should be structured in HCP Terraform or a CI/CD pipeline to limit direct state access, rather than allowing team members to access state files directly.  
  > Structure collaboration workflows in HCP Terraform or in a CI/CD pipeline within your Git repository to limit direct state access.
- Many Terraform resources and data sources store secret values in plaintext in the state file, so secrets should be managed with AWS Secrets Manager rather than stored in state.  
  > There are many resources and data sources in Terraform that store secret values in plaintext in the state file. Avoid storing secrets in state―use AWS Secrets Manager instead.
- When exporting sensitive values as Terraform outputs, the values must be marked as sensitive to prevent them from being displayed in plaintext.  
  > When exporting sensitive values to output, make sure that the values are marked as sensitive.

## [https://docs.aws.amazon.com/cli/latest/reference/ec2/describe-vpcs.html](https://docs.aws.amazon.com/cli/latest/reference/ec2/describe-vpcs.html)

community, fetched 2026-09-28

- To list all VPCs in your account using the AWS CLI, run `aws ec2 describe-vpcs` with no additional arguments.  
  > aws ec2 describe-vpcs
- To retrieve details for a specific VPC by ID, pass the --vpc-ids flag to the describe-vpcs command.  
  > aws ec2 describe-vpcs \
    --vpc-ids vpc-06e4ab6c6cEXAMPLE
- The describe-vpcs command returns VPC attributes including CidrBlock, VpcId, State, OwnerId, InstanceTenancy, IsDefault, and Tags in a JSON structure.  
  > {
    "Vpcs": [
        {
            "CidrBlock": "30.1.0.0/16",
            "DhcpOptionsId": "dopt-19edf471",
            "State": "available",
            "VpcId": "vpc-0e9801d129EXAMPLE",
            "OwnerId": "111122223333",
            "InstanceTenancy": "default",
- The --filters option on describe-vpcs allows filtering by criteria such as cidr, state, is-default, vpc-id, and tag key/value combinations.  
  > cidr - The primary IPv4 CIDR block of the VPC. The CIDR block you specify must exactly match the VPC's CIDR block for information to be returned for the VPC. Must contain the slash followed by one or two digits (for example, /28 ).
- When filtering with multiple values for a single filter, the values are combined with OR logic; when specifying multiple filters, they are combined with AND logic.  
  > If you specify multiple filters, the filters are joined with an AND , and the request returns only results that match all of the specified filters.
- The describe-vpcs command is paginated; you can disable automatic pagination with --no-paginate to retrieve only the first page of results.  
  > describe-vpcs is a paginated operation. Multiple API calls may be issued in order to retrieve the entire data set of results. You can disable pagination by providing the --no-paginate argument.
- A VPC's state can be pending, available, or deleting, as shown in the describe-vpcs output schema.  
  > State -> (string)
The current state of the VPC.
Possible values:
pending
available
deleting
- The --region global option overrides the configured default region for a single AWS CLI command.  
  > --region (string)
The region to use. Overrides config/env settings.
- The --endpoint-url global option overrides the command's default AWS endpoint URL, which can be used to point the CLI at a local endpoint such as LocalStack.  
  > --endpoint-url (string)
Override command's default URL with the given URL.
- The --no-sign-request global option prevents the AWS CLI from loading credentials and signing requests, useful for unauthenticated or mock endpoints.  
  > --no-sign-request (boolean)
Do not sign requests. Credentials will not be loaded if this argument is provided.
- The --profile global option directs the AWS CLI to use a named profile from the credentials file, enabling multiple credential sets to be managed locally.  
  > --profile (string)
Use a specific profile from your credential file.
- The --query global option accepts a JMESPath expression to filter and reshape AWS CLI response data directly in the terminal.  
  > --query (string)
A JMESPath query to use in filtering the response data.
- The describe-vpcs output includes a CidrBlockAssociationSet showing each IPv4 CIDR block associated with the VPC along with its association state.  
  > "CidrBlockAssociationSet": [
                {
                    "AssociationId": "vpc-cidr-assoc-00b17b4eddEXAMPLE",
                    "CidrBlock": "10.0.0.0/16",
                    "CidrBlockState": {
                        "State": "associated"
                    }
                }
            ]

## [https://docs.aws.amazon.com/cli/latest/reference/ec2/describe-instances.html](https://docs.aws.amazon.com/cli/latest/reference/ec2/describe-instances.html)

community, fetched 2026-09-28

- You can verify EC2 instances provisioned by Terraform by running the AWS CLI command `aws ec2 describe-instances` with the `--instance-ids` flag.  
  > aws ec2 describe-instances \
    --instance-ids i-1234567890abcdef0
- The `describe-instances` output includes the `SubnetId` and `VpcId` fields for each instance, which can be used to verify that an EC2 instance was placed into the correct VPC and subnet created by the networking module.  
  > "SubnetId": "subnet-04a636d18e83cfacb",
                    "VpcId": "vpc-1234567890abcdef0"
- The `describe-instances` output includes `AvailabilityZone` under `Placement`, allowing you to confirm that instances were launched across the correct availability zones as configured in the networking module.  
  > "Placement": {
                        "AvailabilityZone": "us-east-2a",
                        "GroupName": "",
                        "Tenancy": "default"
                    }
- You can use the `--filters` option with `Name=instance-type,Values=...` to scope `describe-instances` results to a specific instance type, useful for verifying the instance type passed via the compute module's input variable.  
  > aws ec2 describe-instances \
    --filters Name=instance-type,Values=m5.large
- You can filter `describe-instances` results by multiple criteria simultaneously (e.g., instance type and Availability Zone) by specifying multiple `--filters` arguments.  
  > aws ec2 describe-instances \
    --filters Name=instance-type,Values=t2.micro,t3.micro Name=availability-zone,Values=us-east-2c
- You can filter instances by a specific tag key-value pair using the `tag:<key>` filter syntax, which is useful for verifying resources tagged by Terraform (e.g., Name tags applied to EC2 instances).  
  > aws ec2 describe-instances \
    --filters "Name=tag:Owner,Values=my-team"
- The `--query` parameter accepts a JMESPath expression and can be combined with `--output` to extract specific fields (such as InstanceId and SubnetId) from `describe-instances` output, making it easier to verify Terraform-provisioned resources.  
  > aws ec2 describe-instances \
    --query 'Reservations[*].Instances[*].{Instance:InstanceId,Subnet:SubnetId}' \
    --output json
- The `--dry-run` flag on `describe-instances` checks whether you have the required permissions without actually making the request, returning `DryRunOperation` if permissions are present or `UnauthorizedOperation` if not.  
  > --dry-run | --no-dry-run (boolean)
Checks whether you have the required permissions for the operation, without actually making the request, and provides an error response. If you have the required permissions, the error response is DryRunOperation . Otherwise, it is UnauthorizedOperation .
- The `--region` global option on any AWS CLI command overrides the region configured in the profile or environment, allowing verification of resources across specific AWS regions.  
  > --region (string)
The region to use. Overrides config/env settings.
- The `describe-instances` output shows the `InstanceType` field for each instance, confirming the instance type that was passed as an input variable to the compute module.  
  > "InstanceType": "t3.nano"
- Filters passed to `describe-instances` can also be supplied via a JSON file using the `file://` syntax, which is useful for complex multi-criteria verification queries.  
  > aws ec2 describe-instances \
    --filters file://filters.json
- The `describe-instances` output includes block device mapping details such as `VolumeId` and `DeleteOnTermination`, which can be used to verify EBS volumes provisioned by the storage module.  
  > "BlockDeviceMappings": [
                        {
                            "DeviceName": "/dev/xvda",
                            "Ebs": {
                                "AttachTime": "2022-11-15T10:49:00+00:00",
                                "DeleteOnTermination": true,
                                "Status": "attached",
                                "VolumeId": "vol-02e6ccdca7de29cf2"
                            }
                        }
                    ]

## [https://docs.aws.amazon.com/cli/latest/reference/s3/ls.html](https://docs.aws.amazon.com/cli/latest/reference/s3/ls.html)

community, fetched 2026-09-28

- Running `aws s3 ls` with no arguments lists all S3 buckets owned by the authenticated user, showing each bucket's creation timestamp and name.  
  > The following ls command lists all of the buckets owned by the user.  In this example, the user owns the buckets amzn-s3-demo-bucket and amzn-s3-demo-bucket2.  The timestamp is the date the bucket was created, shown in your machine's time zone.
- Running `aws s3 ls s3://<bucket-name>` lists all objects and common prefixes (folders) inside a specific S3 bucket.  
  > aws s3 ls s3://amzn-s3-demo-bucket
- Adding `--recursive` to `aws s3 ls` lists every object in a bucket in full path order rather than showing common prefixes as PRE entries.  
  > The following ls command will recursively list objects in a bucket.  Rather than showing PRE dirname/ in the output, all the content in a bucket will be listed in order.

## [https://docs.aws.amazon.com/code-library/latest/ug/cli_2_ec2_code_examples.html](https://docs.aws.amazon.com/code-library/latest/ug/cli_2_ec2_code_examples.html)

community, fetched 2026-09-28

- You can verify that an EC2 instance exists and is running by using the AWS CLI (e.g., aws ec2 describe-instances or related commands), which supports the 'verify resources in the AWS console or CLI' step after a Terraform apply.  
  > The following code examples show you how to perform actions and implement common scenarios by using the AWS Command Line Interface with Amazon EC2.
- An internet gateway can be attached to a VPC using the AWS CLI command aws ec2 attach-internet-gateway, specifying --internet-gateway-id and --vpc-id.  
  > aws ec2 attach-internet-gateway \
    --internet-gateway-id igw-0d0fb496b3EXAMPLE \
    --vpc-id vpc-0a60eb65b4EXAMPLE
- A route table can be associated with a subnet via the AWS CLI using aws ec2 associate-route-table with --route-table-id and --subnet-id arguments.  
  > aws ec2 associate-route-table --route-table-id rtb-22574640 --subnet-id subnet-9d4a7b6c
- An EBS volume can be attached to an EC2 instance using aws ec2 attach-volume, specifying the volume ID, instance ID, and device name (e.g., /dev/sdf).  
  > aws ec2 attach-volume --volume-id vol-1234567890abcdef0 --instance-id i-01474ef662b89480 --device /dev/sdf
- After attaching a volume to an EC2 instance, the AWS CLI returns the attachment state as 'attaching', confirming the operation was accepted.  
  > {
    "AttachTime": "YYYY-MM-DDTHH:MM:SS.000Z",
    "InstanceId": "i-01474ef662b89480",
    "VolumeId": "vol-1234567890abcdef0",
    "State": "attaching",
    "Device": "/dev/sdf"
}
- A security group ingress rule allowing inbound SSH (TCP port 22) from a CIDR range can be added using aws ec2 authorize-security-group-ingress with --group-id, --protocol, --port, and --cidr.  
  > aws ec2 authorize-security-group-ingress \
    --group-id sg-1234567890abcdef0 \
    --protocol tcp \
    --port 22 \
    --cidr 203.0.113.0/24
- A security group egress rule allowing outbound TCP traffic to a specific CIDR block can be added using aws ec2 authorize-security-group-egress with --group-id and --ip-permissions.  
  > aws ec2 authorize-security-group-egress \
    --group-id sg-1234567890abcdef0 \
    --ip-permissions 'IpProtocol=tcp,FromPort=80,ToPort=80,IpRanges=[{CidrIp=10.0.0.0/16}]'
- An Elastic IP address can be allocated from Amazon's address pool using aws ec2 allocate-address, which returns a PublicIp and AllocationId.  
  > aws ec2 allocate-address

Output:
{
    "PublicIp": "70.224.234.241",
    "AllocationId": "eipalloc-01435ba59eEXAMPLE",
    "PublicIpv4Pool": "amazon",
    "NetworkBorderGroup": "us-west-2",
    "Domain": "vpc"
}
- An Elastic IP address can be associated with an EC2 instance via the CLI using aws ec2 associate-address with --instance-id and --allocation-id.  
  > aws ec2 associate-address \
    --instance-id i-0b263919b6498b123 \
    --allocation-id eipalloc-64d5890a
- An IPv6 CIDR block can be associated with a subnet using aws ec2 associate-subnet-cidr-block, providing the subnet ID and the IPv6 CIDR block.  
  > aws ec2 associate-subnet-cidr-block --subnet-id subnet-5f46ec3b --ipv6-cidr-block 2001:db8:1234:1a00::/64
- An additional IPv4 CIDR block can be associated with a VPC using aws ec2 associate-vpc-cidr-block, specifying --vpc-id and --cidr-block.  
  > aws ec2 associate-vpc-cidr-block \
    --vpc-id vpc-1EXAMPLE \
    --cidr-block 10.2.0.0/16
- A network interface can be attached to a running EC2 instance using aws ec2 attach-network-interface with --network-interface-id, --instance-id, and --device-index.  
  > aws ec2 attach-network-interface \
    --network-interface-id eni-0dc56a8d4640ad10a \
    --instance-id i-1234567890abcdef0 \
    --device-index 1

## [https://developer.hashicorp.com/terraform/tutorials/aws/aws-asg](https://developer.hashicorp.com/terraform/tutorials/aws/aws-asg)

official, fetched 2026-09-28

- The create_before_destroy lifecycle argument instructs Terraform to create a new resource before destroying the original, avoiding service interruptions when a resource must be replaced.  
  > The create_before_destroy argument in the lifecycle block instructs Terraform to create the new version before destroying the original to avoid any service interruptions.
- A launch configuration resource uses a lifecycle block with create_before_destroy set to true to ensure replacement order.  
  > lifecycle {
    create_before_destroy = true
  }
- The aws_autoscaling_group resource accepts min_size, max_size, desired_capacity, launch_configuration, and vpc_zone_identifier arguments.  
  > resource "aws_autoscaling_group" "terramino" {
  min_size             = 1
  max_size             = 3
  desired_capacity     = 1
  launch_configuration = aws_launch_configuration.terramino.name
  vpc_zone_identifier  = module.vpc.public_subnets
}
- The vpc_zone_identifier argument of an aws_autoscaling_group resource can reference subnet outputs from a VPC module, threading networking module outputs into the compute resource.  
  > vpc_zone_identifier  = module.vpc.public_subnets
- An aws_lb_target_group resource references the VPC ID from a module output, demonstrating cross-module dependency wiring.  
  > resource "aws_lb_target_group" "hashicups" {
  name     = "learn-asg-hashicups"
  port     = 80
  protocol = "HTTP"
  vpc_id   = module.vpc.vpc_id
}
- The aws_autoscaling_attachment resource links an Auto Scaling group to a load balancer target group, allowing AWS to automatically add and remove instances from the target group.  
  > resource "aws_autoscaling_attachment" "terramino" {
  autoscaling_group_name = aws_autoscaling_group.terramino.id
  alb_target_group_arn   = aws_lb_target_group.terramino.arn
}
- The aws_lb_listener resource specifies how to handle HTTP requests on a port, forwarding all requests to a target group via a default_action block.  
  > resource "aws_lb_listener" "terramino" {
  load_balancer_arn = aws_lb.terramino.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.terramino.arn
  }
}
- A security group's ingress block can reference another security group as the traffic source, ensuring only traffic forwarded from the load balancer reaches the EC2 instances.  
  > ingress {
    from_port       = 80
    to_port         = 80
    protocol        = "tcp"
    security_groups = [aws_security_group.terramino_lb.id]
  }
- Resource attributes from one resource block can be referenced in another using expressions such as aws_security_group.terramino_lb.id.  
  > security_groups = [aws_security_group.terramino_instance.id]
- Running terraform plan after an out-of-band scaling change shows the drift and proposes to revert desired_capacity back to the value in configuration.  
  > Terraform proposes to scale your instances back down to 1, since your configuration specifies desired_capacity = 1.
- terraform plan reports objects that have changed outside of Terraform since the last apply, flagging state drift before any changes are made.  
  > Note: Objects have changed outside of Terraform

Terraform detected the following changes made outside of Terraform since the
last "terraform apply":
- The ignore_changes lifecycle argument accepts a list of attribute names that Terraform should not attempt to reconcile, preventing it from reverting dynamic changes such as ASG scaling.  
  > lifecycle {
    ignore_changes = [desired_capacity, target_group_arns]
  }
- After adding a lifecycle ignore_changes rule and running terraform apply, Terraform reports no changes if the only difference was in the ignored attributes.  
  > $ terraform apply
No changes. Your infrastructure matches the configuration.
- terraform state list shows all resources Terraform is tracking, including resources inside called modules listed with their module path prefix.  
  > $ terraform state list
data.aws_ami.amazon_linux
data.aws_availability_zones.available
aws_autoscaling_attachment.terramino
aws_autoscaling_group.terramino
aws_launch_configuration.terramino
aws_lb.terramino
aws_lb_listener.terramino
aws_lb_target_group.terramino
aws_security_group.terramino_instance
aws_security_group.terramino_lb
module.vpc.aws_internet_gateway.this[0]
module.vpc.aws_route.public_internet_gateway[0]
module.vpc.aws_route_table.public[0]
module.vpc.aws_route_table_association.public[0]
module.vpc.aws_route_table_association.public[1]
module.vpc.aws_route_table_association.public[2]
module.vpc.aws_subnet.public[0]
module.vpc.aws_subnet.public[1]
module.vpc.aws_subnet.public[2]
module.vpc.aws_vpc.this[0]
- Terraform does not track the individual EC2 instances inside an Auto Scaling group in state; it only tracks the ASG capacity, not its member instances.  
  > Notice that Terraform does not list your ASG's EC2 instances in the state's resources. This is because Terraform is not aware of the member instances of the group, only the capacity.
- An aws_autoscaling_policy resource can be defined with adjustment_type ChangeInCapacity and a negative scaling_adjustment to scale the group down, with a cooldown period in seconds.  
  > resource "aws_autoscaling_policy" "scale_down" {
  name                   = "terramino_scale_down"
  autoscaling_group_name = aws_autoscaling_group.terramino.name
  adjustment_type        = "ChangeInCapacity"
  scaling_adjustment     = -1
  cooldown               = 120
}
- An aws_cloudwatch_metric_alarm resource can trigger an autoscaling policy action when CPU utilization stays at or below a threshold for a number of consecutive evaluation periods.  
  > resource "aws_cloudwatch_metric_alarm" "scale_down" {
  alarm_description   = "Monitors CPU utilization for Terramino ASG"
  alarm_actions       = [aws_autoscaling_policy.scale_down.arn]
  alarm_name          = "terramino_scale_down"
  comparison_operator = "LessThanOrEqualToThreshold"
  namespace           = "AWS/EC2"
  metric_name         = "CPUUtilization"
  threshold           = "10"
  evaluation_periods  = "2"
  period              = "120"
  statistic           = "Average"

  dimensions = {
    AutoScalingGroupName = aws_autoscaling_group.terramino.name
  }
}
- Running terraform apply provisions all declared resources and confirms the count added, changed, or destroyed in its summary output.  
  > Apply complete! Resources: 18 added, 0 changed, 0 destroyed.
- The terraform output -raw command retrieves a specific output value as a plain string, usable directly in shell commands such as curl.  
  > $ curl $(terraform output -raw lb_endpoint)
- A root module can call a child VPC module and then reference that module's outputs (such as module.vpc.vpc_id and module.vpc.public_subnets) in other resource blocks to wire networking into compute resources.  
  > This configuration uses the vpc module to create a new VPC with public subnets for you to provision the rest of the resources in. The other resources reference the VPC module's outputs.
- You cannot modify a launch configuration after creation; any change to its definition forces Terraform to create a new resource.  
  > You cannot modify a launch configuration, so any changes to the definition force Terraform to create a new resource.
- The aws_launch_configuration resource accepts a name_prefix argument; Terraform appends a unique identifier to the prefix for each new launch configuration created.  
  > a name prefix to use for all versions of this launch configuration. Terraform will append a unique identifier to the prefix for each launch configuration created.
- Using aws_autoscaling_attachment to associate a target group with an ASG and using the inline target_group_arns argument on the ASG are mutually exclusive; when using the attachment resource, you must ignore changes to target_group_arns on the ASG resource.  
  > The two are mutually exclusive, so if you use the aws_autoscaling_attachment resource as done in this configuration, you must ignore changes to the attribute of the ASG resource itself.

## [https://developer.hashicorp.com/terraform/tutorials/state/state-cli](https://developer.hashicorp.com/terraform/tutorials/state/state-cli)

official, fetched 2026-09-28

- The terraform.tfstate file is a JSON-encoded file that Terraform writes and reads at each operation to track resources created by your configuration and map them to real-world resources.  
  > This file is the JSON encoded state that Terraform writes and reads at each
operation.
- Without a matching state file, Terraform cannot determine what infrastructure it manages; the state file is required for Terraform to create plans and make changes.  
  > Terraform compares your configuration with the state file and your existing
infrastructure to create plans and make changes to your infrastructure.
- When you run terraform apply or terraform destroy, Terraform writes metadata about your configuration to the state file and updates infrastructure resources accordingly.  
  > When you run terraform apply or terraform destroy against your initialized
configuration, Terraform writes metadata about your configuration to the state file and updates your infrastructure resources accordingly.
- The resources section of the state file contains a 'mode' key indicating whether the resource is a managed resource ('managed') or a data source ('data').  
  > The first key in this schema is the mode. Mode refers to the type of resource
Terraform creates — either a resource (managed) or a data source (data).
- The state file records resource attributes in plain text (e.g., security_groups as a literal string) rather than the variable-interpolated expressions used in the configuration file.  
  > The security_groups attribute, for example, is captured in plain text in state as opposed to the variable interpolated string in the configuration file.
- Terraform records inter-resource dependencies in the state file under a 'dependencies' key, so any changes to a dependency force a change to the dependent resource.  
  > "dependencies": [
            "aws_security_group.sg_8080",
            "data.aws_ami.ubuntu"
          ]
- You should never manually edit the state file; doing so risks unnecessary drift between your Terraform configuration, state, and infrastructure, which could result in resources being destroyed and recreated on the next apply.  
  > You should not manually change information in your state file in a real-world
situation to avoid unnecessary drift between your Terraform configuration,
state, and infrastructure. Any change in state could result in your
infrastructure being destroyed and recreated at your next terraform apply.
- The 'terraform show' command produces a human-friendly output of all resources and outputs contained in the current state file.  
  > Run terraform show to get a human-friendly output of the resources contained in your state.
- The 'terraform state list' command lists the resource names and local identifiers tracked in the state file, which is useful for finding a specific resource in complex configurations.  
  > Run terraform state list to get the list of resource names and local identifiers in your state file. This command is useful for more complex configurations where you need to find a specific resource without parsing state with terraform show.
- After running terraform destroy, the terraform.tfstate file still exists but contains an empty resources list, confirming all resources were removed.  
  > Your terraform.tfstate file still exists, but does not contain any resources.
Run terraform show to confirm.
$ terraform show
The state file is empty. No resources are represented.
- The 'terraform state mv' command moves resources from one state file to another (using the -state-out flag) and can also rename resources; it updates state but not the configuration file.  
  > The terraform state mv command moves resources from one state file to another.
You can also rename resources with mv. The move command will update the
resource in state, but not in your configuration file.
- To move a resource to a different state file with terraform state mv, use the -state-out flag to specify the destination state file path.  
  > $ terraform state mv -state-out=../terraform.tfstate aws_instance.example_new aws_instance.example_new
Move "aws_instance.example_new" to "aws_instance.example_new"
Successfully moved 1 object(s).
- A 'removed' block in configuration (introduced in Terraform 1.7) removes a resource from state without destroying the real infrastructure when destroy = false is set in its lifecycle block.  
  > removed {
  from = aws_instance.example_new

  lifecycle {
    destroy = false
  }
}
- Terraform automatically performs a refresh during plan, apply, and destroy operations, reconciling state with real infrastructure by default.  
  > Terraform automatically performs a refresh during the plan, apply, and destroy operations. All of these commands will reconcile state by default, and have the potential to modify your state file.
- If a resource exists in the state file but is not present in the configuration, terraform plan will show it as scheduled for destruction.  
  > Because the new EC2 instance is present in state but not in the
configuration, Terraform plans to destroy the moved instance, and remove the
resource from the state file.
- After terraform destroy completes, the empty state file has a 'resources' key set to an empty array, confirming no managed resources remain.  
  > {
  "version": 4,
  "terraform_version": "1.7.0",
  "serial": 18,
  "lineage": "0c41e079-7e11-bcb9-4c2d-050228201fa6",
  "outputs": {},
  "resources": [],
  "check_results": null
}
- Running terraform apply provisions the declared resources, prints a summary of what was created, and updates the state file; outputs are displayed at the end.  
  > Apply complete! Resources: 2 added, 0 changed, 0 destroyed.

Outputs:

aws_region = "us-east-1"
instance_id = "i-05a8893f05c6a37be"
public_ip = "18.212.104.187"
security_group = "sg-0adfd0a0ade3eebdc"
- The AWS provider block can be configured with a region sourced from an input variable, e.g. var.aws_region.  
  > provider "aws" {
  region = var.aws_region
}
- A resource block for an EC2 instance requires at minimum the ami and instance_type arguments, and can optionally reference a security group via vpc_security_group_ids.  
  > resource "aws_instance" "example" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = "t2.micro"
  vpc_security_group_ids = [aws_security_group.sg_8080.id]
- Resource attributes from one block can be referenced in another block using dot notation expressions, such as aws_security_group.sg_8080.id to pass a security group ID into an EC2 instance.  
  > vpc_security_group_ids = [aws_security_group.sg_8080.id]
- Running terraform destroy tears down all managed resources; Terraform updates the state file to reflect that the resources have been removed.  
  > Destroy complete! Resources: 2 destroyed.
Your terraform.tfstate file still exists, but does not contain any resources.
- When you run terraform apply or terraform destroy, Terraform writes metadata about your configuration to the state file and updates infrastructure resources accordingly.  
  > When you run terraform apply or terraform destroy against your initialized
configuration, Terraform writes metadata about your configuration to the state
file and updates your infrastructure resources accordingly.
- Terraform records resource dependencies in the state file under a 'dependencies' key, and any changes to a dependency will force a change to the dependent resource.  
  > Because your state file has a record of your dependencies, enforced by you with a depends_on attribute or by Terraform automatically, any changes to the dependencies will force a change to the dependent resource.
- The -replace flag was introduced in Terraform 0.15.2.  
  > The -replace flag was introduced in Terraform 0.15.2.
- The removed block was introduced in Terraform 1.7; prior versions used the terraform state rm command to remove resources from state.  
  > The removed block was introduced in Terraform 1.7. Previous versions of
Terraform used the terraform state rm command to remove resources from state.
- The terraform import command brings an existing real-world resource back under Terraform management by adding it to the state file.  
  > Run terraform import to bring this instance back into your state file.
- terraform plan output uses a + symbol to indicate resources that will be created and a - symbol for resources that will be destroyed.  
  > Resource actions are indicated with the following symbols:
  + create

## [https://developer.hashicorp.com/terraform/cli/commands/state/show](https://developer.hashicorp.com/terraform/cli/commands/state/show)

official, fetched 2026-09-28

- The terraform state show command displays the attributes of a single resource in the Terraform state file that matches a given address.  
  > The terraform state show command shows the attributes of a single resource in the Terraform state.
- The usage syntax for terraform state show requires an address in resource addressing format pointing to a single resource.  
  > Usage: terraform state show [options] ADDRESS

The command will show the attributes of a single resource in the state file that matches the given address.
- The -state=path flag specifies a path to the state file and defaults to "terraform.tfstate".  
  > -state=path - Path to the state file. Defaults to "terraform.tfstate". Legacy option for the local backend only.
- The -json flag produces machine-readable JSON output for terraform state show, and requires Terraform v1.16 or later.  
  > -json - Displays the resource in machine-readable output
JSON output via the -json option requires Terraform v1.16 or later.
- The JSON output format for terraform state show -json contains three top-level keys: format_version, resource, and diagnostics.  
  > {
  "format_version": "1.0", // the json format version
  "resource": { },         // the resource requested
  "diagnostics": []        // any diagnostics 
}
- A resource inside a module can be shown by prefixing the address with the module name, e.g. module.foo.packet_device.worker.  
  > $ terraform state show 'module.foo.packet_device.worker'
- A resource created with count is addressed using a zero-based index in square brackets, e.g. packet_device.worker[0].  
  > $ terraform state show 'packet_device.worker[0]'
- A resource created with for_each is addressed using the instance key in square brackets with double quotes, and must be wrapped in single quotes on Linux/Mac when the address contains special characters.  
  > $ terraform state show 'packet_device.worker["example"]'
- If providers have been updated with new schema versions since the state was written, you should run terraform refresh before using terraform state show -json so Terraform can display the state correctly.  
  > If you updated providers that contain new schema versions since the state was written, upgrade the state before so that Terraform can display it with show -json. If you are viewing a state file, run terraform refresh first.

## [https://developer.hashicorp.com/terraform/language/meta-arguments/for_each](https://developer.hashicorp.com/terraform/language/meta-arguments/for_each)

official, fetched 2026-09-28

- The for_each meta-argument can be used in resource, module, data, and ephemeral blocks to create multiple instances from a single block.  
  > You can use for_each in the following Terraform configuration blocks:
data blocks
ephemeral blocks
module blocks
resource blocks
- for_each accepts a map or a set of strings, and creates one infrastructure instance per item in that map or set.  
  > The for_each meta-argument accepts a map or a set of strings and creates an instance for each item in that map or set. Each instance is associated with a distinct infrastructure object.
- The toset() function can be used to convert a list of strings into a set suitable for use in for_each.  
  > resource "aws_iam_user" "the-accounts" {
  for_each = toset(["Todd", "James", "Alice", "Dottie"])
  name     = each.key
}
- The tomap() function can be used to create a map for use with for_each.  
  > resource "azurerm_resource_group" "rg" {
  for_each = tomap({
    a_group       = "eastus"
    another_group = "westus2"
  })
  name     = each.key
  location = each.value
}
- When for_each is set on a block, Terraform provides an `each` object with `each.key` (the map key or set member) and `each.value` (the map value, or same as each.key for sets) for use in expressions within that block.  
  > This object has the following attributes:
each.key: The map key or set member corresponding to this instance.
each.value: The map value corresponding to this instance. If a set is provided, this is the same as each.key.
- Individual instances created by for_each are referenced using the syntax TYPE.NAME[KEY] or module.NAME[KEY], using the map key or set member as the index.  
  > <TYPE>.<NAME>[<KEY>] or module.<NAME>[<KEY>]: For example, azurerm_resource_group.rg["a_group"] and azurerm_resource_group.rg["another_group"] refer to individual instances.
- All values that for_each iterates over must be known before Terraform performs any remote resource operations; referencing resource attributes only known after apply (such as a remote-generated unique ID) will result in an error.  
  > All values that the for_each argument iterates over must be known before Terraform performs any remote resource operations. Specifying references to resource attributes that are only known after a configuration is applied, such as a unique ID generated by the remote API when an object is created, will result in an error.
- Sensitive values cannot be used as for_each arguments because Terraform uses the for_each value to identify resource instances and always discloses it in UI output.  
  > You cannot use sensitive values, such as sensitive input variables, sensitive outputs, or sensitive resource attributes, as arguments in for_each. Sensitive values are not allowed because Terraform uses the value in for_each to identify the resource instance and always discloses it in UI output.
- for_each does not implicitly convert lists or tuples to sets; an explicit conversion expression such as toset() must be used.  
  > To prevent unexpected behavior during conversion, the for_each argument does not implicitly convert lists or tuples to sets.
- Converting a list to a set with toset() discards ordering and removes duplicate elements.  
  > Conversion from list to set discards the ordering of the items in the list and removes any duplicate elements. For example, toset(["b", "a", "b"]) produces a set containing only "a" and "b" in no particular order and discards the second "b".
- You cannot use both count and for_each in the same block.  
  > You cannot use both a count and for_each argument in the same block.
- Use for_each when instance arguments must have distinct values that cannot be directly derived from an integer; use count when you want to create nearly identical instances.  
  > Use for_each when some instance arguments must have distinct values that can't be directly derived from an integer. Use the count argument when you want to create nearly identical instances.
- A resource using for_each can be directly chained as the for_each value of another resource to express a one-to-one relationship, such as creating one internet gateway per VPC.  
  > resource "aws_internet_gateway" "example" {
  # One Internet Gateway per VPC
  for_each = aws_vpc.example

  # each.value here is a full aws_vpc object
  vpc_id = each.value.id
}
- An input variable can be typed as set(string) so that it can be used directly in for_each without an explicit type conversion.  
  > variable "subnet_ids" {
  type = set(string)
}

resource "aws_instance" "server" {
  for_each = var.subnet_ids
  #...
}
- A module block can use for_each to create multiple instances of a child module, with each.key used to pass distinct values per instance.  
  > module "bucket" {
  for_each = toset(["assets", "media"])
  source   = "./publish_bucket"
  name     = "${each.key}_bucket"
}
- A for_each module block with a local path source and input variables can create multiple distinct instances of a child module from the root module.  
  > module "ec2_instance" {
  source  = "terraform-aws-modules/ec2-instance/aws"
  version = "6.0.2"
  for_each = local.instance_configs

  name           = each.key
  ami            = data.aws_ami.latest_amazon_linux.id
  instance_type  = each.value.instance_type

  depends_on = [aws_s3_bucket.example]
}
- Keys used in for_each cannot be the result of impure functions such as uuid, bcrypt, or timestamp, because Terraform defers evaluating impure functions during the main evaluation step.  
  > Keys in the for_each argument cannot be the result of or rely on the result of impure functions, including uuid, bcrypt, or timestamp, because Terraform defers evaluating impure functions during the main evaluation step.
- When for_each is used with a map, each.key holds the map key and each.value holds the map value for each instance.  
  > each.key: The map key or set member corresponding to this instance.
each.value: The map value corresponding to this instance. If a set is provided, this is the same as each.key.
- When for_each is used with a set, each.key and each.value are identical for every instance.  
  > subnet_id     = each.key # note: each.key and each.value are the same for a set
- The toset() function can be used to explicitly convert a list of strings into a set suitable for for_each, since Terraform has no literal set syntax.  
  > The Terraform language doesn't have a literal syntax for set values, but you can use the toset function to explicitly convert a list of strings to a set
- An input variable can be declared with type set(string) so that it can be passed directly to for_each without requiring an explicit conversion.  
  > If you are writing a module with an input variable that
will be used as a set of strings for for_each, you can set its type to
set(string) so that you don't need an explicit type conversion
- Converting a list to a set with toset() discards ordering and removes duplicate elements.  
  > Conversion from list to set discards the ordering of the items in the list and
removes any duplicate elements. For example, toset(["b", "a", "b"]) produces a set
containing only "a" and "b" in no particular order and discards the second "b".
- A for expression can be used to extract non-sensitive keys from a map with sensitive values so they can be passed to for_each.  
  > to call keys(local.map) where local.map is an object with sensitive values, but non-sensitive keys, you can create a value to pass to  for_each with toset([for k,v in local.map : k])
- When chaining for_each between an aws_vpc and aws_internet_gateway resource, outputs can expose vpc IDs using a for expression and declare a depends_on to ensure gateways are running first.  
  > output "vpc_ids" {
  value = {
    for k, v in aws_vpc.example : k => v.id
  }

  # The VPCs aren't fully functional until their
  # internet gateways are running.
  depends_on = [aws_internet_gateway.example]
}

## [https://developer.hashicorp.com/terraform/tutorials/configuration-language/for-each](https://developer.hashicorp.com/terraform/tutorials/configuration-language/for-each)

official, fetched 2026-09-28

- The for_each meta-argument allows you to configure a set of similar resources or modules by iterating over a data structure, creating one instance per item.  
  > Terraform's for_each meta-argument allows you to configure a set of similar resources by iterating over a data structure to configure a resource or module for each item in the data structure.
- for_each can be used on both resource blocks and module blocks.  
  > for_each provisions similar resources in module and resource blocks.
- The for_each argument supports maps, lists, and sets as the data structure to iterate over.  
  > The for_each argument also supports lists and sets.
- When for_each is used with a map, each.key holds the map key and each.value holds the corresponding map value for the current iteration.  
  > This Terraform configuration defines multiple VPCs, assigning each key/value pair in the var.project map to each.key and each.value respectively. When you use for_each with a list or set, each.key is the index of the item in the collection, and each.value is the value of the item.
- You can differentiate between instances of resources or modules created with for_each by indexing them with the map key, e.g. module.vpc[each.key].vpc_id.  
  > You can differentiate between instances of resources and modules configured with for_each by using the keys of the map you use. In this example, using module.vpc[each.key].vpc_id to define the VPC means that the security group for a given project will be assigned to the corresponding VPC.
- You cannot use both count and for_each in the same resource or module block.  
  > However, the block already uses count. You cannot use both count and for_each in the same block.
- To work around the count/for_each conflict, move the resource that uses count into a child module, then apply for_each to the module block in the root module.  
  > To solve this, you will move the aws_instance resource into a module, including the count argument, and then use for_each when referring to the module in your main.tf file.
- You cannot include a provider block in modules that use count or for_each; they must inherit provider configuration from the root module.  
  > You cannot include a provider block in modules that use count or for_each. They must inherit provider configuration from the root module. Resources created by the module will all use the same provider configuration.
- A for expression (distinct from for_each) creates a list or map by iterating over a collection, and can be used in output values to map project names to their corresponding resource attributes.  
  > for and for_each are different features. for_each provisions similar resources in module and resource blocks. for creates a list or map by iterating over a collection, such as another list or map.
- Output values can use for expressions to produce a map of project names to resource attributes, such as DNS names or ARNs.  
  > output "public_dns_names" {
  description = "Public DNS names of the load balancers for each project."
  value       = { for p in sort(keys(var.project)) : p => module.elb_http[p].elb_dns_name }
}
- A map-type input variable with a default value can define multiple project configurations, each with distinct sub-attributes like instance_type and environment.  
  > variable "project" {
  description = "Map of project names to configuration."
  type        = map(any)

  default = {
    client-webapp = {
      public_subnets_per_vpc  = 2,
      private_subnets_per_vpc = 2,
      instances_per_subnet    = 2,
      instance_type           = "t2.micro",
      environment             = "dev"
    },
    internal-webapp = {
      public_subnets_per_vpc  = 1,
      private_subnets_per_vpc = 1,
      instances_per_subnet    = 2,
      instance_type           = "t2.nano",
      environment             = "test"
    }
  }
}
- When calling a module multiple times with for_each, the source and input variables are declared once in the module block and each.value is used to supply per-instance values.  
  > module "ec2_instances" {
  source     = "./modules/aws-instance"
  depends_on = [module.vpc]

  for_each = var.project

  instance_count     = each.value.instances_per_subnet * length(module.vpc[each.key].private_subnets)
  instance_type      = each.value.instance_type
  subnet_ids         = module.vpc[each.key].private_subnets[*]
  security_group_ids = [module.app_security_group[each.key].security_group_id]

  project_name = each.key
  environment  = each.value.environment
}
- A module block's source attribute can point to a local subdirectory path to call a child module.  
  > source     = "./modules/aws-instance"
- After adding a new local module reference, you must run terraform init again to register the new module before applying.  
  > Initialize the new module.
$ terraform init
Initializing modules...
- ec2_instances in modules/aws-instance
- Running terraform apply provisions resources and streams output; you must confirm with 'yes' at the prompt before changes are made.  
  > Do you want to perform these actions in workspace "learn-terraform-for-each"?
  Terraform will perform the actions described above.
  Only 'yes' will be accepted to approve.

  Enter a value: yes
- Running terraform destroy tears down all managed resources; you must confirm with 'yes' at the prompt.  
  > Do you really want to destroy all resources in workspace "learn-terraform-for-each"?
  Terraform will destroy all your managed infrastructure, as shown above.
  There is no undo. Only 'yes' will be accepted to confirm.

  Enter a value: yes
- Using separate Terraform projects or workspaces (rather than for_each) is recommended when resource lifecycles need to be managed independently, such as separate production and development environments.  
  > Use separate Terraform projects or workspaces instead of for_each to manage resource lifecycles independently. For example, if production and development environments share the same Terraform project running terraform destroy will destroy both.
- The length() built-in function can be used within resource arguments to compute a count based on the number of items in a collection, such as private subnets.  
  > instance_count     = each.value.instances_per_subnet * length(module.vpc[each.key].private_subnets)
- The required_providers block can pin the AWS provider to a specific version using a version constraint such as ~> 4.22.0.  
  > required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.22.0"
    }
  }
- Outputs from one module (e.g., vpc module) can be threaded into another module (e.g., ec2_instances) as input variables to express cross-module dependencies.  
  > subnet_ids         = module.vpc[each.key].private_subnets[*]
  security_group_ids = [module.app_security_group[each.key].security_group_id]

## [https://developer.hashicorp.com/terraform/language/functions/cidrsubnets](https://developer.hashicorp.com/terraform/language/functions/cidrsubnets)

official, fetched 2026-09-28

- The cidrsubnets function signature is cidrsubnets(prefix, newbits...), where prefix is a CIDR string and each additional newbits argument specifies the number of additional network prefix bits for one returned address range.  
  > cidrsubnets(prefix, newbits...)
prefix must be given in CIDR notation, as defined in
RFC 4632 section 3.1.
The remaining arguments, indicated as newbits above, each specify the number
of additional network prefix bits for one returned address range.
- cidrsubnets returns a list with one element per newbits argument, each element being a string containing an address range in CIDR notation.  
  > The return
value is therefore a list with one element per newbits argument, each
a string containing an address range in CIDR notation.
- Unlike cidrsubnet (which calculates a single subnet and requires you to specify a subnet number), cidrsubnets can calculate many subnets at once, potentially of different sizes, and assigns subnet numbers automatically.  
  > cidrsubnet calculates
a single subnet address within a prefix while allowing you to specify its
subnet number, while cidrsubnets can calculate many at once, potentially of
different sizes, and assigns subnet numbers automatically.
- You must not change any existing newbits arguments to cidrsubnets once addresses have been assigned to real infrastructure, because doing so invalidates later address assignments; however, appending new arguments is safe as long as sufficient address space is available.  
  > you must not change any of the existing arguments once network
addresses have been assigned to real infrastructure, or else later address
assignments will be invalidated. However, you can append new arguments to
existing calls safely, as long as there is sufficient address space available.
- cidrsubnets accepts both IPv4 and IPv6 prefixes, and the result always uses the same addressing scheme as the input prefix.  
  > This function accepts both IPv6 and IPv4 prefixes, and the result always uses
the same addressing scheme as the given prefix.
- Calling cidrsubnets("10.1.0.0/16", 4, 4, 8, 4) produces four consecutive subnets of varying sizes from the /16 prefix.  
  > > cidrsubnets("10.1.0.0/16", 4, 4, 8, 4)
[
  "10.1.0.0/20",
  "10.1.16.0/20",
  "10.1.32.0/24",
  "10.1.48.0/20",
]
- Nested cidrsubnets calls combined with a for expression can concisely allocate groups of network address blocks from a parent prefix.  
  > > [for cidr_block in cidrsubnets("10.0.0.0/8", 8, 8, 8, 8) : cidrsubnets(cidr_block, 4, 4)]
- The hashicorp/subnets/cidr Terraform module wraps cidrsubnets to provide additional functionality such as assigning symbolic names to networks and skipping prefixes for obsolete allocations.  
  > The Terraform module hashicorp/subnets/cidr
wraps cidrsubnets to provide additional functionality for assigning symbolic
names to your networks and skipping prefixes for obsolete allocations.

## [https://developer.hashicorp.com/terraform/language/functions/format](https://developer.hashicorp.com/terraform/language/functions/format)

official, fetched 2026-09-28

- The format function produces a string by formatting values according to a specification string, similar to printf in C.  
  > format(spec, values...)
- The %s verb converts a value to string and inserts its characters.  
  > %s
Convert to string and insert the string's characters.
- The %d verb converts a value to an integer and produces its decimal representation.  
  > %d
Convert to integer number and produce decimal representation.
- The %#v verb serializes any value as JSON, equivalent to jsonencode, and accepts all types including null, list, and map.  
  > %#v
JSON serialization of the value, as with jsonencode. Accepts all types, including items of null, list, and map types.
- The %v verb applies default formatting based on the value type and accepts all types including null, list, and map.  
  > %v
Default formatting based on the value type. Accepts all types, including items of null, list, and map types.
- When %v is used, Terraform maps string to %s, number to %g, bool to %t, and any other type to %#v.  
  > Type
Verb
string
%s
number
%g
bool
%t
any other
%#v
- Null values produce the string "null" when formatted with %v or %#v, and cause an error for other verbs.  
  > Null values produce the string null if formatted with %v or %#v, and cause an error for other verbs.
- An explicit argument position can be specified using [n] immediately before the verb letter, where n is a one-based index.  
  > Introducing a [n] sequence immediately before the verb letter, where n is a decimal integer, explicitly chooses a particular value argument by its one-based index.
- The format function produces an error if the format string requests an impossible conversion or accesses more arguments than are given.  
  > The function produces an error if the format string requests an impossible conversion or access more arguments than are given. An error is produced also for an unsupported format verb.
- A width modifier can be combined with a precision value using a period, e.g. %9.2f means width 9 and precision 2.  
  > %9.2f
Width 9, precision 2.
- The - symbol after % pads the width with spaces on the right rather than the left (left-alignment).  
  > -
Pad the width with spaces on the right rather than the left.
- The 0 symbol after % pads the width with leading zeros rather than spaces.  
  > 0
Pad the width with leading zeros rather than spaces.
- The format function is often less readable than template interpolation syntax for simple substitutions; both produce equivalent output.  
  > Simple format verbs like %s and %d behave similarly to template interpolation syntax, which is often more readable.
> format("Hello, %s!", var.name)
Hello, Valentina!
> "Hello, ${var.name}!"
Hello, Valentina!
- The %q verb converts a value to a string and produces a JSON quoted string representation.  
  > %q
Convert to string and produce a JSON quoted string representation.
- The %f verb converts a value to a number and produces decimal fraction notation with no exponent.  
  > %f
Convert to number and produce decimal fraction notation with no exponent, like 123.456.

## [https://developer.hashicorp.com/terraform/language/meta-arguments/count](https://developer.hashicorp.com/terraform/language/meta-arguments/count)

official, fetched 2026-09-28

- The count meta-argument accepts a whole number and creates that many instances of a resource or module block.  
  > The count meta-argument accepts a whole number and either creates as many instances of the resource or module or invokes an action as many times.
- Each instance created by count is a distinct infrastructure object that is separately created, updated, or destroyed when the configuration is applied.  
  > Each instance has a distinct infrastructure object associated with it, and each is separately created, updated, or destroyed when the configuration is applied.
- Within a block that uses count, you can reference count.index to get the unique zero-based index number of each instance.  
  > count.index: The distinct index number starting with 0 corresponding to this instance.
- A resource block using count = 4 creates four EC2 instances, and count.index can be used in expressions such as tag values to make each instance unique.  
  > resource "aws_instance" "server" {
  count = 4 # create four similar EC2 instances

  ami           = "ami-a1b2c3d4"
  instance_type = "t2.micro"

  tags = {
    Name = "Server ${count.index}"
  }
}
- The count value must be known before Terraform performs any remote resource operations; it cannot refer to resource attributes that are only known after apply.  
  > the count value must be known before Terraform performs any remote resource operations. count cannot refer to any resource attributes that are only known after a configuration is applied, such as a unique ID generated by the remote API when an object is created.
- Individual instances created by count are referenced using an index notation, such as aws_instance.server[0] or aws_instance.server[1], while the block itself is referenced as aws_instance.server.  
  > <TYPE>.<NAME>[<INDEX>] or module.<NAME>[<INDEX>], for example, aws_instance.server[0] and
aws_instance.server[1] refer to individual instances.
- count can be used as a conditional by using a ternary expression, for example setting count = var.creator ? 3 : 0 creates three instances when the variable is true and zero otherwise.  
  > setting a count = var.creator ? 3 : 0 instructs Terraform to create three instances of the resource when a variable named creator is set to true.
- You cannot use both count and for_each in the same resource or module block.  
  > You cannot use both a count and for_each argument in the same resource or module block.
- Use count when instances are nearly identical; use for_each when instance arguments must have distinct values that cannot be directly derived from an integer index.  
  > Use the count argument when you want to create nearly identical instances. Use for_each when some instance arguments must have distinct values that can't be directly derived from an integer index.
- The length() built-in function can be passed a list variable or local value as the count argument to create one resource instance per item in the list.  
  > resource "aws_instance" "server" {

  count = length(var.subnet_ids)

  ami           = "ami-a1b2c3d4"
  instance_type = "t2.micro"
  subnet_id     = var.subnet_ids[count.index]

  tags = {
    Name = "Server ${count.index}"
  }
}
- count can be used on module blocks as well as resource, data, and ephemeral blocks.  
  > You can use count in the following Terraform configuration blocks:
data blocks
ephemeral blocks
module blocks
resource blocks
- A module block can use count with length() and a local list to create multiple instances of the module, using count.index to select a distinct name for each instance.  
  > locals {
  instance_names = ["web", "api", "batch"]
}

module "ec2_instance" {
  source  = "terraform-aws-modules/ec2-instance/aws"
  version = "6.0.2"
  count   = length(local.instance_names)

  name           = local.instance_names[count.index]
  ami            = data.aws_ami.latest_amazon_linux.id
  instance_type  = "t2.micro"

  depends_on = [aws_s3_bucket.example]
}

## [https://developer.hashicorp.com/terraform/language/values/outputs](https://developer.hashicorp.com/terraform/language/values/outputs)

official, fetched 2026-09-28

- An output block requires a value argument, which can be set to any valid expression.  
  > You can set the value argument of an output block to any valid expression.
- Output blocks serve four main purposes: exposing resource attributes from child modules to parent modules, displaying values in CLI output for root modules, sharing state with other Terraform configurations via the terraform_remote_state data source, and passing information from a Terraform operation to an automation tool.  
  > Child modules can expose resource attributes to parent modules.
Root modules can display values in CLI output.
Other Terraform configurations using remote state can access root module outputs with the terraform_remote_state data source, including state sharing in HCP Terraform.
Pass information from a Terraform operation to an automation tool.
- A basic output block includes a description and a value argument referencing a resource attribute.  
  > output "instance_id" {
  description = "ID of the EC2 instance"
  value       = aws_instance.web.id
}

output "instance_ip" {
  description = "Private IP address of the EC2 instance"
  value       = aws_instance.web.private_ip
}
- Terraform displays root module output values in the CLI after you run terraform apply.  
  > Terraform displays root module output values in the CLI after you apply your configuration.
- Parent modules access child module output values using the syntax module.<CHILD_MODULE_NAME>.<OUTPUT_NAME>.  
  > Parent modules can access child module outputs using module.<CHILD_MODULE_NAME>.<OUTPUT_NAME> syntax.
- A parent module references a child module's output by prefixing the output name with the module label, for example module.web_server.instance_ip.  
  > resource "aws_route53_record" "web" {
  zone_id = data.aws_route53_zone.main.zone_id
  name    = "web.example.com"
  type    = "A"
  records = [module.web_server.instance_ip]
  #...
}
- Setting the sensitive argument to true in an output block prevents Terraform from displaying the value in CLI output, showing a redacted message instead.  
  > output "database_password" {
  description = "Auto-generated password for the RDS database instance"
  value       = aws_db_instance.main.password
  sensitive   = true
}
- Even when an output is marked sensitive, Terraform still stores its value in state; using terraform output with -json or -raw flags will display sensitive outputs in plain text.  
  > Terraform stores the values of sensitive outputs in your state. If you use the terraform output CLI command with the -json or -raw flags, Terraform displays sensitive outputs in plain text.
- Adding the ephemeral argument to an output omits that value from state and plan files.  
  > Adding the ephemeral argument to an output omits that value from state and plan files, but it also adds restrictions to the values you can assign to that output.
