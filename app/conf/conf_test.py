from dataclasses import dataclass
from pathlib import Path

from omegaconf import OmegaConf

conf = OmegaConf.create()
print(conf)
print(type(conf))

conf = OmegaConf.create({"k" : "v", "list" : [1, {"a": "1", "b": "2", 3: "c"}]})
print(type(conf))
print(OmegaConf.to_yaml(conf))
print(type(OmegaConf.to_yaml(conf)))

user_yaml_conf = Path(__file__).parents[2] / 'conf' / 'conf_test.yaml'
print(user_yaml_conf)
conf = OmegaConf.load(user_yaml_conf)
print(type(conf))
print(OmegaConf.to_yaml(conf))

@dataclass
class UserConfig:
    name:str
    age:int
    gender:str

content = OmegaConf.load(user_yaml_conf)
structured = OmegaConf.structured(UserConfig)
merge = OmegaConf.merge(structured, content)

user_config:UserConfig = OmegaConf.to_object(merge)
print(user_config.name)