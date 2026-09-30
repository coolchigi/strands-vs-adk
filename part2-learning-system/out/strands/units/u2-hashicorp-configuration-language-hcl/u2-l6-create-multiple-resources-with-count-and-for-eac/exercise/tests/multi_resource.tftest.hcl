mock_provider "aws" {}

# ── count: correct number of subnets ────────────────────────────────────────
run "subnet_count_matches_az_list" {
  command = apply

  assert {
    condition     = length(aws_subnet.public) == length(var.availability_zones)
    error_message = "Expected one aws_subnet.public instance per availability zone, but the counts don't match. Make sure you used count = length(var.availability_zones)."
  }
}

# ── count: each subnet gets a unique CIDR via count.index ───────────────────
run "subnet_cidrs_are_unique" {
  command = apply

  assert {
    condition     = aws_subnet.public[0].cidr_block != aws_subnet.public[1].cidr_block
    error_message = "Subnet 0 and subnet 1 have the same CIDR block. Use cidrsubnet(var.vpc_cidr, 8, count.index) so each subnet gets a distinct CIDR."
  }
}

# ── count: each subnet is placed in the correct AZ ──────────────────────────
run "subnet_az_matches_variable" {
  command = apply

  assert {
    condition     = aws_subnet.public[0].availability_zone == var.availability_zones[0]
    error_message = "Subnet 0 is not in var.availability_zones[0]. Use var.availability_zones[count.index] for the availability_zone argument."
  }

  assert {
    condition     = aws_subnet.public[1].availability_zone == var.availability_zones[1]
    error_message = "Subnet 1 is not in var.availability_zones[1]. Use var.availability_zones[count.index] for the availability_zone argument."
  }
}

# ── count: splat output returns a list with the right length ─────────────────
run "subnet_ids_output_is_list" {
  command = apply

  assert {
    condition     = length(output.subnet_ids) == length(var.availability_zones)
    error_message = "The subnet_ids output should be a list with one ID per availability zone. Use aws_subnet.public[*].id as the output value."
  }
}

# ── for_each: both expected bucket keys are present ──────────────────────────
run "for_each_bucket_keys_exist" {
  command = apply

  assert {
    condition     = contains(keys(aws_s3_bucket.env), "logs")
    error_message = "Expected aws_s3_bucket.env to contain a \"logs\" key. Make sure your for_each map includes logs = \"access-logs\"."
  }

  assert {
    condition     = contains(keys(aws_s3_bucket.env), "backups")
    error_message = "Expected aws_s3_bucket.env to contain a \"backups\" key. Make sure your for_each map includes backups = \"nightly-backups\"."
  }
}

# ── for_each: bucket name equals the map key (each.key) ─────────────────────
run "for_each_bucket_name_is_key" {
  command = apply

  assert {
    condition     = aws_s3_bucket.env["logs"].bucket == "logs"
    error_message = "The logs bucket should have bucket = \"logs\". Set bucket = each.key inside the resource block."
  }

  assert {
    condition     = aws_s3_bucket.env["backups"].bucket == "backups"
    error_message = "The backups bucket should have bucket = \"backups\". Set bucket = each.key inside the resource block."
  }
}

# ── for_each: Purpose tag equals the map value (each.value) ─────────────────
run "for_each_bucket_purpose_tag" {
  command = apply

  assert {
    condition     = aws_s3_bucket.env["logs"].tags["Purpose"] == "access-logs"
    error_message = "The logs bucket tag Purpose should be \"access-logs\". Set Purpose = each.value inside the tags block."
  }

  assert {
    condition     = aws_s3_bucket.env["backups"].tags["Purpose"] == "nightly-backups"
    error_message = "The backups bucket tag Purpose should be \"nightly-backups\". Set Purpose = each.value inside the tags block."
  }
}

# ── for_each: bucket_ids output collects all IDs ─────────────────────────────
run "bucket_ids_output_length" {
  command = apply

  assert {
    condition     = length(output.bucket_ids) == 2
    error_message = "The bucket_ids output should contain exactly 2 IDs (one per for_each entry). Use [for b in aws_s3_bucket.env : b.id] as the output value."
  }
}
