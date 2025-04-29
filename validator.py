from ruamel.yaml import YAML
from pathlib import Path
import pytest
import re

yaml=YAML(typ='safe')   # default, if not specfied, is 'rt' (round-trip)


class Version:
    def __init__(self):
        self.xyz = '2.20.0'
        self.v = 'v2.20'
        self.hyphen = 'v2-20'
        self.ocp_versions = ["414", "415", "416", "417", "418", "419"]
    def __repr__(self):
        return self.v

@pytest.fixture
def version():
   return Version() 

@pytest.fixture
def p02_paths(version):
    TENANT_DIR_STR="konflux-release-data/tenants-config/cluster/stone-prod-p02/tenants/rhoai-tenant/"
    tenant_dir = Path(TENANT_DIR_STR)
    version_dir = tenant_dir / version.v
    prod_release_plan = version_dir / f"ProdReleasePlans-{version}.yaml"
    return { 
            "tenant": tenant_dir, 
            "version": version_dir,
            "prod_release_plan": prod_release_plan
            }



def test_top_level_kustomization(p02_paths, version):
    filename = 'kustomization.yaml'
    data = yaml.load(p02_paths["tenant"] / filename)
    assert f'{version}/' in data["resources"], "Release folder is included in top level kustomization"


def test_release_level_kustomization(p02_paths, version):
    data = yaml.load(p02_paths["version"] / 'kustomization.yaml')
    for item in data["resources"]:
        assert re.search(version.v, item), "All resources have correct version"

# Check release plan config that is common across both component and fbc release plan types
def test_release_plans(p02_paths, version):
    data = list(yaml.load_all(p02_paths["prod_release_plan"]))
    filename = p02_paths["prod_release_plan"].name

    assert data, f"{filename} file exists"
    assert len(data) > 1, "f{filename} contains multiple subdocuments"
    for release_plan in data:
        name = release_plan["metadata"]["name"]
        assert re.search(version.hyphen, name), f"{name} has {version.hyphen} in the name"
        assert re.search(version.hyphen, release_plan["metadata"]["labels"]["release.appstudio.openshift.io/releasePlanAdmission"]), f"{name} has {version.hyphen} in the releasePlanAdmission"

# Validate the component release plan
def test_component_release_plan(p02_paths, version):
    data = list(yaml.load_all(p02_paths["prod_release_plan"]))
    filename = p02_paths["prod_release_plan"].name
    n = 0
    for release_plan in data:
        application = release_plan["spec"]["application"]
        name = release_plan["metadata"]["name"]
        if re.search('^rhoai-fbc-fragment', application):
            continue
        n += 1
        assert re.search(version.hyphen, application), f"{name} has {version.hyphen} in the application name"
        release_notes_sections = ["description", "synopsis", "solution"]
        for item in release_notes_sections:
            section = release_plan["spec"]["data"]["releaseNotes"][item]
            assert re.search(version.xyz, section), f"{name} has correct version listed in the {item} section of the release notes"
    assert n == 1, f"There is only one component release plan"



# Validate the component release plan
def test_fbc_release_plans(p02_paths, version):
    data = list(yaml.load_all(p02_paths["prod_release_plan"]))
    filename = p02_paths["prod_release_plan"].name
    n = 0
    has_ocp_versions = {v: False for v in version.ocp_versions}

    for release_plan in data:
        application = release_plan["spec"]["application"]
        name = release_plan["metadata"]["name"]
        if not re.search('^rhoai-fbc-fragment', application):
            continue
        n += 1
        listed_ocp_version_regex = re.search(r'ocp-(\d+)$', application)
        assert listed_ocp_version_regex, f"{name} references application '{application}' with expected ocp suffix"
        listed_ocp_version = listed_ocp_version_regex[1]
        assert re.search(listed_ocp_version, name), f"ocp version in '{name}' is consistent with '{application}'"
        assert listed_ocp_version in version.ocp_versions, f"ocp version {listed_ocp_version} is in the expected list {version.ocp_versions}"
        assert has_ocp_versions[listed_ocp_version] == False, f"No duplicate releaseplan admissions for {listed_ocp_version}"
        has_ocp_versions[listed_ocp_version] = True

    assert n == len(version.ocp_versions), f"There are exactly {len(version.ocp_versions)} fbc release plans"
