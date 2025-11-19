---
layout: post
title: "How to Store Terraform State in Azure with a Bit More Security in Mind"
date: 2025-02-15 19:00:00 +0200
categories: jekyll update
comments: true
image: /assets/azure-storage/3.png
---

## Thank You "Ned in the Cloud"

First and foremost, I would like to thank "Ned in the Cloud" for this video:

[Youtube: Using Azure Storage for Terraform State - Best Practices](https://www.youtube.com/watch?v=iVyKvopGnrQ)


That video was a starting point for this article, and I used it extensively to write my code here. Thank you!

## Initial Setup Using Official Microsoft Documentation

So, you are ready to deploy your first resource in Azure using Terraform, and obviously, you want to save the state in Azure storage, just like you do with AWS in S3. That should not be difficult, right?

Okay, let's Google "Terraform state in Azure storage." The first link, at least for me, is this manual from Microsoft:

[Microsoft: Store Terraform state in Azure Storage](https://learn.microsoft.com/en-us/azure/developer/terraform/store-state-in-azure-storage?tabs=azure-cli)

Official documentation—wow, that should be the best place to start, right?

At this point, you should suspect that something is not quite right. Too many "right?"

In any case, let's follow the documentation and set up everything as it says. Wow, that was easy, great!

But wait. Some eagle-eyed readers probably noticed something a bit off... Like this:

> _In this example, Terraform authenticates to the Azure storage account using an Access Key. In a production deployment, it's recommended to evaluate the available authentication options supported by the azurerm backend and to use the most secure option for your use case._

What the hell?? What does this mean in plain English? Let me translate this for you: "You should never ever use this in production; this is a huge security flaw."

Don't believe me? Just Google "why is it bad to use Access Key to access Azure storage account":

[Access Keys: An Unintended Backdoor-by-Design to Azure Storage Accounts Data](https://www.tenable.com/blog/access-keys-an-unintended-backdoor-by-design-to-azure-storage-accounts-data)

[From listKeys to Glory: How We Achieved a Subscription Privilege Escalation and RCE by Abusing Azure Storage Account Keys](https://orca.security/resources/blog/azure-shared-key-authorization-exploitation/)

Okay, now we know that even official documentation is not always the best way to start.

## Other Bloggers and Articles

So, I started to look beyond official documentation and tried to find some simple and straightforward manuals that just work. Unfortunately, the majority of what I found was quite bad, if not very bad. I stumbled upon one document where it was recommended to set up your Azure storage account with `allow_blob_public_access = true`!!!! That is a legacy setting now, but nevertheless, if you see "public access" in your config, you should suspect something is wrong! You don’t want any public access to your Terraform state, which could contain sensitive data! Never ever do this!

So, after searching and mostly watching "Ned in the Cloud" over and over, I came up with my own setup.

## Solution: Use Entra ID (Formerly Azure AD)

In my opinion, the best approach is using Entra ID (formerly Azure AD). This eliminates the need for Access Keys, which are a huge security risk and difficult to rotate. With Entra ID, you get more granular access control, better auditing, and overall tighter security.

## Requirements

Before we can start deploying this code, we will need to make sure you have everything that is needed. First and foremost, you need an account in the Azure portal, plus OpenTofu or Terraform and Azure CLI installed. Here, I will use OpenTofu.

If you're ready, then log in with Azure CLI by running `az login`. It will give you a link that you need to open in a browser and log in to Azure, just like when you visit [https://portal.azure.com/](https://portal.azure.com/). Pick your account and log in. Then, return to the command line and select a subscription if you have more than one. You will see something like this:

{% highlight bash %}
[Tenant and subscription selection]

No     Subscription name    Subscription ID                       Tenant
-----  -------------------  ------------------------------------  -----------------
[1] *  Free Trial           axxxxxxx-12xx-4xxx-bxxx-fxxxxxxxxxxx  Default Directory
{% endhighlight %}

Press enter or select your subscription by providing the respective number (1 in our case) and pressing enter. Now you should be logged in.

## Terraform Code to Set Up Storage Account and Container

Create `main.tf` and put this code there:

{% highlight bash %}
terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~>3.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~>3.0"
    }
  }
}

provider "azurerm" {
  features {}
  storage_use_azuread = true
}

resource "random_string" "resource_code" {
  length  = 5
  special = false
  upper   = false
}

resource "azurerm_resource_group" "tfstate" {
  name     = "tfstate"
  location = "eastus2"
  tags = {
    ManagedBy = "Terraform"
  }
}

resource "azurerm_storage_account" "tfstate" {
  name                            = "tfstate${random_string.resource_code.result}"
  resource_group_name             = azurerm_resource_group.tfstate.name
  location                        = azurerm_resource_group.tfstate.location
  account_tier                    = "Standard"
  account_kind                    = "StorageV2"
  account_replication_type        = "GRS"
  min_tls_version                 = "TLS1_2"
  shared_access_key_enabled       = false
  default_to_oauth_authentication = true
  allow_nested_items_to_be_public = false

  blob_properties {
    versioning_enabled            = true
    change_feed_enabled           = true
    change_feed_retention_in_days = 90
    last_access_time_enabled      = true

    delete_retention_policy {
      days = 30
    }

    container_delete_retention_policy {
      days = 30
    }

  }

  tags = {
    ManagedBy = "Terraform"
  }
}

resource "azurerm_storage_container" "tfstate" {
  name                  = "tfstate"
  storage_account_name  = azurerm_storage_account.tfstate.name
  container_access_type = "private"
}

output "storage_account_name" {
  value = azurerm_storage_account.tfstate.name
}

output "storage_container_name" {
  value = azurerm_storage_container.tfstate.name
}

{% endhighlight %}

## Explanation of the Code

### Generating a Unique Resource Code
This code generates a random 5-character alphanumeric string using Terraform’s `random_string` resource. We will later use this string as a suffix for the storage account name.

{% highlight bash %}
resource "random_string" "resource_code" {
  length  = 5
  special = false
  upper   = false
}
{% endhighlight %}

### Secure Authentication
This code ensures that we use **Azure AD/Entra ID** to access the storage account instead of access keys, which are a major security risk.

{% highlight bash %}
provider "azurerm" {
  features {}
  storage_use_azuread = true
}
{% endhighlight %}

### Geo-Redundant Storage (GRS)
Using `GRS` replication ensures that our data is available across multiple regions, providing better redundancy and resilience.

{% highlight bash %}
account_replication_type = "GRS"
{% endhighlight %}

More details: [Azure Storage Redundancy](https://learn.microsoft.com/en-us/azure/storage/common/storage-redundancy)

### Important Security Settings
{% highlight bash %}
shared_access_key_enabled       = false
default_to_oauth_authentication = true
allow_nested_items_to_be_public = false
{% endhighlight %}
- **Disabling Access Keys:** Ensures access keys cannot be used for authentication.
- **Enforcing OAuth Authentication:** Defaults authentication to Azure AD.
- **Blocking Public Access:** Prevents any nested items from being exposed publicly.
  - Terraform defaults this to `true`, even though Azure defaults it to `false`!

More details: [GitHub Issue on `allow_nested_items_to_be_public`](https://github.com/hashicorp/terraform-provider-azurerm/issues/27513)

### Versioning, Logging, and Retention Policies
These settings provide **historical tracking, logging, and deletion protection** for better security and auditing:
{% highlight bash %}
blob_properties {
  versioning_enabled            = true
  change_feed_enabled           = true
  change_feed_retention_in_days = 90
  last_access_time_enabled      = true

  delete_retention_policy {
    days = 30
  }

  container_delete_retention_policy {
    days = 30
  }
}
{% endhighlight %}
- **Versioning & Change Feed:** Tracks modifications.
- **Delete Retention:** Allows recovery of deleted blobs and containers for 30 days.

For even more security, consider `infrastructure_encryption_enabled`, which enables **double encryption** or managing your own encryption keys instead of relying on Microsoft.

## Applying the Terraform Configuration
Run:
{% highlight bash %}
tofu init
tofu apply
{% endhighlight %}

If successful, you should see:
{% highlight bash %}
Apply complete! Resources: 4 added, 0 changed, 0 destroyed.

Outputs:

storage_account_name = "tfstate4qymu"
storage_container_name = "tfstate"
{% endhighlight %}

As you can see from the Terraform output, the storage account was created with the name `tfstate4qymu`. In your case, the name will be different, so update your code accordingly.

## Setting Up Access to Azure Storage for Your User

Now we need to assign ourselves and anyone who requires access to the Terraform state in Azure storage the **"Storage Blob Data Contributor"** role.

To do this, go to **portal.azure.com** → **Storage accounts** → **tfstate4qymu** → **Access Control (IAM**) → **Add** → **Add role assignment** → Assign **"Storage Blob Data Contributor"** to your user.

![Diagram]({{ site.url }}/assets/azure-storage/1.png)

## Saving State to Azure Storage

At this point, you're done! You can go ahead and store state for other projects in Azure, so feel free to skip this section and head straight to the last one—**"Saving State for Other Resources"**.

But if you're feeling a bit playful, you can try saving the state for this project itself in Azure Storage, kind of like a snake eating its own tail.

So, here's the final code for this case:

{% highlight bash %}
terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~>3.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~>3.0"
    }
  }
    backend "azurerm" {
    resource_group_name  = "tfstate"
    storage_account_name = "tfstate4qymu"
    container_name       = "tfstate"
    key                  = "azure-storage-terraform-backend.tfstate"
    use_azuread_auth     = true
  }
}

provider "azurerm" {
  features {}
  storage_use_azuread = true
}

resource "random_string" "resource_code" {
  length  = 5
  special = false
  upper   = false
}

resource "azurerm_resource_group" "tfstate" {
  name     = "tfstate"
  location = "eastus2"
  tags = {
    ManagedBy = "Terraform"
  }
}

resource "azurerm_storage_account" "tfstate" {
  name                            = "tfstate${random_string.resource_code.result}"
  resource_group_name             = azurerm_resource_group.tfstate.name
  location                        = azurerm_resource_group.tfstate.location
  account_tier                    = "Standard"
  account_kind                    = "StorageV2"
  account_replication_type        = "GRS"
  min_tls_version                 = "TLS1_2"
  shared_access_key_enabled       = false
  default_to_oauth_authentication = true
  allow_nested_items_to_be_public = false

  blob_properties {
    versioning_enabled            = true
    change_feed_enabled           = true
    change_feed_retention_in_days = 90
    last_access_time_enabled      = true

    delete_retention_policy {
      days = 30
    }

    container_delete_retention_policy {
      days = 30
    }

  }

  tags = {
    ManagedBy = "Terraform"
  }
}

resource "azurerm_storage_container" "tfstate" {
  name                  = "tfstate"
  storage_account_name  = azurerm_storage_account.tfstate.name
  container_access_type = "private"
}

output "storage_account_name" {
  value = azurerm_storage_account.tfstate.name
}

output "storage_container_name" {
  value = azurerm_storage_container.tfstate.name
}

{% endhighlight %}

Now, let's run:

{% highlight bash %}
tofu init -migrate-state
{% endhighlight %}

This will migrate the state of the storage account and container to the blob storage.

Confirm with yes, and once the process is complete, your Terraform state configuration will be securely stored in the tfstate container under the key azure-storage-terraform-backend.tfstate.

![Diagram]({{ site.url }}/assets/azure-storage/2.png)

## Saving State for Other Resources

Whenever you need to add a new resource in Azure, simply include the backend configuration as shown below, ensuring that each project has a unique key. Also, make sure to use the correct `storage_account_name`, as it will be different from the one in our example:

{% highlight bash %}
backend "azurerm" {
  resource_group_name  = "tfstate"
  storage_account_name = "tfstate4qymu"
  container_name       = "tfstate"
  key                  = "<TO CHANGE>.tfstate"
  use_azuread_auth     = true
}
{% endhighlight %}

And that’s it! This is all you need. Simple, right?