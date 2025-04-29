from ruamel.yaml import YAML
from pathlib import Path
import pytest
import re

yaml=YAML(typ='safe') 


class Version:
    def __init__(self, xyz):
        self.xyz = xyz
        xyz_regex = re.search(r'^(\d+)\.(\d+)\.(\d+)$', self.xyz)
        assert xyz_regex, f"{self.xyz} matches pattern X.Y.Z"
        self.x = xyz_regex[1]
        self.y = xyz_regex[2]
        self.z = xyz_regex[3]
        # v - starts with v, uses dots
        self.v = f'v{self.x}.{self.y}'
        # hyphen - starts with v, uses hyphens
        self.hyphen = f'v{self.x}-{self.y}'

class Release:
    def __init__(self, xyz, ocp_versions, addon_ocp_version):
        self.version = Version(xyz)
        self.ocp_versions = ocp_versions
        self.addon_ocp_version = addon_ocp_version

@pytest.fixture
def release():
   return Release('2.20.0', ["414", "415", "416", "417", "418", "419"], "416") 

@pytest.fixture
def p02_paths(release):
    version = release.version
    TENANT_DIR_STR="konflux-release-data/tenants-config/cluster/stone-prod-p02/tenants/rhoai-tenant/"
    tenant_dir = Path(TENANT_DIR_STR)
    version_dir = tenant_dir / version.v
    prod_release_plan = version_dir / f"ProdReleasePlans-{version.v}.yaml"
    stage_release_plan = version_dir / f"StageReleasePlans-{version.v}.yaml"

    return { 
            "tenant": tenant_dir, 
            "version": version_dir,
            "prod_release_plan": prod_release_plan,
            "stage_release_plan": stage_release_plan,
            }


def test_top_level_kustomization(p02_paths, release):
    version = release.version
    filename = 'kustomization.yaml'
    data = yaml.load(p02_paths["tenant"] / filename)
    assert f'{version.v}/' in data["resources"], "Release folder is included in top level kustomization"


def test_release_level_kustomization(p02_paths, release):
    version = release.version
    data = yaml.load(p02_paths["version"] / 'kustomization.yaml')
    for item in data["resources"]:
        assert re.search(version.v, item), "All resources have correct version"



# Checks that apply to all release plan specs, stage and prod
def validate_release_plans(release_plan, release):
    version = release.version
    name = release_plan["metadata"]["name"]
    assert re.search(version.hyphen, name), f"{name} has {version.hyphen} in the name"
    assert re.search(version.hyphen, release_plan["metadata"]["labels"]["release.appstudio.openshift.io/releasePlanAdmission"]), f"{name} has {version.hyphen} in the releasePlanAdmission"

# Checks that apply to all component release plan specs
def validate_component_release_plans(release_plan, release):
    version = release.version
    application = release_plan["spec"]["application"]
    name = release_plan["metadata"]["name"]
    assert re.search(version.hyphen, application), f"{name} has {version.hyphen} in the application name"
    release_notes_sections = ["description", "synopsis", "solution"]
    for item in release_notes_sections:
        section = release_plan["spec"]["data"]["releaseNotes"][item]
        assert re.search(version.xyz, section), f"{name} has correct version listed in the {item} section of the release notes"


# Validate fbc managed release plans
def validate_fbc_release_plans(release_plan, release):
    version = release.version

    application = release_plan["spec"]["application"]
    name = release_plan["metadata"]["name"]
    # filters out addon releases and component releases
    listed_ocp_version_regex = re.search(r'ocp-(\d+)$', application)
    assert listed_ocp_version_regex, f"{name} references application '{application}' with expected ocp suffix"
    listed_ocp_version = listed_ocp_version_regex[1]
    assert re.search(listed_ocp_version, name), f"ocp version in plan name: '{name}' is consistent with application: '{application}'"
    assert listed_ocp_version in release.ocp_versions, f"ocp version {listed_ocp_version} is in the expected list {release.ocp_versions}"

    return listed_ocp_version

def validate_addon_fbc_release_plans(release_plan, release):
    version = release.version
    addon_ocp_version = release.addon_ocp_version
    listed_ocp_version = validate_fbc_release_plans(release_plan, release)
    assert listed_ocp_version == addon_ocp_version, f"addon ocp version {listed_ocp_version} should match expected {addon_ocp_version}"



def validate_all_release_plans(release_plan_path, release):
    data = list(yaml.load_all(release_plan_path))
    filename = release_plan_path.name
    has_ocp_versions = {v: False for v in release.ocp_versions}
    assert data, f"{filename} file exists"
    assert len(data) > 1, "f{filename} contains multiple subdocuments"
    n_release_plans = {"managed": 0, "component": 0, "addon": 0}

    for release_plan in data:
        application = release_plan["spec"]["application"]
        name = release_plan["metadata"]["name"]
        validate_release_plans(release_plan, release)

        if re.search('^rhoai-onprem', name) and re.search('^rhoai-v', application):
            validate_component_release_plans(release_plan, release)
            n_release_plans["component"] += 1

        elif re.search('^rhoai-onprem', name) and re.search('^rhoai-fbc-fragment', application):
            n_release_plans["managed"] += 1
            listed_ocp_version = validate_fbc_release_plans(release_plan, release)
            assert has_ocp_versions[listed_ocp_version] == False, f"No duplicate releaseplan admissions for {listed_ocp_version} unless it is {release.addon_ocp_version}"
            has_ocp_versions[listed_ocp_version] = True

        elif re.search('^rhoai-addon', name):
            n_release_plans["addon"] += 1
            validate_addon_fbc_release_plans(release_plan, release)
        else:
            assert False, f"{filename} only contains release plans with application:{application} and name:{name} that match expected patterns"

    assert n_release_plans["managed"] == len(release.ocp_versions), f"There are exactly {len(release.ocp_versions)} fbc release plans"
    assert n_release_plans["component"] == 1, f"There is exactly one component release plan"
    return n_release_plans

def test_stage_release_plans(p02_paths, release):
    version = release.version
    release_plan_path = p02_paths["stage_release_plan"]
    n_release_plans = validate_all_release_plans(release_plan_path, release)
    assert n_release_plans["addon"] == 1, "There is exactly one addon release in the stage release plan"


def test_prod_release_plans(p02_paths, release):
    version = release.version
    release_plan_path = p02_paths["prod_release_plan"]
    n_release_plans = validate_all_release_plans(release_plan_path, release)
    assert n_release_plans["addon"] == 0, "There are zero addon releases in the prod release plan"

