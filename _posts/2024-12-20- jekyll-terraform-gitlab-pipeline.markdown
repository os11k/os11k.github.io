---
layout: post  
title: "Jekyll Blog with Terraform (OpenTofu) Using GitLab Pipelines"
date: 2024-12-19 18:30:00 +0200  
categories: jekyll update  
comments: true  
---

In this guide, I will provide a short manual for deploying a static blog, in this case Jekyll (with minor changes, you should be able to make it work for any other static website), to Amazon S3 using GitLab pipelines. All infrastructure will be managed in Terraform (or OpenTofu, as in our case).

This manual assumes that you are using Route 53 as your DNS provider, and all AWS infrastructure will be deployed to the US East (N. Virginia) region. If you want to use a different region, set the `aws_region` variable accordingly in `blog.tfvars`.

## Step 1: Credential Setup and Creating the S3 Bucket

First, we need to set up AWS credentials and ensure that AWS CLI and Terraform (or OpenTofu) are already installed.

I used this manual to install OpenTofu:

[Installing OpenTofu on .deb-based Linux](https://opentofu.org/docs/intro/install/deb/)

Here is the installation code:

{% highlight bash %}
# Download the installer script:
curl --proto '=https' --tlsv1.2 -fsSL https://get.opentofu.org/install-opentofu.sh -o install-opentofu.sh
# Alternatively: wget --secure-protocol=TLSv1_2 --https-only https://get.opentofu.org/install-opentofu.sh -O install-opentofu.sh

# Give it execution permissions:
chmod +x install-opentofu.sh

# Please inspect the downloaded script

# Run the installer:
./install-opentofu.sh --install-method deb

# Remove the installer:
rm -f install-opentofu.sh
{% endhighlight %}

To install Terraform, use this guide:

[Install Terraform](https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli)

{% highlight bash %}
sudo apt-get update && sudo apt-get install -y gnupg software-properties-common
wget -O- https://apt.releases.hashicorp.com/gpg | gpg --dearmor | sudo tee /usr/share/keyrings/hashicorp-archive-keyring.gpg > /dev/null
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt update
sudo apt-get install terraform
{% endhighlight %}

To install AWS CLI, follow the instructions here:

[Installing or updating to the latest version of the AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)

{% highlight bash %}
apt install unzip
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
{% endhighlight %}

Once the installation is complete, set up your AWS credentials using the profile `prod` (you can choose any profile name, but `prod` is used for this manual):

{% highlight bash %}
aws configure --profile prod
{% endhighlight %}

After setting up your credentials, verify them by running `cat ~/.aws/credentials` — it should return something like:

{% highlight bash %}
[prod]
aws_access_key_id=AXXXXXXXXX
aws_secret_access_key=xxxxxxxxxxxxxxxxxxx
{% endhighlight %}

Test the credentials with the following command to ensure they work:

{% highlight bash %}
aws sts get-caller-identity --profile prod
{% endhighlight %}

You should see output similar to:

{% highlight bash %}
{
    "UserId": "AXXXXXXXXX",
    "Account": "8XXXXXXXXX",
    "Arn": "arn:aws:iam::8XXXXXXXXX:user/jurijsxxxxxxx"
}
{% endhighlight %}

Now, create the S3 bucket where the Terraform state file will be saved. Keep in mind that this name might already be taken, so use something unique. If you use a different name, make sure to update `main.tf` accordingly.:

{% highlight bash %}
aws s3api create-bucket --bucket "myblog-tf-state" --region "us-east-1" --acl private --profile prod
{% endhighlight %}

The output should look something like this:

{% highlight bash %}
{
    "Location": "/myblog-tf-state"
}
{% endhighlight %}

## Step 2: Setup Terraform Code

Most of the Terraform code was taken from the following repository:

[GitHub terraform-aws-static-site](https://github.com/pirxthepilot/terraform-aws-static-site)

The author's blog post explains in detail what each part of the code does:

[pirx.io - Automated Static Site Deployment in AWS Using Terraform](https://pirx.io/posts/2022-05-02-automated-static-site-deployment-in-aws-using-terraform/)

However, I encountered a few issues with this code. First, it was missing the mandatory `aws_s3_bucket_ownership_controls` resource. The solution was to add the `aws_s3_bucket_ownership_controls` resource and update the `aws_s3_bucket_acl` accordingly. Here is the full code snippet for the relevant part:

{% highlight bash %}
resource "aws_s3_bucket" "static_site" {
  bucket = var.domain
}

resource "aws_s3_bucket_ownership_controls" "static_site" {
  bucket = aws_s3_bucket.static_site.id
  rule {
    object_ownership = "BucketOwnerPreferred"
  }
}

resource "aws_s3_bucket_acl" "static_site" {
  depends_on = [aws_s3_bucket_ownership_controls.static_site]

  bucket = aws_s3_bucket.static_site.id
  acl    = "private"
}
{% endhighlight %}

Additionally, we need to create an IAM user for deploying the blog via the GitLab pipeline. I copied the relevant code from here:

[GitHub terraform-aws-s3-static-site](https://github.com/brianmacdonald/terraform-aws-s3-static-site)

{% highlight bash %}
resource "aws_iam_user" "deploy" {
  name = "${var.domain}-deploy"
  path = "/"
}

resource "aws_iam_access_key" "deploy" {
  user = aws_iam_user.deploy.name
}

resource "aws_iam_user_policy" "deploy" {
  name   = "deploy"
  user   = aws_iam_user.deploy.name
  policy = data.aws_iam_policy_document.deploy.json
}
{% endhighlight %}

Add this code snippet to `outputs.tf` to output the credentials needed for the pipeline:

{% highlight bash %}
output "AWS_ACCESS_KEY_ID" {
  sensitive   = true
  description = "The AWS Access Key ID for the IAM deployment user."
  value       = aws_iam_access_key.deploy.id
}

output "AWS_SECRET_ACCESS_KEY" {
  sensitive   = true
  description = "The AWS Secret Key for the IAM deployment user."
  value       = aws_iam_access_key.deploy.secret
}
{% endhighlight %}

To make things easier, I’ve consolidated all the code into a single repository:

[GitHub jekyll-terraform-aws-s3](https://github.com/os11k/jekyll-terraform-aws-s3)

I chose to use a monolithic approach instead of modules for simplicity. You just need to set at least the `domain` and `route53_zone_id` variables in `blog.tfvars` and you're ready to deploy the infrastructure in AWS:

{% highlight bash %}
tofu init
tofu plan -var-file="blog.tfvars"
tofu apply -var-file="blog.tfvars"
{% endhighlight %}

or using Terraform:

{% highlight bash %}
terraform init
terraform plan -var-file="blog.tfvars"
terraform apply -var-file="blog.tfvars"
{% endhighlight %}

Once applied, the output will display variables to use later in the pipeline:

{% highlight bash %}
AWS_ACCESS_KEY_ID = <sensitive>
AWS_SECRET_ACCESS_KEY = <sensitive>
CLOUDFRONT_DISTRIBUTION_ID = "EXXXXXX"
S3_BUCKET = "my-site.com"
{% endhighlight %}

To retrieve sensitive variables, run:

{% highlight bash %}
tofu output --json
{% endhighlight %}

or using Terraform:
{% highlight bash %}
terraform output --json
{% endhighlight %}

## Step 3: Setup GitLab Pipeline

The pipeline I use is directly copied from here:

[SchenkTech Blog - Hosting a Jekyll Site in S3 Part 2](https://blog.schenk.tech/posts/jekyll-blog-in-aws-part2/)

Since the author didn’t provide a Git repository for the code, I created one myself:

[GitLab deploy-jekyll-to-s3](https://gitlab.com/jurijs.ivolga/deploy-jekyll-to-s3)

When you fork that repository or copy the files, you will need to set the following variables in GitLab CI/CD settings. Ensure they are masked and protected to safeguard sensitive information:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `CLOUDFRONT_DISTRIBUTION_ID`
- `S3_BUCKET`

Next, add your actual Jekyll code to the repository, commit, and push it:

{% highlight bash %}
cd ~
git clone https://github.com/daattali/beautiful-jekyll.git
rm -Rf ./beautiful-jekyll/.git* ./beautiful-jekyll/README.md
cp -a ./beautiful-jekyll/* ./deploy-jekyll-to-s3/  # Assuming your code with the pipeline is in ~/deploy-jekyll-to-s3 directory
cd ~/deploy-jekyll-to-s3
git add .
git commit -m "added jekyll"
git push
{% endhighlight %}

And you're done! Once the build completes, your website will be deployed, and you should see the Beautiful Jekyll template live.