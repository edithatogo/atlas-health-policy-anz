"""Bounded one-off original public policy PDF transport; not medallion qualification."""
from __future__ import annotations
import hashlib
import ipaddress
import json
import re
import socket
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MAX_BYTES = 32 * 1024 * 1024
HOSTS = frozenset({"www.health.qld.gov.au", "www.cairns-hinterland.health.qld.gov.au", "www.treasury.qld.gov.au", "www.forgov.qld.gov.au", "www.statedevelopment.qld.gov.au", "www.publications.qld.gov.au", "www.qra.qld.gov.au"})

def check_url(url: str, *, resolve: bool = True) -> None:
    parts = urllib.parse.urlsplit(url)
    if parts.scheme != "https" or parts.hostname not in HOSTS or parts.username or parts.password or parts.port not in (None, 443):
        raise ValueError("URL outside exact public HTTPS allowlist")
    if resolve:
        addresses = socket.getaddrinfo(parts.hostname, 443, type=socket.SOCK_STREAM)
        if not addresses or any(not ipaddress.ip_address(row[4][0]).is_global for row in addresses):
            raise ValueError("non-public DNS resolution")

class CheckedRedirect(urllib.request.HTTPRedirectHandler):
    max_redirections = 3
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        check_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)

def validate_body(body: bytes, media_type: str) -> None:
    if len(body) > MAX_BYTES:
        raise ValueError("document exceeds size budget")
    if media_type not in ("application/pdf", "application/octet-stream"):
        raise ValueError("response is not a PDF media type; no challenge bypass attempted")
    if not body.startswith(b"%PDF-") or b"%%EOF" not in body[-65536:]:
        raise ValueError("PDF signature/end marker absent; body not retained")

def capture(item: dict) -> dict:
    sid, url = item["source_id"], item["url"]
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{2,80}", sid):
        raise ValueError("invalid source_id")
    result = dict(item, observed_at=datetime.now(timezone.utc).isoformat(), status="capture_failed", sha256=None, size_bytes=None, stored_path=None, parsing_qualified=False)
    if item.get("mirror_authorized") is not True:
        result.update(status="rights_pending", error="original not mirrored without a rights disposition")
        return result
    try:
        check_url(url)
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), CheckedRedirect())
        request = urllib.request.Request(url, headers={"User-Agent": "AtlasHealthPolicyANZ/1.0 (bounded public policy archive; no crawling)", "Accept": "application/pdf", "Accept-Encoding": "identity"})
        with opener.open(request, timeout=40) as response:
            result["http_status"] = response.status
            result["final_url"] = response.url
            check_url(response.url)
            result["media_type"] = response.headers.get_content_type()
            result["etag"] = response.headers.get("ETag")
            result["last_modified"] = response.headers.get("Last-Modified")
            body = response.read(MAX_BYTES + 1)
        validate_body(body, result["media_type"])
        digest = hashlib.sha256(body).hexdigest()
        relative = Path("originals") / f"{sid}--{digest[:16]}.pdf"
        target = ROOT / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() and target.read_bytes() != body:
            raise ValueError("immutable destination collision")
        target.write_bytes(body)
        if hashlib.sha256(target.read_bytes()).hexdigest() != digest:
            raise ValueError("post-write fixity failure")
        result.update(status="captured_original", sha256=digest, size_bytes=len(body), stored_path=relative.as_posix(), pdf_signature_checked=True)
    except (OSError, ValueError, urllib.error.URLError) as exc:
        result["error"] = f"{type(exc).__name__}: {str(exc)[:600]}"
    return result

def main() -> None:
    request = json.loads((ROOT / "request.json").read_text(encoding="utf-8"))
    if len(request["sources"]) > 20 or len({item["source_id"] for item in request["sources"]}) != len(request["sources"]):
        raise ValueError("source count or identity outside bounded packet")
    results = []
    for item in request["sources"]:
        result = capture(item)
        results.append(result)
        print(item["source_id"], result["status"], flush=True)
        time.sleep(1)
    manifest = {"schema_version": "source-packet-1.0", "packet_id": request["packet_id"], "qualification": "source_staging_only_not_bronze_closure", "evaluation_included": False, "hugging_face_write": False, "source_count": len(results), "captured_count": sum(x["status"] == "captured_original" for x in results), "objects": results, "limitations": ["PDF magic and EOF checks are not full parser or malware qualification", "Edition observations require revalidation if bytes change", "No semantic assertions, policy compliance certification or complete corpus claim"]}
    payload = json.dumps(manifest, indent=2, ensure_ascii=False).encode() + b"\n"
    (ROOT / "capture-manifest.json").write_bytes(payload)
    (ROOT / "capture-manifest.sha256").write_text(hashlib.sha256(payload).hexdigest() + "  capture-manifest.json\n")
    if not manifest["captured_count"]:
        raise SystemExit("No originals captured; failure manifest retained")

if __name__ == "__main__":
    main()
