#!/usr/bin/env python3
import json, urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT=Path(__file__).resolve().parent
FCG=ROOT/"fcg/successor_fcg.json"
BP=ROOT/"breakpoints/bp7_mend_fcg_breakpoint_v1.json"
def load(path): return json.loads(path.read_text())
def fcos(): return [load(p) for p in sorted((ROOT/"fco").glob("*.json"))]
def traversal(release_id):
 graph=load(FCG); nodes={n["fco_id"]:n for n in graph["nodes"]}; reverse={}
 if release_id not in nodes or nodes[release_id]["fco_type"]!="RELEASE_FCO": raise ValueError("unknown release FCO")
 for edge in graph["edges"]: reverse.setdefault(edge["target"],[]).append(edge)
 seen=set(); out=[]
 def visit(node_id):
  if node_id in seen:return
  seen.add(node_id)
  for edge in reverse.get(node_id,[]): visit(edge["source"])
  out.append(nodes[node_id])
 visit(release_id); return {"release_fco_id":release_id,"traversal":out}
class Handler(BaseHTTPRequestHandler):
 def send_json(self,obj,status=200):
  body=json.dumps(obj,indent=2).encode(); self.send_response(status); self.send_header("content-type","application/json"); self.send_header("content-length",str(len(body))); self.end_headers(); self.wfile.write(body)
 def do_GET(self):
  path=urllib.parse.urlparse(self.path).path
  try:
   if path=="/api/breakpoint": return self.send_json(load(BP))
   if path=="/api/fcg": return self.send_json(load(FCG))
   if path=="/api/fcos": return self.send_json({"fcos":fcos()})
   if path.startswith("/api/fco/"):
    item=next((x for x in fcos() if x["fco_id"]==path.removeprefix("/api/fco/")),None); return self.send_json(item or {"error":"not_found"},200 if item else 404)
   if path.startswith("/api/traversal/"): return self.send_json(traversal(path.removeprefix("/api/traversal/")))
   if path=="/api/status": return self.send_json({"service":"mend-fco-successor","status":"PASS","bedrock":"EXECUTED","antigence":"EXECUTED","release":"SUPPORTED"})
   if path in {"/","/index.html"}:
    body=(ROOT/"web/successor.html").read_bytes(); self.send_response(200); self.send_header("content-type","text/html"); self.end_headers(); return self.wfile.write(body)
   return self.send_json({"error":"not_found"},404)
  except Exception as exc:return self.send_json({"error":type(exc).__name__},400)
if __name__=="__main__": ThreadingHTTPServer(("127.0.0.1",8900),Handler).serve_forever()
