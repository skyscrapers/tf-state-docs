#!/bin/sh
TR_VERSION=`curl -s https://api.github.com/repos/gruntwork-io/terragrunt/releases/latest | jq -r .tag_name`
TOFU_VERSION=$1

wget -q "https://github.com/gruntwork-io/terragrunt/releases/download/${TR_VERSION}/terragrunt_linux_amd64"
# chmod +x terragrunt_linux_amd64
# sudo mv terragrunt_linux_amd64 /usr/local/bin/terragrunt

# sudo apt-get update && sudo apt-get install -y wget unzip
# wget -q -O tofu.zip https://github.com/opentofu/opentofu/releases/download/v${TOFU_VERSION}/tofu_${TOFU_VERSION}_linux_amd64.zip
# unzip -u tofu.zip
# sudo mv tofu /usr/local/bin/