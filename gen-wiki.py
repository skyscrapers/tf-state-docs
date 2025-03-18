import os
import yaml
import json
import boto3
import argparse
import subprocess
from collections import defaultdict

MODULES_NAME = []

def compare_directory_names(directory_names):
    # Create a defaultdict to store matching directory groups
    grouped_directories = defaultdict(list)
    
    # Iterate through each directory name and extract the base directory name
    for directory in directory_names:
        parts = directory.split('-')
        base_name = parts[0]  # Assume the base directory name is the last part
        grouped_directories[base_name].append(directory)
    
    # Create the result list in the required format
    matching_directories = [{base_name: dirs} for base_name, dirs in grouped_directories.items()]
    return matching_directories


def process_files(module_dir, directory):
    files = os.listdir(f"{module_dir}/{directory}")
    for file in files:
        if file.endswith('.md'):
            return f"{module_dir}/{directory}/{file}"
        
def remove_module_from_list(module_list, module_to_remove):
    clean_least = [i for i in module_list if i not in module_to_remove]
    return clean_least

def create_str_for_multiple_modules(paths, module_name, module_full_name):
    content = ""
    print(module_name)
    if any(paths):
      content += f"## {module_name.capitalize()}\n\n"
    for index, path in enumerate(paths):
        if path != None:
          with open(path, 'r') as f:
              tmp = f.read()
              if tmp.strip():
                  content += f"### {module_full_name[index].capitalize()}\n\n"
                  tmp = tmp.replace("# ", "#### ",)
                  content += tmp
    MODULES_NAME.append(module_name)
    return content

def create_modules_documentation(output_dir):
    modules_dir = '../modules'
    markdown_content = ""

    output_file = os.path.join(output_dir, f"Modules-documentation.md")
    os.makedirs(output_dir, exist_ok=True)

    directory_names = [d for d in os.listdir(modules_dir) if os.path.isdir(os.path.join(modules_dir, d))]
    multiple_directory = compare_directory_names(directory_names)

    for modules in multiple_directory:
      paths = []
      for module, directories in modules.items():
          for directory in directories:
              paths.append(process_files(modules_dir, directory))
      

      if paths.__len__() > 1:
        print(paths, module, directories)
        markdown_content += create_str_for_multiple_modules(paths, module, directories)

      with open(output_file, 'w') as f:
          f.write(markdown_content)
      print(f"Markdown file generated for module: {module}")

def load_config(config_file):
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    return config
    
def read_json_file(file_path):
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            return data
    except Exception as e:
        print(f"Error reading file: {e}")
        return None

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
        row = "| " + " | ".join(f"`{str(item.get(h, ''))}`" for h in headers) + " |\n"
        table += row

    table += "\n"
    return table

def extract_repo_name(file_path):
    with open(file_path, 'r') as file:
        for line in file:
            if "customer_name" in line:
                customer_name = line.split('=', 1)[1].strip().strip('"')
                return customer_name
    
def download_bucket(directory):
    s3 = boto3.client('s3')
    bucket_name = "terraform-remote-state-" + extract_repo_name("root.hcl")
    try:
        s3.download_file(bucket_name, directory, "tmp_file.json")
        return "tmp_file.json"
    except Exception as e:
        print(f"Error: {e}")
        return None

def process_directory(directory, config):
    json_content = download_bucket(directory)
    if not json_content:
        return None

    data = read_json_file(json_content)
    markdown_content = ""

    for resource_type, settings in config.get('resources', {}).items():
        header = settings.get('header', resource_type)
        attributes = settings.get('attributes', [])
        extracted_data = extract_attributes(data, resource_type, attributes)
        table = generate_markdown_table(header, extracted_data)
        if table:
            markdown_content += table

    if markdown_content:
        directory = directory.split('/', 1)[1]
        markdown_content = f"## {directory.capitalize()}\n\n" + markdown_content

    return markdown_content

def process_environment(environment, config, output_dir):
    markdown_content = ""
    for root, dirs, files in os.walk(f"{environment}"):
        if '.terragrunt-cache' in root:
            continue

        content = process_directory(root, config)
        if content:
            markdown_content += content

        for file in files:
            if file.endswith('.md'):
                with open(os.path.join(root, file), 'r') as f:
                    content = f.read()
                    if content.strip():
                        markdown_content += f"\n### Docs\n\n"
                        markdown_content += content

    if markdown_content.strip() != f"# {environment.capitalize()} Environment\n\n":
        print(os.getcwd())
        output_file = f"{output_dir}/{environment.capitalize()}-environment.md"
        os.makedirs(output_dir, exist_ok=True)
        with open(output_file, 'w') as f:
            f.write(markdown_content)
        print(f"Markdown file generated for {environment}: {output_file}")

def list_md_files(directory):
    """List all .md files in a given directory."""
    md_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.md'):
                md_files.append(os.path.join(root, file))
    return md_files

def copy_wiki(md_files):
    for md_file in md_files:
        subprocess.run(['cp', "terraform/live/" + md_file, 'temp_wiki'], check=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Extract secrets using terragrunt state pull based on a YAML configuration.')
    parser.add_argument('config_file', default='/config.yml', help='Path to the YAML configuration file')
    parser.add_argument('output_dir', default='output/', help='Path to the output directory')
    parser.add_argument('--repo_name', default=os.getenv("REPO_NAME"), help='Name of the repo you want to create a doc for')
    parser.add_argument('--shared_dir', default='shared', help='Directory for shared resources')

    args = parser.parse_args()

    config = load_config(args.config_file)
    os.chdir("terraform/live")
    directories = [d for d in os.listdir(os.getcwd()) if os.path.isdir(os.path.join(os.getcwd(), d))]
    for directory in directories:
        process_environment(directory, config, args.output_dir)

    md_files = list_md_files(args.output_dir)
    try :
        create_modules_documentation(args.output_dir)
        md_files += list_md_files(args.output_dir)
    except Exception as e:
        print(f"Error creating modules documentation: {e}")
    os.chdir("../..")
    copy_wiki(md_files)
