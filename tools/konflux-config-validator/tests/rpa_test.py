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

# helper arrays for parameterizing by different categories
all_release_plan_admissions = [item['manifest'] for item in release_files["release_plan_admissions"]]

prod_release_plan_admissions = [item['manifest'] for item in release_files["release_plan_admissions"] if item["environment"] == "prod" ]

stage_release_plan_admissions = [item['manifest'] for item in release_files["release_plan_admissions"] if item["environment"] == "stage" ]

onprem_release_plan_admissions = [item['manifest'] for item in release_files["release_plan_admissions"] if item["is_addon"] == False ]

addon_release_plan_admissions = [item['manifest'] for item in release_files["release_plan_admissions"] if item["is_addon"] == True ]
                                  
fbc_release_plan_admissions = [item['manifest'] for item in release_files["release_plan_admissions"] if item["kind"] == "fbc" ]

component_release_plan_admissions = [item['manifest'] for item in release_files["release_plan_admissions"] if item["kind"] == "component" ]

@pytest.mark.parametrize("manifest", component_release_plan_admissions )
def test_component_rpa_application_name(manifest):
        assert manifest["spec"]["applications"][0] == f"rhoai-{release.version.hyphen}"
        assert len(manifest["spec"]["applications"]) == 1
    
@pytest.mark.parametrize("manifest", component_release_plan_admissions )
def test_component_rpa_product_version(manifest):
    product_version = manifest["spec"]["data"]["releaseNotes"]["product_version"]
    name = manifest["metadata"]["name"]
    assert product_version == release.version.xy, f"{name}: product_version is listed as {product_version}, which does not match the expected release {release.version.xy}"

@pytest.mark.parametrize("manifest", component_release_plan_admissions )
def test_component_rpa_tag_version(manifest):
    tags = manifest["spec"]["data"]["mapping"]["defaults"]["tags"]
    name = manifest["metadata"]["name"]
    assert release.version.v in tags, f"{name}: Version {release.version.v} not present in spec.data.mapping.defaults.tags[]"

@pytest.mark.parametrize("manifest", all_release_plan_admissions )
def test_rpa_names(manifest):
    name = manifest["metadata"]["name"]
    assert re.search(rf'{release.version.hyphen}', manifest["metadata"]["name"])


@pytest.mark.parametrize("manifest", prod_release_plan_admissions )
def test_prod_rpa_intentions(manifest):
    name = manifest["metadata"]["name"]
    intention = manifest["spec"]["data"]["intention"]
    assert intention == "production", f"{name}: spec.data.intention should be 'production' instead of '{intention}'"

@pytest.mark.parametrize("manifest", stage_release_plan_admissions )
def test_prod_rpa_intentions(manifest):
    name = manifest["metadata"]["name"]
    intention = manifest["spec"]["data"]["intention"]
    assert intention == "staging", f"{name}: spec.data.intention should be 'staging' instead of '{intention}'"

@pytest.mark.parametrize("manifest", all_release_plan_admissions )
def test_release_plan_admissions(manifest):
    name = manifest["metadata"]["name"]
    pipeline_params = manifest["spec"]["pipeline"]["pipelineRef"]["params"]
    pipeline_revision = [item["value"] for item in pipeline_params if item["name"] == "revision"][0]

    assert pipeline_revision == "production", f"{name}: the revision in spec.pipeline.pipelineRef should be 'production' instead of '{pipeline_revision}'"


all_components = [] 
for admission in component_release_plan_admissions:
    for component in admission["spec"]["data"]["mapping"]["components"]:
        all_components.append( (admission["metadata"]["name"], component) )
@pytest.mark.parametrize("admission_name,component", all_components )
def test_components_in_release_plan_admissions(admission_name,component):
    assert re.search(rf'{release.version.hyphen}', component["name"]), f"{admission_name}: component name {component['name']} does not have {release.version.hyphen} in it"

