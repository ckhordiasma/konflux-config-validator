from ruamel.yaml import YAML
from pathlib import Path
import re

WORK_DIR_STR="konflux-release-data/tenants-config/cluster/stone-prod-p02/tenants/rhoai-tenant/"
WORK_DIR = Path(WORK_DIR_STR)
yaml=YAML(typ='safe')   # default, if not specfied, is 'rt' (round-trip)

v_release = 'v2.20'
xyz_release = '2.20.0'
hyphen_release = re.sub('\.', '-', v_release)

def test_top_level_kustomization():
    filename = 'kustomization.yaml'
    data = yaml.load(WORK_DIR / filename)
    assert f'{v_release}/' in data["resources"], "Release folder is included in top level kustomization"


def test_release_level_kustomization():
    data = yaml.load(WORK_DIR / v_release / 'kustomization.yaml')
    for item in data["resources"]:
        assert re.search(v_release, item), "All resources have correct version"

def test_release_plans():
    filename = f"ProdReleasePlans-{v_release}.yaml" 
    data = list(yaml.load_all(WORK_DIR / v_release / filename))
    assert data, f"{filename} file exists"
    assert len(data) > 1, "f{filename} contains multiple subdocuments"
    for release_plan in data:
        name = release_plan["metadata"]["name"]
        application = release_plan["spec"]["application"]
        assert re.search(hyphen_release, name), f"{name} has {hyphen_release} in the name"
        assert re.search(hyphen_release, application), f"{name} has {hyphen_release} in the application"
        assert re.search(hyphen_release, release_plan["metadata"]["labels"]["release.appstudio.openshift.io/releasePlanAdmission"]), f"{name} has {hyphen_release} in the releasePlanAdmission"

        if re.search('^rhoai-fbc-fragment', application):
            # fbc-fragment processing
            pass
        elif re.search(f'^rhoai-', application):
            # component processing
            description = release_plan["spec"]["data"]["releaseNotes"]["description"]
            synopsis = release_plan["spec"]["data"]["releaseNotes"]["synopsis"]
            solution = release_plan["spec"]["data"]["releaseNotes"]["solution"]
            for item in (description, synopsis, solution):
                assert re.search(xyz_release, item), f"{name} has correct version listed in release notes"
        else:
            assert false, f"{filename} contains only valid subdocuments"
