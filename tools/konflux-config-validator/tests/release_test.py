from ruamel.yaml import YAML
from pathlib import Path
import pytest
import re
import urllib.request
from utils.helpers import array_diff
import logging
from conftest import release, release_paths, release_files

log = logging.getLogger(__name__)
yaml=YAML(typ='safe') 



def test_build_config():
    assert release.build_config


# Tests that apply to files in the top level of our tenant folder
def test_top_level():
    version = release.version
    filename = 'kustomization.yaml'
    data = yaml.load(release_paths["tenant"] / filename)
    assert f'{version.v}/' in data["resources"], "Release folder is not included in top level kustomization"

#
# Tests that apply to files in the release folder
#

# Test items in the release folder kustomization file
def test_release_level_kustomization():
    version = release.version
    data = yaml.load(release_paths["version"] / 'kustomization.yaml')
    for item in data["resources"]:
        assert re.search(version.v, item), "Item {item} in release kustomization does not have correct version: {version.v}"

all_release_plans = [ item["manifest"] for item in release_files["release_plans"]]
component_release_plans = [ item["manifest"] for item in release_files["release_plans"] if item["kind"] == "component" ]

fbc_release_plans = [ item["manifest"] for item in release_files["release_plans"] if item["kind"] == "fbc" ]

addon_release_plans = [ item["manifest"] for item in release_files["release_plans"] if item["is_addon"] == True ]

stage_release_plans = [ item["manifest"] for item in release_files["release_plans"] if item["environment"] == "stage" ]
prod_release_plans = [ item["manifest"] for item in release_files["release_plans"] if item["environment"] == "prod" ]

stage_fbc_release_plans = [ item["manifest"] for item in release_files["release_plans"] if item["environment"] == "stage" and item["kind"] == "fbc"]
prod_fbc_release_plans = [ item["manifest"] for item in release_files["release_plans"] if item["environment"] == "prod" and item["kind"] == "fbc"]


@pytest.mark.parametrize("manifest", all_release_plans)
def test_release_plan_name(manifest):
    name = manifest["metadata"]["name"]
    version = release.version
    assert re.search(version.hyphen, name), f"{name} does not have {version.hyphen} in the name"


@pytest.mark.parametrize("manifest", all_release_plans)
def test_release_plan_referenced_rpa(manifest):
    name = manifest["metadata"]["name"]
    version = release.version
    assert re.search(version.hyphen, manifest["metadata"]["labels"]["release.appstudio.openshift.io/releasePlanAdmission"]), f"{name} does not have {version.hyphen} in the releasePlanAdmission"

# Checks that apply to all component release plan specs
@pytest.mark.parametrize("manifest", component_release_plans)
def test_component_release_plans(manifest):
    version = release.version
    application = manifest["spec"]["application"]
    name = manifest["metadata"]["name"]
    assert re.search(version.hyphen, application), f"{name} does not have {version.hyphen} in the application name"
    release_notes_sections = ["description", "synopsis", "solution"]
    for item in release_notes_sections:
        section = manifest["spec"]["data"]["releaseNotes"][item]
        assert re.search(version.xyz, section), f"{name} does not have correct version listed in the {item} section of the release notes"

# Validate fbc managed release plans
@pytest.mark.parametrize("manifest", fbc_release_plans)
def test_fbc_release_plans(manifest):
    version = release.version
    application = manifest["spec"]["application"]
    name = manifest["metadata"]["name"]
    # filters out addon releases and component releases
    listed_ocp_version_regex = re.search(r'ocp-(\d+)$', application)
    assert listed_ocp_version_regex, f"{name} does not reference application '{application}' with expected ocp suffix"
    listed_ocp_version = listed_ocp_version_regex[1]
    assert re.search(listed_ocp_version, name), f"ocp version in plan name: '{name}' is not consistent with application: '{application}'"

    
@pytest.mark.parametrize("manifest", fbc_release_plans)
def test_fbc_release_plans(manifest):
    version = release.version

    application = manifest["spec"]["application"]
    name = manifest["metadata"]["name"]
    # filters out addon releases and component releases
    listed_ocp_version_regex = re.search(r'ocp-(\d+)$', application)
    listed_ocp_version = listed_ocp_version_regex[1]
    assert listed_ocp_version in release.ocp_versions, f"The ocp version {listed_ocp_version} listed in the release plan is not in the expected list from the RHOAI-Build-Config repo: {release.ocp_versions}"


@pytest.mark.parametrize("manifest", addon_release_plans)
def test_addon_fbc_release_plans(manifest):
    version = release.version
    addon_ocp_version = release.addon_ocp_version

    application = manifest["spec"]["application"]
    name = manifest["metadata"]["name"]
    # filters out addon releases and component releases
    listed_ocp_version_regex = re.search(r'ocp-(\d+)$', application)
    listed_ocp_version = listed_ocp_version_regex[1]

    assert listed_ocp_version == addon_ocp_version, f"addon ocp version {listed_ocp_version} does not match expected {addon_ocp_version}"

def test_num_addon_release_plans():
    addon_release_plans = [item for item in release_files["release_plans"] if item["is_addon"]] 
    assert addon_release_plans[0]["environment"] == "stage"

def test_num_component_release_plans():
    assert len(component_release_plans) == 2

@pytest.mark.parametrize("manifests", [stage_fbc_release_plans, prod_fbc_release_plans])
def test_check_release_plan_ocp_versions(manifests):
    version = release.version
    has_ocp_versions = {}

    for manifest in manifests:
        application = manifest["spec"]["application"]
        name = manifest["metadata"]["name"]


        listed_ocp_version_regex = re.search(r'ocp-(\d+)$', application)
        listed_ocp_version = listed_ocp_version_regex[1]

        has_ocp_versions[listed_ocp_version] = True

    consistent, only_in_release_plan, only_in_config = array_diff(has_ocp_versions.keys(), release.ocp_versions)

    assert len(only_in_config) == 0, f"There is are ocp version(s) listed in the RHOAI Build Config repo that do not have a corresponding release plan: {only_in_config}"






