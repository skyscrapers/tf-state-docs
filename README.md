# Gen-wiki.py

`gen-wiki.py` is a script designed to automate the extraction of specific attributes from Terraform state files using Terragrunt, and generate corresponding markdown documentation for each environment in your repo. This documentation can then be used to populate a wiki.

## Features

- **Configuration Loading**: Load configurations from a YAML file.
- **JSON Parsing**: Parse JSON content to extract resource attributes.
- **AWS Profile Removal**: Remove AWS profile information from Terragrunt configuration files.
- **Markdown Generation**: Generate markdown tables from extracted attributes.
- **Terragrunt Integration**: Execute `terragrunt` commands to pull state files.
- **File Management**: Copy and clean up markdown files to a temporary directory.

## Requirements

- Python 3.12
- `pyyaml` library: `pip install pyyaml`
- `terragrunt` command-line tool
- `shutil` and `subprocess` for file and process management

## Usage

1. **Install Dependencies**:
    Ensure you have Python and the required libraries installed. Install `pyyaml` if you haven't already:

    ```sh
    pip install pyyaml
    ```

2. **Prepare Configuration**:
    Create a YAML configuration file detailing the environments and resources to document. Example:

    ```yaml
    resources:
      aws_elasticache_replication_group:
        header: ElastiCache clusters
        attributes:
          - primary_endpoint_address
          - reader_endpoint_address
          - id
    ```

3. **Run the Script**:
    Execute the script with the configuration file and the desired output directory. Example:

    ```sh
    python gen-wiki.py config.yaml output_directory
    ```

    Optional arguments:
    - `--repo_name`: Name of the repository to create documentation for.
    - `--shared_dir`: Directory for shared resources (default: `shared`).

    Example with optional arguments:

    ```sh
    python gen-wiki.py config.yaml output_directory --repo_name my-repo --shared_dir custom_shared
    ```

## Script Overview

- **load_config(config_file)**: Loads the YAML configuration file.
- **load_json(json_content)**: Parses JSON content.
- **remove_aws_provider_profile(file_name)**: Removes AWS profile information from the specified file.
- **extract_attributes(data, resource_type, attributes)**: Extracts specified attributes from the JSON data.
- **generate_markdown_table(header, data)**: Generates a markdown table from the extracted data.
- **run_terragrunt(directory)**: Runs the `terragrunt state pull` command in the specified directory.
- **process_environment(directory, config, output_dir)**: Processes each environment to extract data and generate markdown documentation.
- **list_md_files(directory)**: Lists all markdown files in the specified directory.
- **copy_wiki(md_files)**: Copies markdown files to the temporary wiki directory.
- **clean_up_directory(directory_list)**: Cleans up temporary directories.

## Example Output

The script generates markdown files for each environment specified in the configuration file. The files are saved in the specified output directory and copied to a temporary wiki directory.

