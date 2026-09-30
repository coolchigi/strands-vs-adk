# HashiCorp Configuration Language (HCL)

## Outcomes

- Write resource blocks with required arguments, meta-arguments, and lifecycle rules
- Parameterise configurations with input variables using type, description, default, and validation
- Reduce repetition with local values built from expressions and functions
- Expose resource attributes as output values from a configuration
- Reference attributes across blocks using dot-notation expressions and built-in functions including cidrsubnet and length
- Create multiple similar resources from a single block using count and for_each

## Lessons

- [Write resource blocks with arguments and meta-arguments](u2-l1-write-resource-blocks-with-arguments-and-meta-ar/README.md)
- [Parameterise with input variables](u2-l2-parameterise-with-input-variables/README.md)
- [Reduce repetition with local values](u2-l3-reduce-repetition-with-local-values/README.md)
- [Expose values with output blocks](u2-l4-expose-values-with-output-blocks/README.md)
- [Reference attributes across blocks and use built-in functions](u2-l5-reference-attributes-across-blocks-and-use-built/README.md)
- [Create multiple resources with count and for_each](u2-l6-create-multiple-resources-with-count-and-for-eac/README.md)

## Project

Extend the project directory: declare an S3 bucket resource and an EC2 instance resource (both targeting LocalStack). Use at least one input variable for the bucket name and instance type, at least one local value for a shared name-prefix tag, and output the bucket's id and the instance's id. Use count or for_each to create two subnets from a CIDR variable using cidrsubnet. Apply to LocalStack and verify the outputs print correctly.
