import os
import re
import yaml
import json
import argparse
import subprocess
import shutil

TEMP_DIR = 'temp_wiki'

HOMEPAGE_CONTENT = """
# Welcome to {repo_name} terragrunt Wiki

## Introduction
Welcome to the official wiki for the **{repo_name}** project. Here you will find all the necessary documentation to understand and contribute to the project.

## Table of Contents
{toc}
"""

def load_config(config_file):
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    return config

def load_json(json_content):
    return json.loads(json_content)

def remove_aws_provider_profile(file_name):
    search_pattern = r'aws_profile\s*=\s*".*?"'
    replace_pattern = 'aws_profile   = ""'

    with open(file_name, 'r') as file:
        content = file.read()
    new_content = re.sub(search_pattern, replace_pattern, content)
    with open(file_name, 'w') as file:
        file.write(new_content)

def extract_attributes(data, resource_type, attributes):
    extracted_data = []
    for resource in data.get('resources', []):
        if resource.get('type') == resource_type:
            for instance in resource.get('instances', []):
                extracted_item = {}
                if not attributes:
                    extracted_item['id'] = instance.get('attributes', {}).get('id')
                for attr in attributes:
                    if attr:
                        extracted_item[attr] = instance.get('attributes', {}).get(attr)
                extracted_data.append(extracted_item)
    return extracted_data

def generate_markdown_table(header, data):
    if not data:
        return ""

    headers = list(data[0].keys())
    table = f"### {header}\n\n"
    table += "| " + " | ".join(headers) + " |\n"
    table += "| " + " | ".join(['---'] * len(headers)) + " |\n"

    for item in data:
        row = "| " + " | ".join(str(item.get(h, '')) for h in headers) + " |\n"
        table += row

    table += "\n"
    return table

def run_terragrunt(directory):
    try:
        result = subprocess.run(['terragrunt', 'state', 'pull'], cwd=directory, check=True, capture_output=True, text=True)
        print(f"Directory = ", directory)
        return result.stdout
    except subprocess.CalledProcessError as e:
        return None

def process_directory(directory, config):
    json_content = run_terragrunt(directory)
    if not json_content:
        return None

    data = load_json(json_content)
    markdown_content = ""

    for resource_type, settings in config.get('resources', {}).items():
        header = settings.get('header', resource_type)
        attributes = settings.get('attributes', [])
        extracted_data = extract_attributes(data, resource_type, attributes)
        table = generate_markdown_table(header, extracted_data)
        if table:
            markdown_content += table

    if markdown_content:
        module_name = os.path.basename(directory)
        markdown_content = f"## {module_name.capitalize()}\n\n" + markdown_content

    return markdown_content

def process_environment(environment, config, output_dir):
    markdown_content = f"# {environment.capitalize()} Environment\n\n"
    for root, dirs, files in os.walk(environment):
        if '.terragrunt-cache' in root:
            continue

        content = process_directory(root, config)
        if content:
            markdown_content += content

    if markdown_content.strip() != f"# {environment.capitalize()} Environment\n\n":
        output_file = os.path.join(output_dir, f"{environment}.md")
        os.makedirs(output_dir, exist_ok=True)
        with open(output_file, 'w') as f:
            f.write(markdown_content)
        print(f"Markdown file generated for {environment}: {output_file}")

def process_shared_ecr(shared_dir, config, output_dir):
    ecr_dir = os.path.join(shared_dir, 'ecr')
    if os.path.isdir(ecr_dir):
        markdown_content = f"# Shared ECR\n\n"
        content = process_directory(ecr_dir, config)
        if content:
            markdown_content += content
            output_file = os.path.join(output_dir, 'ecr.md')
            with open(output_file, 'w') as f:
                f.write(markdown_content)
            print(f"Markdown file generated for shared ECR: {output_file}")

def list_md_files(directory):
    """List all .md files in a given directory."""
    md_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.md'):
                md_files.append(os.path.join(root, file))
    return md_files

def generate_sidebar_content(md_files):
    """Generate sidebar content from a list of markdown files."""
    sidebar_content = "# Sidebar\n\n - [Home](home)\n"
    for md_file in md_files:
        filename = os.path.basename(md_file)
        name, _ = os.path.splitext(filename)
        sidebar_content += f"- [{name}]({name})\n"
    return sidebar_content

def generate_homepage_content(repo_name, md_files):
    """Generate home page content from a list of markdown files."""
    toc = ""
    for md_file in md_files:
        filename = os.path.basename(md_file)
        name, _ = os.path.splitext(filename)
        toc += f"- [{name}]({name})\n"
    return HOMEPAGE_CONTENT.format(repo_name=repo_name, toc=toc)

def create_sidebar_and_homepage(temp_dir, repo_name, md_files):
    """Create a custom sidebar and a stylish home page."""
    homepage_content = generate_homepage_content(repo_name, md_files)

    with open(os.path.join(temp_dir, 'Home.md'), 'w', encoding='utf-8') as file:
        file.write(homepage_content)

def copy_wiki(md_files):
    for md_file in md_files:
        subprocess.run(['cp', "terraform/live/" + md_file, 'temp_wiki'], check=True)

def clean_up_directory(directory_list):
    os.chdir("..")
    for directory in directory_list:
        try:
            shutil.rmtree(directory)
        except Exception as e:
            print(f"{e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Extract secrets using terragrunt state pull based on a YAML configuration.')
    parser.add_argument('config_file', help='Path to the YAML configuration file')
    parser.add_argument('output_dir', help='Path to the output directory')
    parser.add_argument('repo_name', help='Name of the repo you want to create a doc for')
    parser.add_argument('--environments', nargs='+', default=['development', 'production', 'test', 'staging'], help='Environments to process')
    parser.add_argument('--shared_dir', default='shared', help='Directory for shared resources')

    args = parser.parse_args()

    config = load_config(args.config_file)
    os.chdir("terraform/live")
    remove_aws_provider_profile("terragrunt.hcl")
    directories = [d for d in os.listdir(os.getcwd()) if os.path.isdir(os.path.join(os.getcwd(), d))]
    for directory in directories:
        process_environment(directory, config, args.output_dir)

    md_files = list_md_files(args.output_dir)
    os.chdir("../..")
    create_sidebar_and_homepage(TEMP_DIR, args.repo_name, md_files)
    copy_wiki(md_files)