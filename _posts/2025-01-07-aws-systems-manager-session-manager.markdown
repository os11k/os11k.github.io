---
layout: post
title: "How to Substitute SSH with AWS Session Manager"
date: 2025-01-07 18:35:00 +0200
categories: jekyll update
comments: true
---

In this article, I will explore AWS Systems Manager Session Manager and how anyone can use it as an alternative to SSH.

## Why Replace SSH?
So why would we want to move away from SSH, a protocol that has worked very well for decades? In my environment, as the number of EC2 instances grew, I found that I sometimes needed to give access to parts of my infrastructure. This wasn’t just about accessing an EC2 instance but often included access to the AWS account as well. In such cases, we not only need to manage AWS accounts but also access to EC2 instances—creating users, generating SSH keys, and so on. When someone leaves, we have to remove access to both the AWS account and the EC2 instances, deleting keys and users accordingly.

## The Idea Behind Session Manager
Imagine we have a tool that combines both SSH and AWS access. All we need to do is create an AWS user with working keys or tokens, and as long as the user has the necessary credentials, they can log in to EC2 instances. When we want to remove their access, we simply remove their access to the AWS console. This was the main reason I wanted to try out Session Manager.

## Alternatives to Session Manager
To be fair, there are several alternatives to SSM, such as EC2 Instance Connect, but we will focus on Session Manager for now.

## Setup Plan
My initial goal was to follow the steps described here:

[Session Manager Setup Guide](https://docs.aws.amazon.com/prescriptive-guidance/latest/patterns/connect-to-an-amazon-ec2-instance-by-using-session-manager.html)

I opted for a paranoid configuration that includes using KMS, generating separate keys for encrypting S3 buckets, and an additional layer of encryption for session data. However, there were a few challenges with this setup.

## Challenges of a Paranoid Setup
Session Manager is region-based, meaning we need to configure it separately for each region. This includes setting up region-specific KMS keys (which cannot be reused across regions), creating separate S3 buckets for each region (since you can't use multiple keys for encrypting the same bucket), and making sure CloudWatch log groups are in the same region.

Long story short, while it's good to be paranoid, the overhead was significant, so I opted for a more pragmatic approach.

## Pragmatic Approach
In my setup, I removed KMS and CloudWatch, and I’m using one bucket for all regions. Logs are still written to S3 buckets, and they are encrypted with AWS-managed keys.

## Code Template
I used the following resource as a template for my code:

[Terraform SSM Example](https://github.com/aws-samples/enable-session-manager-terraform)

It’s a good starting point, but unfortunately, it had too many issues and bugs, so I don’t think it’s production-ready in its current state.

## EC2 Instance Requirements
EC2 instances no longer require SSH access! You can remove port 22 from your security groups. Additionally, there’s no need to add any key to your EC2 instance. All that’s required is for your EC2 instance to have the AWS Systems Manager (SSM) Agent installed. This software is typically included in most popular AMIs, such as Ubuntu.

Also, the EC2 instance needs internet access. If the instance is in a private VPC, review this part of the code and apply the appropriate security group rules to your VPC:
[EC2 SG Configuration](https://github.com/aws-samples/enable-session-manager-terraform/blob/main/session-manager-module/ec2.tf)

## Creating the IAM Role and Resources
At the end of the day, I wrote a module that configures the IAM role, which needs to be attached to the instance and S3 bucket, along with other necessary resources. Using my module, you will still need to create the `aws_ssm_document` document as described below. Here’s a link to the module I wrote on GitHub:
[Terraform Session Manager Module](https://github.com/os11k/terraform-session-manager)

## Example Terraform Configuration
Here’s my `main.tf` to deploy Session Manager. I assume the module code is located in `../modules/ssm`:

{% highlight bash %}
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5"
    }
  }
}

provider "aws" {
  region  = "us-east-1"
  profile = "my-profile-name"
}

module "ssm" {
  source = "../modules/ssm"
}

output "ssm_profile_name" {
  value = module.ssm.ssm-profile-name
}

provider "aws" {
  region  = "us-east-1"
  profile = "my-profile-name"
  alias   = "useast1"
}

resource "aws_ssm_document" "session_manager_prefs_useast1" {
  provider = aws.useast1

  name            = "SSM-SessionManagerRunShell"
  document_type   = "Session"
  document_format = "JSON"

  content = <<DOC
{
    "schemaVersion": "1.0",
    "description": "SSM document to house preferences for session manager",
    "sessionType": "Standard_Stream",
    "inputs": {
        "s3BucketName": "${module.ssm.ssm_s3_bucket_id}",
        "s3KeyPrefix": "AWSLogs/ssm_session_logs",
        "s3EncryptionEnabled": true,
        "cloudWatchLogGroupName": "",
        "runAsEnabled": true,
        "runAsDefaultUser": "${var.user}",
        "shellProfile": {
          "windows": "",
          "linux": "exec /bin/bash\ncd /home/${var.user}"
        },
        "idleSessionTimeout": "20"
    }
}
DOC
}
{% endhighlight %}

## Initial Setup for `us-east-1`
First, we call the module in `us-east-1` to create the IAM role, bucket, and other necessary resources using this code:

{% highlight bash %}
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5"
    }
  }
}

provider "aws" {
  region  = "us-east-1"
  profile = "my-profile-name"
}

module "ssm" {
  source = "../modules/ssm"
}
{% endhighlight %}

This part of the code will output the IAM role name that should be attached to your instances:

{% highlight bash %}
output "ssm_profile_name" {
  value = module.ssm.ssm-profile-name
}
{% endhighlight %}

## Region-Specific Configuration
The last part needs to be copied and pasted for each region where you plan to use Session Manager. Remember, Session Manager config is region-specific.

### Creating Providers for Each Region
First, create a provider. Each region should have a separate provider like this:

{% highlight bash %}
provider "aws" {
  region  = "us-east-1"
  profile = "my-profile-name"
  alias   = "useast1"
}
{% endhighlight %}

### Configuring Session Manager for `us-east-1`
Then, configure Session Manager in that region, ensuring the provider is set accordingly (in our code, it's `aws.useast1`):

{% highlight bash %}
resource "aws_ssm_document" "session_manager_prefs_useast1" {
  provider = aws.useast1

  name            = "SSM-SessionManagerRunShell"
  document_type   = "Session"
  document_format = "JSON"

  content = <<DOC
{
    "schemaVersion": "1.0",
    "description": "SSM document to house preferences for session manager",
    "sessionType": "Standard_Stream",
    "inputs": {
        "s3BucketName": "${module.ssm.ssm_s3_bucket_id}",
        "s3KeyPrefix": "AWSLogs/ssm_session_logs",
        "s3EncryptionEnabled": true,
        "cloudWatchLogGroupName": "",
        "runAsEnabled": true,
        "runAsDefaultUser": "${var.user}",
        "shellProfile": {
          "windows": "",
          "linux": "exec /bin/bash\ncd /home/${var.user}"
        },
        "idleSessionTimeout": "20"
    }
}
DOC
}
{% endhighlight %}

### Adding Configuration for `us-east-2`
Now, let’s assume you want to configure Session Manager in `us-east-2`. You only need to add this snippet at the bottom:

{% highlight bash %}
provider "aws" {
  region  = "us-east-2"
  profile = "my-profile-name"
  alias   = "useast2"
}

resource "aws_ssm_document" "session_manager_prefs_useast1" {
  provider = aws.useast2

  name            = "SSM-SessionManagerRunShell"
  document_type   = "Session"
  document_format = "JSON"

  content = <<DOC
{
    "schemaVersion": "1.0",
    "description": "SSM document to house preferences for session manager",
    "sessionType": "Standard_Stream",
    "inputs": {
        "s3BucketName": "${module.ssm.ssm_s3_bucket_id}",
        "s3KeyPrefix": "AWSLogs/ssm_session_logs",
        "s3EncryptionEnabled": true,
        "cloudWatchLogGroupName": "",
        "runAsEnabled": true,
        "runAsDefaultUser": "${var.user}",
        "shellProfile": {
          "windows": "",
          "linux": "exec /bin/bash\ncd /home/${var.user}"
        },
        "idleSessionTimeout": "20"
    }
}
DOC
}
{% endhighlight %}

### Documentation for the Schema Elements of a Session Document
You can find more information about the input parameters and options available for aws_ssm_document in the official AWS documentation:
[AWS Systems Manager - Session document schema](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-schema.html)

## Conclusion
As you can see, we need to create an Aliased Provider Block, then add a new configuration for Session Manager, referencing the newly created alias.

As an improvement, I could put the Session Manager configuration in a separate module, but in my environment, I don’t think it’s worth the extra complexity, as I don’t have many regions with infrastructure.
