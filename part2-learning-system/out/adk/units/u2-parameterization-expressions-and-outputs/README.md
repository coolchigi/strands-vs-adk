# Parameterization, Expressions, and Outputs

## Outcomes

- Declare strongly-typed input variables with defaults, sensitivity constraints, and validation rules
- Manipulate collection types and calculate resource configurations dynamically using built-in functions
- Expose resource attributes and calculated data to the CLI and external callers using outputs

## Lessons

- [Input Variables and Precedence Resolution](u2-l1-input-variables-and-precedence-resolution/README.md)
- [HCL Operators, Functions, and Dynamic Expressions](u2-l2-hcl-operators-functions-and-dynamic-expressions/README.md)
- [Exposing State and Resource Attributes with Output Values](u2-l3-exposing-state-and-resource-attributes-with-outp/README.md)

## Project

Refactor the AWS network configuration into separate `variables.tf`, `main.tf`, and `outputs.tf` files. Parameterize VPC CIDR, subnet CIDR maps, and availability zones using validation rules. Use `merge()` to assign standardized resource tags, and export the VPC ID, public subnet IDs list, and an ephemeral session token in `outputs.tf`. Apply the configuration against LocalStack and confirm outputs print as expected.
