"""Dependency-light command-line interface."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .bronze import ingest_local_file, write_manifest
from .gold import classify_modality
from .graph import load_graph
from .graphrag import retrieve_graph_context
from .institutional import run_institutional_gap_analysis
from .nlp import analyse_with_spacy
from .local_runner import prepare_local_document
from .offline_bundle import build_bundle, verify_bundle
from .source_registry import load_registry


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="au-health-policy-atlas")
    sub = parser.add_subparsers(dest="command", required=True)

    doctor = sub.add_parser(
        "doctor",
        help="validate bundled source registry and report runtime state",
    )
    doctor.add_argument("--registry", default=None)

    bronze = sub.add_parser(
        "bronze-ingest",
        help="ingest one local source object into content-addressed Bronze storage",
    )
    bronze.add_argument("source_path")
    bronze.add_argument("--source-id", required=True)
    bronze.add_argument("--source-uri", required=True)
    bronze.add_argument("--cas-root", default="build/cas")
    bronze.add_argument("--manifest", default="build/bronze/manifest.json")
    bronze.add_argument("--release-id", default="bronze-dev")

    modality = sub.add_parser(
        "classify-modality",
        help="run deterministic normative-modality classification",
    )
    modality.add_argument("text")

    local = sub.add_parser(
        "prepare-local",
        help="prepare a local/sensitive text, HTML, PDF or DOCX document",
    )
    local.add_argument("document")
    local.add_argument("--source-id", required=True)
    local.add_argument("--output-dir", required=True)
    local.add_argument("--spacy", action="store_true", help="emit optional spaCy NLP features")
    local.add_argument(
        "--spacy-model",
        default=None,
        help="qualified spaCy statistical model name; blank English when omitted",
    )
    local.add_argument(
        "--graph",
        action="store_true",
        help="emit rebuildable local medallion graph projection",
    )

    gap = sub.add_parser(
        "institutional-gap",
        help="compare one local policy against a pinned public Gold JSONL baseline",
    )
    gap.add_argument("local_document")
    gap.add_argument("public_gold_jsonl")
    gap.add_argument("--source-id", required=True)
    gap.add_argument("--output-dir", required=True)

    nlp = sub.add_parser(
        "nlp-analyse",
        help="run optional spaCy exact-offset NLP projection",
    )
    nlp.add_argument("text")
    nlp.add_argument("--spacy-model", default=None)

    graph_query = sub.add_parser(
        "graph-query",
        help="run transparent path-preserving GraphRAG retrieval over a derived graph",
    )
    graph_query.add_argument("graph_dir")
    graph_query.add_argument("query")
    graph_query.add_argument("--top-k", type=int, default=12)
    graph_query.add_argument("--max-hops", type=int, default=2)

    bundle = sub.add_parser(
        "bundle-build",
        help="build a content-addressed offline comparison bundle",
    )
    bundle.add_argument("--output-dir", required=True)
    bundle.add_argument("--bundle-id", required=True)
    bundle.add_argument("files", nargs="+")

    verify = sub.add_parser(
        "bundle-verify",
        help="verify an offline bundle without network access",
    )
    verify.add_argument("bundle_dir")
    return parser


def _print_json(payload: object) -> None:
    print(json.dumps(payload, sort_keys=True))


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "doctor":
        registry = load_registry(args.registry)
        _print_json({"status": "ok", "source_count": len(registry["sources"])})
        return 0
    if args.command == "bronze-ingest":
        obj = ingest_local_file(
            args.source_path,
            source_id=args.source_id,
            source_uri=args.source_uri,
            cas_root=args.cas_root,
        )
        manifest = write_manifest(
            [obj],
            args.manifest,
            release_id=args.release_id,
        )
        _print_json(manifest)
        return 0
    if args.command == "classify-modality":
        result = classify_modality(args.text)
        _print_json(
            {
                "modality": result.modality,
                "deterministic": result.deterministic,
                "reason_code": result.reason_code,
            }
        )
        return 0
    if args.command == "prepare-local":
        receipt = prepare_local_document(
            args.document,
            source_id=args.source_id,
            output_dir=args.output_dir,
            use_spacy=args.spacy,
            spacy_model=args.spacy_model,
            build_graph_projection=args.graph,
        )
        _print_json(receipt)
        return 0
    if args.command == "institutional-gap":
        receipt = run_institutional_gap_analysis(
            local_document=args.local_document,
            local_source_id=args.source_id,
            public_gold_jsonl=args.public_gold_jsonl,
            output_dir=args.output_dir,
        )
        _print_json(receipt)
        return 0
    if args.command == "nlp-analyse":
        _print_json(analyse_with_spacy(args.text, model_name=args.spacy_model).as_dict())
        return 0
    if args.command == "graph-query":
        graph = load_graph(args.graph_dir)
        context = retrieve_graph_context(
            graph,
            args.query,
            top_k=args.top_k,
            max_hops=args.max_hops,
        )
        _print_json(context.as_dict())
        return 0
    if args.command == "bundle-build":
        manifest = build_bundle(
            files=args.files,
            output_dir=args.output_dir,
            bundle_id=args.bundle_id,
        )
        _print_json(manifest)
        return 0
    if args.command == "bundle-verify":
        ok, failures = verify_bundle(args.bundle_dir)
        _print_json({"verified": ok, "failures": failures})
        return 0 if ok else 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
