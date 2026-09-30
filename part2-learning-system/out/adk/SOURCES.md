# Sources

Every claim a lesson teaches, the words it rests on, and where they are.

## [https://developer.hashicorp.com/terraform/intro/core-workflow](https://developer.hashicorp.com/terraform/intro/core-workflow)

official, fetched 2026-09-28

- The core Terraform workflow consists of three steps: Write (authoring infrastructure as code), Plan (previewing changes before applying), and Apply (provisioning reproducible infrastructure).  
  > The core Terraform workflow has three steps:
Write - Author infrastructure as code.
Plan - Preview changes before applying.
Apply - Provision reproducible infrastructure.
- The terraform init command is used to initialize Terraform and initialize provider plugins.  
  > # Initialize Terraform
$ terraform init
- Running speculative plans with terraform plan allows practitioners to preview changes, catch syntax errors, and confirm that the configuration behaves as expected.  
  > As you make progress on authoring your config, repeatedly running plans can help
flush out syntax errors and ensure that your config is coming together as you
expect.
- The terraform apply command generates and displays an execution plan for confirmation prior to altering any infrastructure resources.  
  > Because terraform apply will display a plan for confirmation before
proceeding to change any infrastructure, that's the command you run for final
review.
- When terraform apply prompts for confirmation before applying changes, only the input 'yes' is accepted to approve execution.  
  >   Only 'yes' will be accepted to approve.

## [https://developer.hashicorp.com/terraform/language/modules](https://developer.hashicorp.com/terraform/language/modules)

official, fetched 2026-09-28

- A module in Terraform represents a collection of resources managed together.  
  > A module is a collection of resources that Terraform manages together.
- The configuration files located in the root directory of a workspace are referred to by Terraform as the root module.  
  > Every Terraform workspace includes configuration files in its root directory. Terraform refers to this configuration as the root module.
- Modules declared via module blocks in a configuration are called child modules.  
  > Modules you configure using module blocks are called child modules.
- A root module can call the same child module multiple times within a single configuration.  
  > You can configure the root module to call child modules multiple times within the same configuration.
- Child modules called by the root module can themselves call nested child modules.  
  > The root module can also call a child module that calls its own nested child module.
- Terraform can retrieve modules from multiple sources, such as the local file system, a Terraform registry, and VCS repositories.  
  > Terraform can load modules from multiple sources, including the local file system, a Terraform registry, and VCS repositories.
- Terraform supports accessing modules from external sources such as S3 buckets and GitHub repositories.  
  > Terraform lets users access modules from several kinds of sources, including S3 buckets and GitHub repositories.
- Users call modules published to supported sources by declaring a module block in their configuration.  
  > Module consumers can use the module block in their configurations to call modules published to one of the supported kinds of sources.

## [https://developer.hashicorp.com/terraform/cli/init](https://developer.hashicorp.com/terraform/cli/init)

official, fetched 2026-09-28

- Before Terraform can carry out operations like provisioning infrastructure or updating state, the working directory must be initialized.  
  > A working directory must be initialized before Terraform can perform any operations in it (like provisioning infrastructure or modifying state).
- The hidden .terraform directory is created during initialization and stores cached provider plugins, modules, the active workspace, and backend configuration.  
  > A hidden .terraform directory, which Terraform uses to manage cached provider plugins and modules, record which workspace is currently active, and record the last known backend configuration in case it needs to migrate state on the next run. This directory is automatically managed by Terraform, and is created during initialization.
- The terraform init command initializes a working directory containing Terraform configuration, enabling subsequent commands such as terraform plan and terraform apply.  
  > Run the terraform init command to initialize a working directory that contains a Terraform configuration. After initialization, you will be able to perform other commands, like terraform plan and terraform apply.
- Executing commands that require initialization without running init first will cause an error specifying that init must be run.  
  > If you try to run a command that relies on initialization without first initializing, the command will fail with an error and explain that you need to run init.
- Terraform initialization downloads and installs provider plugins, downloads modules, and accesses state in the configured backend.  
  > Initialization performs several tasks to prepare a directory, including accessing state in the configured backend, downloading and installing provider plugins, and downloading modules.
- Reinitialization is required when making changes to backend configurations, provider requirements, or module sources and version constraints.  
  > Certain types of changes to a Terraform configuration can require reinitialization before normal operations can continue. This includes changes to provider requirements, module sources or version constraints, and backend configurations.
- The terraform init command is idempotent, meaning running it again when no changes are needed has no effect.  
  > You can reinitialize at any time; the init command is idempotent, and will have no effect if no changes are required.
- The terraform get command only downloads modules referenced in the configuration without performing other initialization tasks.  
  > The terraform get command will download modules referenced in the configuration, but will not perform the other required initialization tasks.

## [https://developer.hashicorp.com/terraform/cli/code](https://developer.hashicorp.com/terraform/cli/code)

official, fetched 2026-09-28

- The terraform fmt command automatically rewrites Terraform configuration files into a canonical format and style.  
  > The terraform fmt command automatically rewrites Terraform
configuration files to a canonical format and style, so you don't have to
waste time making minor adjustments for readability and consistency.
- The terraform validate command checks the syntax and arguments of configuration files in a directory, including resource and module argument and attribute names and types.  
  > The terraform validate commands validates the
syntax and arguments of the Terraform configuration files in a directory,
including argument and attribute names and types for resources and modules.
- The terraform plan and apply commands automatically validate the configuration before carrying out any other tasks.  
  > The plan and apply commands automatically validate a configuration before
performing any other work.

## [https://developer.hashicorp.com/terraform/cli/run](https://developer.hashicorp.com/terraform/cli/run)

official, fetched 2026-09-28

- The basic provisioning commands terraform plan, terraform apply, and terraform destroy all require an initialized working directory.  
  > All of these commands require an initialized working directory, and all of them act only upon the currently selected workspace.
- The terraform plan command determines the desired state from configuration, checks the current state of resources via provider APIs using state data, and describes the changes needed without modifying real-world infrastructure.  
  > The terraform plan command evaluates a Terraform configuration to determine the desired state of all the resources it declares, then compares that desired state to the real infrastructure objects being managed with the current working directory and workspace. It uses state data to determine which real objects correspond to which declared resources, and checks the current state of each resource using the relevant infrastructure provider's API.
- The terraform plan command does not apply changes to real-world infrastructure, but it can save the plan as an artifact for terraform apply to run.  
  > It does not perform any actual changes to real world infrastructure objects; it only presents a plan for making changes. Plans are usually run to validate configuration changes and confirm that the resulting actions are as expected. However, terraform plan can also save its plan as a runnable artifact, which terraform apply can use to carry out those exact changes.
- By default, terraform apply runs a fresh plan and shows it to the user for confirmation before executing the planned changes via provider APIs.  
  > By default, terraform apply performs a fresh plan right before applying changes, and displays the plan to the user when asking for confirmation.
- The terraform apply command can accept a pre-generated plan file from terraform plan instead of calculating a new plan.  
  > However, it can also accept a plan file produced by terraform plan in lieu of running a new plan. You can use this to reliably perform an exact set of pre-approved changes, even if the configuration or the state of the real infrastructure has changed in the minutes since the original plan was created.
- The terraform destroy command prompts the user for confirmation and destroys all resources managed by the current working directory and workspace using state data.  
  > The terraform destroy command destroys all of the resources being managed by the current working directory and workspace, using state data to determine which real world objects correspond to managed resources. Like terraform apply, it asks for confirmation before proceeding.
- A destroy operation behaves the same as deleting all resources from the configuration and running apply, but avoids requiring configuration file modifications.  
  > A destroy behaves exactly like deleting every resource from the configuration and then running an apply, except that it doesn't require editing the configuration.

## [https://developer.hashicorp.com/terraform/language/providers/requirements](https://developer.hashicorp.com/terraform/language/providers/requirements)

official, fetched 2026-09-28

- Provider requirements are declared within a required_providers block nested inside the top-level terraform configuration block.  
  > The required_providers block must be nested inside the top-level
terraform block (which can also contain other settings).
- In a required_providers block, each provider entry specifies a local name as the key and an object with source and version arguments as the value.  
  > Each argument in the required_providers block enables one provider. The key
determines the provider's local name (its unique identifier
within this module), and the value is an object with the following elements:
source - the global source address for the
provider you intend to use, such as hashicorp/aws.
version - a version constraint specifying
which subset of available provider versions the module is compatible with.
- Outside of the required_providers block, Terraform configurations reference providers by their assigned local names.  
  > Outside of the required_providers block, Terraform configurations always refer
to providers by their local names.
- A provider source address consists of three slash-delimited components: an optional hostname, a namespace, and a type.  
  > Source addresses consist of three parts delimited by slashes (/), as
follows:
[<HOSTNAME>/]<NAMESPACE>/<TYPE>
- When the hostname is omitted from a provider source address, Terraform defaults to the public registry at registry.terraform.io.  
  > Hostname (optional): The hostname of the Terraform registry that
distributes the provider. If omitted, this defaults to
registry.terraform.io, the hostname of
the public Terraform Registry.
- If a provider requirement omits the source argument, Terraform uses an implied source address of registry.terraform.io/hashicorp/<LOCAL NAME>.  
  > If you omit the source argument when requiring a provider,
Terraform uses an implied source address of
registry.terraform.io/hashicorp/<LOCAL NAME>.
- The version argument in a provider requirement is optional, and omitting it causes Terraform to accept any available version of the provider.  
  > The version argument is optional; if omitted, Terraform will accept any
version of the provider as compatible.
- The ~> version constraint operator allows only the rightmost component of the specified version number to increment.  
  > The ~> operator is a convenient
shorthand for allowing the rightmost component of a version to increment.
- When a resource does not explicitly define which provider configuration to use, Terraform determines the local provider name from the first word of the resource type.  
  > (If a resource doesn't specify which
provider configuration to use, Terraform interprets the first word of the
resource type as a local provider name.)

## [https://developer.hashicorp.com/terraform/language/block/provider](https://developer.hashicorp.com/terraform/language/block/provider)

official, fetched 2026-09-28

- The provider block is used to declare and configure Terraform plugins called providers.  
  > Use the provider block to declare and configure Terraform plugins, called providers.
- Provider configurations should be defined in the root module, and child modules receive their provider configurations from their parent modules.  
  > Define provider configurations in the root module of your Terraform configuration. Child modules receive their provider configurations from their parent modules, so we strongly recommend against defining provider blocks in child modules.
- The provider block accepts provider-specific arguments, an alias argument, and a deprecated version argument.  
  > The provider block supports the following arguments:
provider "<PROVIDER_NAME>"   block
<PROVIDER_ARGUMENTS>   various
alias   string
version   string (Deprecated)
- If a provider block is not explicitly defined, Terraform assumes and creates an empty default configuration for that provider.  
  > If you do not explicitly define a provider block, Terraform assumes and creates an empty default configuration for that provider.
- Terraform raises an error if a provider has required arguments but only an empty default configuration is created.  
  > However, if a provider has required arguments, Terraform raises an error because it can't create that provider without the required values.
- Expressions used to configure provider arguments can only reference values known before applying the configuration, such as input variables or direct values, and cannot reference computed resource attributes.  
  > You can use expressions to configure provider arguments, but you can only reference values that Terraform knows before it applies your configuration. You can reference input variables and arguments that you specify directly in your configuration, but you cannot reference computed resource attributes, such as google.web.public_ip.
- The alias argument allows defining multiple configurations for the same provider, enabling different configurations to be used by individual resources, data sources, or modules.  
  > Optionally use the alias argument to define multiple configurations for the same provider. Defining multiple provider aliases lets you specify which provider configuration to use for individual resources, data sources, or modules.
- To create multiple configurations for a provider, declare multiple provider blocks with the same name and add the alias argument to each additional configuration.  
  > To create multiple configurations for a given provider, include multiple provider blocks with the same provider name, then add the alias argument to each additional provider configuration to give it a unique identifier.
- To refer to an aliased provider configuration within resource, data, or module blocks, use the format <PROVIDER_NAME>.<ALIAS> in the provider argument.  
  > To refer to a provider alias, use <PROVIDER_NAME>.<ALIAS> in the provider argument of the following blocks:
resource blocks
data blocks
module blocks
- When multiple configurations exist for a provider, the block without an alias is the default configuration, and resources without a provider meta-argument will use it.  
  > If there are multiple aliases for a provider, the provider block without an alias argument is the default configuration for that provider. Resources, data sources, and modules that don't specify the provider meta-argument use the default provider configuration that matches the resource type name.
- The version argument inside a provider block is deprecated; provider version constraints should instead be declared in the required_providers block inside the terraform block.  
  > The version argument in provider configurations is deprecated, and Terraform will remove it in a future version. Instead, declare provider version constraints in the terraform block's required_providers block.
- If every provider block in a configuration includes an alias, Terraform creates an implied empty default configuration for that provider.  
  > If every provider block in your configuration uses an alias, Terraform creates an implied empty default configuration for that provider. Any resource that does not specify a provider meta-argument uses the empty default configuration.
- Child modules must declare expected provider aliases using the configuration_aliases argument in their required_providers block.  
  > To use an aliased provider configuration in a child module, the child module must declare the alias using the configuration_aliases argument in the required_providers block.

## [https://developer.hashicorp.com/terraform/language/block/resource](https://developer.hashicorp.com/terraform/language/block/resource)

official, fetched 2026-09-28

- The resource label is used by Terraform to track the resource in state and does not influence settings on the actual infrastructure resource.  
  > Terraform uses this label to track the resource in your state file. The label does not affect settings on the actual infrastructure resource.
- To reference a resource in a Terraform configuration, you reference it using '<TYPE>.<LABEL>' syntax.  
  > To reference the resource in your configuration, you must refer to it using <TYPE>.<LABEL> syntax.
- The depends_on meta-argument explicitly defines an upstream dependency that Terraform must complete operations on before operating on the referencing resource.  
  > The depends_on meta-argument specifies an upstream resource that the resource depends on. Terraform must complete all operations on the upstream resource before performing operations on the resource containing the depends_on argument.
- The provider meta-argument within a resource block allows a resource to select an alternate provider configuration by referencing its alias.  
  > The provider argument instructs Terraform to use an alternate provider configuration to provision the resource.
resource {
  provider = <provider>.<alias>
}
- Referencing another resource's attribute (such as `role = aws_iam_role.example.name`) instructs Terraform to create the upstream dependency first.  
  > In the following example, the aws_iam_instance_profile resource references the aws_iam_role resource, instructing Terraform to create the upstream resource first.

## [https://developer.hashicorp.com/terraform/language/expressions/references](https://developer.hashicorp.com/terraform/language/expressions/references)

official, fetched 2026-09-28

- Managed resources are referenced using the resource type and resource name in the format <RESOURCE TYPE>.<NAME>.  
  > <RESOURCE TYPE>.<NAME> represents a managed resource of
the given type and name.
- When a resource does not use count or for_each, referencing it produces an object whose attributes can be accessed with dot or square-bracket notation.  
  > If the resource doesn't use count or for_each, the reference's value is an
object. The resource's attributes are elements of the object, and you can
access them using dot or square bracket notation.
- When a resource has the count argument set, referencing it produces a list of objects representing its instances.  
  > If the resource has the count argument set, the reference's value is a
list of objects representing its instances.
- When a resource has the for_each argument set, referencing it produces a map of objects representing its instances.  
  > If the resource has the for_each argument set, the reference's value is a
map of objects representing its instances.
- A data resource is referenced with the data prefix followed by the data source type and name.  
  > data.<DATA TYPE>.<NAME> is an object representing a
data resource of the given data
source type and name.
- Referencing another managed resource within a resource argument creates an implicit dependency between those two resources.  
  > For example, an expression in a resource
argument that refers to another managed resource creates an implicit dependency
between the two resources.
- A splat expression can be used to retrieve a list of an attribute across all instances of a resource configured with count.  
  > aws_instance.example[*].id returns a list of all of the ids of each of the
instances.
- Index syntax can be used to retrieve an attribute of a specific instance of a resource configured with count.  
  > aws_instance.example[0].id returns just the id of the first instance.
- Attributes of instances created using for_each are accessed by specifying the instance key using index syntax.  
  > aws_instance.example["a"].id returns the id of the "a"-keyed resource.

## [https://developer.hashicorp.com/terraform/language/values/variables](https://developer.hashicorp.com/terraform/language/values/variables)

official, fetched 2026-09-28

- In Terraform configurations, variables are referenced using the syntax var.<NAME>.  
  > To reference a variable in other parts of your configuration, use var.<NAME> syntax.
- Variable blocks can include type constraints, human-readable descriptions, and default values.  
  > variable "instance_type" {
  type        = string
  description = "EC2 instance type for the web server"
  default     = "t2.micro"
}
- If an input variable does not have a default value defined, Terraform will prompt the user to supply one prior to generating a plan.  
  > If a variable does not have a default value, such as the subnet_id variable, then Terraform prompts the user to assign a value before it generates a plan.
- Setting sensitive = true on a variable prevents Terraform from displaying its value in CLI output.  
  > If you are defining a variable for sensitive data such as an API key or password, use the sensitive argument to prevent Terraform from displaying the value in CLI output:
- The ephemeral argument can be added to an input variable configuration to exclude the variable from Terraform state and plan files.  
  > You can add the ephemeral argument to your variable configuration to omit the variable from state and plan files.
- Custom validation rules can be added to variable definitions using a validation block specifying a condition and an error message.  
  > validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
- Root module input variables can be populated via environment variables prefixed with TF_VAR_.  
  > You can set environment variables using the TF_VAR_ prefix to a variable name:
export TF_VAR_instance_type=t3.medium
export TF_VAR_environment=staging
terraform apply
- Input variable values can be passed directly to the CLI using the -var=<VAR_NAME>=<VALUE> command line flag.  
  > You can assign variable values with the Terraform CLI using the -var=<VAR_NAME>=<VALUE> flag:
terraform apply -var="instance_type=t3.medium" -var="environment=prod"
- Terraform automatically loads variable definitions from files named terraform.tfvars, terraform.tfvars.json, or files ending in .auto.tfvars or .auto.tfvars.json.  
  > Terraform automatically loads variable definition files if it detects any of the following:
File names ending in .auto.tfvars or .auto.tfvars.json
A file named terraform.tfvars.json
A file named terraform.tfvars
- Terraform resolves variable precedence from highest to lowest: CLI -var/-var-file/HCP Terraform, *.auto.tfvars in lexical order, terraform.tfvars.json, terraform.tfvars, environment variables, and lastly default arguments.  
  > Once you assign a value to a variable, you cannot reassign that variable within the same file. However, if the root module receives multiple values for the same variable name from different sources, Terraform uses the following order of precedence:
Any -var and -var-file options on the command line in the order provided and variables from HCP Terraform
Any *.auto.tfvars or *.auto.tfvars.json files in lexical order
The terraform.tfvars.json file
The terraform.tfvars file
Environment variables
The default argument of the variable block

## [https://developer.hashicorp.com/terraform/language/expressions/operators](https://developer.hashicorp.com/terraform/language/expressions/operators)

official, fetched 2026-09-28

- When multiple operators are used together, Terraform evaluates them in order: unary !, - (multiplication by -1); then *, /, %; then +, - (subtraction); then >, >=, <, <=; then ==, !=; then &&; then ||.  
  > When multiple operators are used together in an expression, they are evaluated
in the following order of operations:
!, - (multiplication by -1)
*, /, %
+, - (subtraction)
>, >=, <, <=
==, !=
&&
||
- Parentheses can be used to override the default operator order of operations in Terraform.  
  > Use parentheses to override the default order of operations. Without
parentheses, higher levels will be evaluated first, so Terraform will interpret
1 + 2 * 3 as 1 + (2 * 3) and not as (1 + 2) * 3.
- The ? and : characters form conditional expressions in Terraform and are not considered operators.  
  > The ? character combined with the : character is part of a conditional expression in Terraform and is not considered an operator.
- Terraform's arithmetic operators (+, -, *, /, %, and unary -) expect number values and produce number values.  
  > The arithmetic operators all expect number values and produce number values
as results:
- The % operator returns the remainder of dividing a by b.  
  > a % b returns the remainder of dividing a by b. This operator is
generally useful only when used with whole numbers.
- Equality operators (== and !=) take values of any type and produce boolean results, returning true for == only if both values have the exact same type and value.  
  > The equality operators both take two values of any type and produce boolean
values as results.
a == b returns true if a and b both have the same type and the same
value, or false otherwise.
- Comparison operators (<, <=, >, >=) expect number values and produce boolean values.  
  > The comparison operators all expect number values and produce boolean values
as results.
- Logical operators (||, &&, !) expect bool values and return bool results.  
  > The logical operators all expect bool values and produce bool values as results.
a || b returns true if either a or b is true, or false if both are false.
a && b returns true if both a and b are true, or false if either one is false.
!a returns true if a is false, and false if a is true.
- Terraform does not include an exclusive OR operator, but for boolean values, exclusive OR is equivalent to using the != operator.  
  > Terraform does not have an operator for the "exclusive OR" operation. If you
know that both operators are boolean values then exclusive OR is equivalent
to the != ("not equal") operator.

## [https://developer.hashicorp.com/terraform/language/functions](https://developer.hashicorp.com/terraform/language/functions)

official, fetched 2026-09-28

- The general syntax for calling a function in Terraform is the function name followed by comma-separated arguments enclosed in parentheses.  
  > The general syntax for function calls is a function name followed by comma-separated arguments in parentheses:
max(5, 12, 9)
- Terraform configuration language does not allow user-defined functions directly in the configuration, but custom providers can be developed to expose functions.  
  > You cannot define your own functions in the Terraform configuration language, but you can develop your own providers that expose functions.
- When calling a provider-specific function, the call must be prefixed with provider::<local-name>:: where local-name matches an entry in the required_providers block.  
  > When using a provider-specific function, add the provider::<local-name>:: where <local-name> corresponds with an entry in the required_providers block.
- You can test and evaluate Terraform built-in functions interactively using the terraform console command.  
  > You can experiment with the behavior of Terraform's built-in functions from the Terraform expression console, by running the terraform console command
- The coalesce function takes multiple arguments and returns the first argument that is neither null nor an empty string.  
  > takes any number of arguments and returns the first one that isn't null or an empty string
- The lookup function retrieves the value of a single element from a map based on a given key.  
  > retrieves the value of a single element from a map, given its key
- The merge function accepts an arbitrary number of maps or objects and returns a single merged map or object.  
  > takes an arbitrary number of maps or objects, and returns a single map or object that contains a merged set of elements from all arguments
- The flatten function takes a list and eliminates nested lists by replacing them with a flattened sequence of their contents.  
  > takes a list and replaces any elements that are lists with a flattened sequence of the list contents
- The file function reads the contents of a file located at a given path and returns them as a string.  
  > reads the contents of a file at the given path and returns them as a string
- The templatefile function reads a file at a specified path and renders its contents as a template with a provided set of template variables.  
  > reads the file at the given path and renders its content as a template using a supplied set of template variables
- The try function evaluates expressions in sequence and returns the result of the first expression that does not raise an error.  
  > evaluates all of its argument expressions in turn and returns the result of the first one that does not produce any errors
- The can function evaluates an expression and returns a boolean indicating whether it evaluated without errors.  
  > evaluates the given expression and returns a boolean value indicating whether the expression produced a result without any errors

## [https://developer.hashicorp.com/terraform/language/values/outputs](https://developer.hashicorp.com/terraform/language/values/outputs)

official, fetched 2026-09-28

- Output blocks can be used by child modules to expose resource attributes to parent modules.  
  > Child modules can expose resource attributes to parent modules.
- Root module outputs display their values in the CLI output.  
  > Root modules can display values in CLI output.
- Other Terraform configurations can access root module outputs across state sharing using the terraform_remote_state data source.  
  > Other Terraform configurations using remote state can access root module outputs with the terraform_remote_state data source, including state sharing in HCP Terraform.
- The value argument of an output block accepts any valid expression.  
  > You can set the value argument of an output block to any valid expression.
- Terraform displays root module outputs on the command line interface after applying a configuration.  
  > Terraform displays root module output values in the CLI after you apply your configuration.
- Parent modules access child module outputs using the syntax module.<CHILD_MODULE_NAME>.<OUTPUT_NAME>.  
  > Parent modules can access child module outputs using module.<CHILD_MODULE_NAME>.<OUTPUT_NAME> syntax.
- Setting the sensitive argument to true on an output prevents Terraform from showing its value in CLI output.  
  > If you are outputting sensitive data such as a password or API key, use the sensitive argument to prevent Terraform from displaying the value in CLI output
- Terraform saves the values of sensitive outputs inside the state file.  
  > Terraform stores the values of sensitive outputs in your state.
- Running the terraform output command with -json or -raw prints sensitive output values in plain text.  
  > If you use the terraform output CLI command with the -json or -raw flags, Terraform displays sensitive outputs in plain text.
- Marking an output with the ephemeral argument excludes the value from state and plan files.  
  > Adding the ephemeral argument to an output omits that value from state and plan files, but it also adds restrictions to the values you can assign to that output.

## [https://developer.hashicorp.com/terraform/language/modules/configuration](https://developer.hashicorp.com/terraform/language/modules/configuration)

official, fetched 2026-09-28

- The source argument in a module block instructs Terraform where to retrieve the child module's configuration files.  
  > Add the module block to your configuration and configure the source argument, which tells Terraform where to get the child module's configuration files.
- Module sources can be located in the public or private Terraform registry, Git repositories, object storage, or the local file system.  
  > You can specify modules hosted on the public or a private Terraform registry, Git repositories, object storage services, and the local file system.
- When sourcing modules from a registry, you can define a version constraint using the version argument.  
  > If you are using modules from a registry, you can add the version argument and specify a version constraint.
- For Git repositories, Terraform by default uses the branch pointed to by HEAD, but a specific branch, tag, or SHA-1 hash can be targeted using the ref query parameter.  
  > If you are using modules hosted in GitHub, BitBucket, or another Git repository, Terraform clones and uses the default branch referenced by HEAD. You can add the ref query parameter to the location specified in the source argument to reference any value supported by the git checkout command, such as a branch, SHA-1 hash, or tag.
- Inputs exposed by a module can be provided as arguments within the module block to configure its behavior.  
  > Module authors expose inputs that you can configure as arguments in the module block. Inputs let you customize the module's behavior without modifying the module's source code.
- Values from child module outputs can be accessed in the parent module using the expression syntax module.<MODULE-NAME>.<OUTPUT-NAME>.  
  > You can reference the values in the parent module using the module.<MODULE-NAME>.<OUTPUT-NAME> expression.
- Any input variable referenced inside a module block's source or version arguments must have const = true declared.  
  > Any input variable referenced in a module block's source or version arguments must declare const = true.
- The count meta-argument can be added to a module block to deploy multiple instances of that module with identical configuration.  
  > count: Use this argument to state how many instances of a module to provision. All instances have the same configuration.
- The for_each meta-argument allows looping over a set of keys to create multiple module instances.  
  > for_each: Use this argument to loop through a set of keys so that Terraform provisions similar module instances.
- Running terraform init downloads the child module files into a local workspace directory.  
  > After configuring the module block in the root or calling module, run terraform init to download the module files into the local working directory.
- The moved block can be used to update a resource address and transfer state into a child module without destroying and recreating the resource.  
  > To change a resource address and move a resource into a child module, use the moved block.
- For Git module sources, the ref query parameter can be appended to the source URL to target a specific branch, tag, or SHA-1 hash.  
  > You can add the ref query parameter to the location specified in the source argument to reference any value supported by the git checkout command, such as a branch, SHA-1 hash, or tag.
- Adding a depth query parameter to a Git module source URL causes Git to perform a shallow clone with that specified commit depth.  
  > Add the depth query parameter to the source URL and specify how many commits the clone operation should include. The depth parameter adds the --depth option to the git clone command, which instructs Git to create a shallow clone that includes only the specified number of commits in the history.
- If a module's source or registry version changes, terraform init must be run again to update it.  
  > If you change the source argument or change the version argument for a module in a registry, you must rerun terraform init.

## [https://developer.hashicorp.com/terraform/language/modules/develop/structure](https://developer.hashicorp.com/terraform/language/modules/develop/structure)

official, fetched 2026-09-28

- The root module is the only required element in the standard module structure, requiring Terraform files in the repository's root directory.  
  > Root module. This is the only required element for the standard
module structure. Terraform files must exist in the root directory of
the repository.
- The recommended filenames for a minimal Terraform module are main.tf, variables.tf, and outputs.tf.  
  > main.tf, variables.tf, outputs.tf. These are the recommended filenames for
a minimal module, even if they're empty.
- In a complex module where resource creation is split across multiple files, any nested module calls should be placed in main.tf.  
  > For a complex module, resource creation may be split into multiple
files but any nested module calls should be in the main file.
- Variable declarations and output declarations should be kept in variables.tf and outputs.tf, respectively.  
  > variables.tf
and outputs.tf should contain the declarations for variables and outputs,
respectively.
- Nested child modules in the standard module structure should be placed in the modules/ subdirectory.  
  > Nested modules. Nested modules should exist under the modules/
subdirectory.
- When a root module calls nested child modules in the same repository, it should reference them with relative paths like ./modules/consul-cluster so Terraform does not download them separately.  
  > If the root module includes calls to nested modules, they should use relative
paths like ./modules/consul-cluster so that Terraform will consider them
to be part of the same repository or package, rather than downloading them
again separately.
- Module blocks within an examples/ directory should set their source argument to the address an external caller would use rather than a relative path.  
  > Because examples will often be copied into other repositories for
customization, any module blocks should have their source set to the
address an external caller would use, not to a relative path.

## [https://developer.hashicorp.com/terraform/cli/commands/show](https://developer.hashicorp.com/terraform/cli/commands/show)

official, fetched 2026-09-28

- The terraform show command produces human-readable output from a state file or plan file.  
  > The terraform show command provides human-readable output from a state or plan file.
- Running terraform show without specifying a file path defaults to displaying the latest state snapshot.  
  > If you don't specify a file path, Terraform will show the latest state snapshot.
- The -json option causes terraform show to output machine-readable JSON representing the state or plan file.  
  > -json - Displays machine-readable output from a state or plan file
- When running terraform show -json against state files, Terraform outputs a JSON representation of the state, even if no file path is specified.  
  > For Terraform state files, including when no path is provided, terraform show -json shows a JSON representation of the state.
- Using the -json flag with terraform show will reveal any sensitive values stored in Terraform state in plain text.  
  > When using the -json command-line flag, any sensitive values in Terraform state will be displayed in plain text.
- The -no-color flag disables color formatting in the terraform show output.  
  > -no-color - Disables output with coloring

## [https://developer.hashicorp.com/terraform/cli/commands/output](https://developer.hashicorp.com/terraform/cli/commands/output)

official, fetched 2026-09-28

- The `terraform output` command extracts output variable values directly from the state file.  
  > The terraform output command extracts the value of an output variable from the state file.
- Running `terraform output` without specifying a name displays every output defined in the root module.  
  > With no additional arguments, output will display all the outputs for the root module.
- When an output NAME is provided to `terraform output`, only that specific output's value is printed.  
  > If an output NAME is specified, only the value of that output is printed.
- The `-json` flag formats output values as a JSON object with a key per output, or returns only the specified output if NAME is provided.  
  > -json - If specified, the outputs are formatted as a JSON object, with a key per output. If NAME is specified, only the output specified will be returned.
- The `-raw` flag converts a given output value to a string and prints it without special formatting, but only supports string, number, and boolean types.  
  > -raw - If specified, Terraform will convert the specified output value to a string and print that string directly to the output, without any special formatting. This can be convenient when working with shell scripts, but it only supports string, number, and boolean values.
- The `-no-color` flag disables color in the output.  
  > -no-color - If specified, output won't contain any color.
- The `-state=path` flag specifies the path to the state file and defaults to `terraform.tfstate`, acting as a legacy option only for the local backend.  
  > -state=path - Path to the state file. Defaults to "terraform.tfstate". Legacy option for the local backend only.
- When using `-json` or `-raw` flags, Terraform prints sensitive values in plain text rather than masking them.  
  > When using the -json or -raw command-line flags, Terraform displays sensitive values in plain text.
- Terraform displays `<sensitive>` when listing all outputs, but does not redact sensitive values when an output is queried specifically by name.  
  > Note that Terraform does not redact sensitive values when you specify the output by name:
- Terraform omits ephemeral values from `terraform output` entirely, even when queried by name, because ephemeral values are never saved in the state.  
  > However, Terraform completely omits any ephemeral values, even if you specify an output by name. Ephemeral values are never stored in state or included in Terraform plans.
- The `terraform output` command only displays outputs defined in the root module.  
  > The terraform output command only displays outputs defined in the root module.
- To view outputs from child modules via `terraform output`, you must expose them through an output block defined in the root module.  
  > To display outputs from child modules, define an output block in your root module using the value of an output from a child module.

## [https://developer.hashicorp.com/terraform/cli/commands/state](https://developer.hashicorp.com/terraform/cli/commands/state)

official, fetched 2026-09-28

- The terraform state command suite allows you to modify the Terraform state file without editing it directly.  
  > You can use the terraform state commands to modify the Terraform state instead modifying the state directly.
- Every terraform state subcommand that modifies state writes a backup file, and this behavior cannot be disabled.  
  > All terraform state subcommands that modify the state write backup files. The path of these backup file can be controlled with -backup.
- Automatic backups generated during state modifications cannot be turned off.  
  > Note that backups for state modification can not be disabled. Due to the sensitivity of the state file, Terraform forces every state modification command to write a backup file.
- Read-only state subcommands like list do not create backup files.  
  > Subcommands that are read-only (such as list) do not write any backup files since they aren't modifying the state.
- Terraform state subcommands function with remote state in the same way they do with local state.  
  > The Terraform state subcommands all work with remote state just as if it was local state.

## [https://developer.hashicorp.com/terraform/tutorials/state/state-cli](https://developer.hashicorp.com/terraform/tutorials/state/state-cli)

official, fetched 2026-09-28

- The terraform show command produces a human-readable display of all the resources currently tracked in Terraform state.  
  > Run terraform show to get a human-friendly output of the resources contained in your state.
- The terraform state list command displays resource names and local identifiers tracked in the state file.  
  > Run terraform state list to get the list of resource names and local identifiers in your state file.
- The -replace flag can be supplied to terraform plan and terraform apply to recreate specified resources without altering the configuration.  
  > You can use the -replace flag for terraform plan and terraform apply operations to safely recreate resources in your environment even if you have not edited the configuration
- The terraform taint command is deprecated in favor of the -replace flag for plan and apply operations.  
  > In older versions of Terraform, you may have used the terraform taint command to achieve a similar outcome. That command has now been deprecated in favor of the -replace flag
- The terraform state mv command moves resources between state files or renames resources within state without altering the configuration file.  
  > The terraform state mv command moves resources from one state file to another. You can also rename resources with mv. The move command will update the resource in state, but not in your configuration file.
- The -state-out flag in terraform state mv specifies the target destination state file for the moved resource.  
  > Move the new EC2 instance resource you just created, aws_instance.example_new, to the old configuration's file in the directory above your current location, as specified with the -state-out flag.
- Resource names must be unique within an intended state file.  
  > Resource names must be unique to the intended state file. The terraform state mv command can also rename resources to make them unique.
- In Terraform versions prior to 1.7, the terraform state rm command was used to remove resources from state.  
  > Previous versions of Terraform used the terraform state rm command to remove resources from state.
- The terraform refresh command updates the state file to match changes made to physical resources outside of the Terraform workflow.  
  > The terraform refresh command updates the state file when physical resources change outside of the Terraform workflow.
- Terraform automatically executes a state refresh during plan, apply, and destroy operations by default.  
  > Terraform automatically performs a refresh during the plan, apply, and destroy operations. All of these commands will reconcile state by default, and have the potential to modify your state file.
