from pathlib import Path
import pytest

from ruamel.yaml import YAML

import re
from utils.classes import Version
from utils.classes import Release
yaml=YAML(typ='safe') 


def get_release_paths(release):
    version = release.version
    TENANT_DIR_STR="konflux-release-data/tenants-config/cluster/stone-prod-p02/tenants/rhoai-tenant/"
    tenant_dir = Path(TENANT_DIR_STR)
    version_dir = tenant_dir / version.v
    prod_release_plan = version_dir / f"ProdReleasePlans-{version.v}.yaml"
    stage_release_plan = version_dir / f"StageReleasePlans-{version.v}.yaml"
    project_development_stream = version_dir / f"ProjectDevelopmentStream-{version.v}.yaml"

    release_plan_admissions = [] 

    ADDON_DIR_STR="konflux-release-data/config/stone-prod-p02.hjvn.p1/service/ReleasePlanAdmission/rhoai/"
    addon_dir = Path(ADDON_DIR_STR)
    release_plan_admissions.append({
        "path": addon_dir / f"rhoai-addon-{version.hyphen}-stage.yaml",
        "environment": "stage",
        "is_addon": True,
        "kind": "fbc", })

    ONPREM_DIR_STR="konflux-release-data/config/stone-prod-p02.hjvn.p1/product/ReleasePlanAdmission/rhoai/"

    onprem_dir = Path(ONPREM_DIR_STR)

    release_plan_admissions.append({
        "path": onprem_dir / f"rhoai-onprem-{version.hyphen}-fbc-stage.yaml",
        "environment": "stage",
        "is_addon": False,
        "kind": "fbc",})

    release_plan_admissions.append({
        "path": onprem_dir / f"rhoai-onprem-{version.hyphen}-fbc-prod.yaml",
        "environment": "prod",
        "is_addon": False,
        "kind": "fbc", })

    release_plan_admissions.append({
        "path": onprem_dir / f"rhoai-onprem-{version.hyphen}-components-stage.yaml",
        "environment": "stage",
        "is_addon": False,
        "kind": "component",})

    release_plan_admissions.append({
        "path": onprem_dir / f"rhoai-onprem-{version.hyphen}-components-prod.yaml",
        "environment": "prod",
        "is_addon": False,
        "kind": "component",})

   
    return { 
            "tenant": tenant_dir, 
            "version": version_dir,
            "prod_release_plan": prod_release_plan,
            "stage_release_plan": stage_release_plan,
            "project_development_stream": project_development_stream,
            "release_plan_admissions": release_plan_admissions
            }




def get_release_files(release_paths):
 
    release_plan_admissions = []
    for item in release_paths["release_plan_admissions"]:
        release_plan_admissions.append({
            "manifest": yaml.load(item["path"]),
            "kind": item["kind"],
            "is_addon": item["is_addon"],
            "environment": item["environment"],
            })

  
    stage_release_plans = list(yaml.load_all( release_paths["stage_release_plan"] ))
    prod_release_plans = list(yaml.load_all( release_paths["prod_release_plan"] ))

    project_development_stream = list(yaml.load_all(release_paths["project_development_stream"]))

    release_plans = []
    for manifest in stage_release_plans:
        application = manifest["spec"]["application"]
        name = manifest["metadata"]["name"]
        kind, is_addon = identify_release_plan(manifest)
        release_plans.append({ 
                              "manifest": manifest,
                              "kind": kind,
                              "is_addon": is_addon,
                              "environment": "stage", })

    for manifest in prod_release_plans:
        application = manifest["spec"]["application"]
        name = manifest["metadata"]["name"]
        kind, is_addon = identify_release_plan(manifest)
        release_plans.append({ 
                              "manifest": manifest,
                              "kind": kind,
                              "is_addon": is_addon,
                              "environment": "prod", })
    
    return { 
            "release_plans": release_plans,
            "project_development_stream": project_development_stream,
            "release_plan_admissions": release_plan_admissions
            }

def identify_release_plan(manifest):
    application = manifest["spec"]["application"]
    name = manifest["metadata"]["name"]
    is_addon = False

    if re.search('^rhoai-onprem', name) and re.search('^rhoai-v', application):
        kind = "component"
    elif re.search('^rhoai-onprem', name) and re.search('^rhoai-fbc-fragment', application):
        kind = "fbc"

    elif re.search('^rhoai-addon', name):
        kind = "fbc"
        is_addon = True
    else:
        kind = "unknown"
    return (kind, is_addon)

release = Release('2.24.0', "416")

release_paths = get_release_paths(release)
release_files = get_release_files(release_paths)
