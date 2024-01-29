#!/usr/bin/env python
from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase
from ansible.module_utils.common.text.converters import to_text, to_native


class LookupModule(LookupBase):
    def run(self, terms, variables=None, **kwargs):
        ret = []

        try:
            for path in terms:
                with open(path, "rb") as byte_stream:
                    text = byte_stream.read()
                    ret.append(to_text(text.decode("UTF-16")))
        except Exception as e:
            raise AnsibleError(to_native(repr(e)))

        return ret
