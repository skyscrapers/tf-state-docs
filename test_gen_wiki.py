import unittest
from unittest.mock import patch, mock_open, MagicMock
import os
import json
import yaml
from gen_wiki import (
    load_config, read_json_file, extract_attributes, generate_markdown_table,
    extract_repo_name, download_bucket, process_directory, process_environment,
    list_md_files, copy_wiki
)

class TestGenWiki(unittest.TestCase):

    @patch("builtins.open", new_callable=mock_open, read_data="customer_name = \"test_repo\"")
    def test_extract_repo_name(self, mock_file):
        result = extract_repo_name("dummy_path")
        self.assertEqual(result, "test_repo")

    @patch("builtins.open", new_callable=mock_open, read_data="{}")
    def test_read_json_file_success(self, mock_file):
        result = read_json_file("dummy_path")
        self.assertEqual(result, {})

    @patch("builtins.open", new_callable=mock_open)
    def test_read_json_file_failure(self, mock_file):
        mock_file.side_effect = Exception("File not found")
        result = read_json_file("dummy_path")
        self.assertIsNone(result)

    def test_generate_markdown_table(self):
        header = "Test Table"
        data = [
            {"col1": "data1", "col2": "data2"},
            {"col1": "data3", "col2": "data4"}
        ]
        expected_output = (
            "### Test Table\n\n"
            "| col1 | col2 |\n"
            "| --- | --- |\n"
            "| data1 | data2 |\n"
            "| data3 | data4 |\n\n"
        )
        result = generate_markdown_table(header, data)
        self.assertEqual(result, expected_output)

    def test_extract_attributes(self):
        data = {
            "resources": [
                {
                    "type": "aws_instance",
                    "instances": [
                        {"attributes": {"id": "i-12345", "name": "instance1"}},
                        {"attributes": {"id": "i-67890", "name": "instance2"}}
                    ]
                }
            ]
        }
        resource_type = "aws_instance"
        attributes = ["id", "name"]
        expected_output = [
            {"id": "i-12345", "name": "instance1"},
            {"id": "i-67890", "name": "instance2"}
        ]
        result = extract_attributes(data, resource_type, attributes)
        self.assertEqual(result, expected_output)

    @patch("builtins.open", new_callable=mock_open, read_data="test_config: value")
    def test_load_config(self, mock_file):
        expected_output = {"test_config": "value"}
        result = load_config("dummy_path")
        self.assertEqual(result, expected_output)

    @patch("boto3.client")
    @patch("os.makedirs")
    @patch("shutil.rmtree")
    def test_download_bucket(self, mock_rmtree, mock_makedirs, mock_boto3_client):
        mock_s3_client = MagicMock()
        mock_boto3_client.return_value = mock_s3_client
        download_bucket("test_directory")
        mock_boto3_client.assert_called_once_with('s3')
        mock_rmtree.assert_called_once_with("temp_wiki", ignore_errors=True)
        mock_makedirs.assert_called_once_with("temp_wiki", exist_ok=True)
        mock_s3_client.download_file.assert_called()

    @patch("os.walk")
    def test_list_md_files(self, mock_os_walk):
        mock_os_walk.return_value = [
            ("root", ["dir"], ["file1.md", "file2.txt", "file3.md"])
        ]
        expected_output = ["root/file1.md", "root/file3.md"]
        result = list_md_files("dummy_path")
        self.assertEqual(result, expected_output)

    @patch("subprocess.run")
    def test_copy_wiki(self, mock_subprocess_run):
        md_files = ["file1.md", "file2.md"]
        copy_wiki(md_files)
        calls = [
            unittest.mock.call(['cp', "terraform/live/file1.md", 'temp_wiki'], check=True),
            unittest.mock.call(['cp', "terraform/live/file2.md", 'temp_wiki'], check=True)
        ]
        mock_subprocess_run.assert_has_calls(calls, any_order=True)

if __name__ == "__main__":
    unittest.main()
