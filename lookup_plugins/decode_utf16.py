#!/usr/bin/env python
from ansible.errors import AnsibleError
from ansible.module_utils.common.text.converters import to_native
from ansible.plugins.lookup import LookupBase
import base64


class LookupModule(LookupBase):
    def run(self, terms, variables=None, **kwargs):
        ret = []

        try:
            for term in terms:
                decoded = base64.b64decode(term).decode("utf-16")
                ret.append(decoded)
        except Exception as e:
            raise AnsibleError(to_native(repr(e)))

        return ret
