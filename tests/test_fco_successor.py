#!/usr/bin/env python3
import hashlib, importlib.util, json, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("fco_successor",ROOT/"scripts/fco_successor.py")
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

class SuccessorTests(unittest.TestCase):
    def test_canonicalization(self):
        self.assertEqual(m.canonical({"b":1,"a":2}),b'{"a":2,"b":1}')
    def test_fco_identity(self):
        x=m.make_fco("TEST","IMPLEMENTED",{"x":1})
        body={k:v for k,v in x.items() if k not in {"fco_id","content_sha256"}}
        self.assertEqual(x["content_sha256"],hashlib.sha256(m.canonical(body)).hexdigest())
    def test_schema_fields(self):
        schema=json.loads((ROOT/"schemas/fco.schema.json").read_text())
        for key in ("fco_id","fco_type","content_sha256","canonicalization","execution_state"):
            self.assertIn(key,schema["required"])
    def test_states_preserved(self):
        schema=json.loads((ROOT/"schemas/fco.schema.json").read_text())
        self.assertEqual(set(schema["properties"]["execution_state"]["enum"]),m.STATES)

if __name__=="__main__": unittest.main()
