"""Lets the asst modules import where the YOLO stack (ultralytics,
huggingface_hub) is not installed. The tests replace the model anyway;
when the real packages are installed they are used as-is.
"""

import importlib.util
import sys
import types

_STUBS = {
    "ultralytics": {"YOLO": object},
    "huggingface_hub": {"hf_hub_download": lambda *args, **kwargs: ""},
}

for _name, _attributes in _STUBS.items():
    if importlib.util.find_spec(_name) is None:
        _module = types.ModuleType(_name)
        for _attribute, _value in _attributes.items():
            setattr(_module, _attribute, _value)
        sys.modules[_name] = _module
