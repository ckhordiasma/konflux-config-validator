from ruamel.yaml import YAML
from pathlib import Path
import pytest
import re
import urllib.request
from conftest import release, release_paths, release_files

yaml=YAML(typ='safe') 
def test_project_development_stream():
    version = release.version
    file_path = release_paths["project_development_stream"]
    data = list(yaml.load_all(file_path))
    filename = file_path.name
    for manifest in data:
        kind = manifest["kind"]
        if kind == "ProjectDevelopmentStream":
            validate_project_development_stream(manifest)
        elif kind == "ProjectDevelopmentStreamTemplate":
            validate_project_development_stream_template(manifest)
        else:
            assert False, f"The file {filename} has only ProjectDevelopmentStream/ProjectDevelopmentStreamTemplate manifests, and does not include '{kind}'"

def validate_project_development_stream(manifest):
    version = release.version
    assert re.search(version.hyphen, manifest["metadata"]["name"])
    assert re.search(version.hyphen, manifest["spec"]["template"]["name"])
    template_values = manifest["spec"]["template"]["values"]
    assert len(template_values) == 3
    for item in template_values:
        assert "name" in item and "value" in item
        name = item["name"]
        value = item["value"]
        if name == "version":
            assert version.v == value, f"Template value ({name}: {value}) does not match expected value {version.v}"
        elif name == "versionName":
            assert version.hyphen ==  value, f"Template value ({name}: {value}) does not match expected value {version.hyphen}"
        elif name == "branch":
            assert version.branch == value, f"Template value ({name}: {value}) does not match expected value {version.branch}"
        else:
            assert False, f"Template name '{name}' in {manifest['metadata']['name']} does not equal version, versionName, or branch"

def validate_project_development_stream_template(manifest):
    version = release.version
    name = manifest["metadata"]["name"]

    assert re.search(version.hyphen, name), f"ProjectDevelopmentStreamTemplate name '{name}' does not contain '{version.hyphen}'"
    assert "spec" in manifest, f"ProjectDevelopmentStreamTemplate '{name}' has no 'spec'"
    assert "project" in manifest["spec"], f"ProjectDevelopmentStreamTemplate '{name}' spec has no 'project'"
    assert "variables" in manifest["spec"], f"ProjectDevelopmentStreamTemplate '{name}' spec has no 'variables'"

    assert "resources" in manifest["spec"], f"ProjectDevelopmentStreamTemplate '{name}' spec has no 'resources'"

    assert isinstance(manifest["spec"]["resources"], list), f"'resources' in '{name}' spec is not a list"

    for resource in manifest["spec"]["resources"]:
        kind = resource.get("kind")
        if kind == "Application":
            validate_application_template(resource)
        elif kind == "IntegrationTestScenario":
            validate_integration_test_scenario_template(resource)
        elif kind == "Component":
            validate_component_template(resource)
        else:
            assert False, f"Resource in '{name}' has unexpected kind: '{kind}''"

def validate_application_template(resource):
    """Validates go-template usage in Application resource."""
    pass

def validate_integration_test_scenario_template(resource):
    """Validates go-template usage in IntegrationTestScenario resource."""
    pass

def validate_component_template(resource):
    """Validates go-template usage in Component resource."""
    pass
