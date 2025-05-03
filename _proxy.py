# -*- coding: utf-8 -*-

import importlib

class proxyObj:
    def __init__(self, module_name, attr_name):
        self._module_name = module_name
        self._attr_name = attr_name
        self._value = None
        self._loaded = False
        self._import_error = None

    def _load(self):
        if not self._loaded:
            try:
                module = importlib.import_module(self._module_name)
                attr = getattr(module, self._attr_name)
                if callable(attr):
                    self._value = attr()
                else:
                    self._value = attr
                self._loaded = True
            except Exception as e:
                self._import_error = e
        if self._import_error:
            raise ImportError(f"Failed to load {self._attr_name} from {self._module_name}: {self._import_error}")
        return self._value

    def __getattr__(self, name):
        return getattr(self._load(), name)

    def __call__(self, *args, **kwargs):
        return self._load()(*args, **kwargs)

    def __dir__(self):
        try:
            real_obj = self._load()
            return dir(real_obj)
        except Exception:
            return super().__dir__()

    def __repr__(self):
        return f"<proxyObj {self._module_name}.{self._attr_name}>"
