import re
import urllib.request
from ruamel.yaml import YAML

yaml=YAML(typ='safe') 
class Version:
    def __init__(self, xyz):
        self.xyz = xyz
        xyz_regex = re.search(r'^(\d+)\.(\d+)\.(\d+)$', self.xyz)
        assert xyz_regex, f"{self.xyz} matches pattern X.Y.Z"
        self.x = xyz_regex[1]
        self.y = xyz_regex[2]
        self.z = xyz_regex[3]

        self.xy = f'{self.x}.{self.y}'
        # v - starts with v, uses dots
        self.v = f'v{self.xy}'
        # hyphen - starts with v, uses hyphens
        self.hyphen = f'v{self.x}-{self.y}'
        self.branch = f'rhoai-{self.x}.{self.y}'

class Release:
    def __init__(self, xyz, addon_ocp_version):
        self.version = Version(xyz)

        RHOAI_BUILD_CONFIG_REPO="https://github.com/red-hat-data-services/RHOAI-Build-Config"
        build_config_url=f"https://raw.githubusercontent.com/red-hat-data-services/RHOAI-Build-Config/refs/heads/{self.version.branch}/config/build-config.yaml" 
        with urllib.request.urlopen(build_config_url) as f:
            self.build_config = yaml.load(f.read().decode('utf-8'))["config"]
        
        # convert from the build config version format vX.Y into just XY
        self.ocp_versions = [ re.sub(r'[v\.]',"", item) for item in self.build_config["supported-ocp-versions"]["release"] ]
        self.addon_ocp_version = addon_ocp_version
        self.build_ocp_versions = [ re.sub(r'[v\.]',"", item["name"]) for item in self.build_config["supported-ocp-versions"]["build"] ] 
