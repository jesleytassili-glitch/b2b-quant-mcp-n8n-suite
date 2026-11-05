#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sindicador Externo OpenAPI 3.0.3 & Catálogo `apis.json` (`APIs.guru` / `GitHub Pages` / `Release v2.2.0`)
(`rapidapi_zyla_hub_suite/openapi_syndicator_2026.py`).

Responsabilidades:
1. Sincroniza as 31 especificações individuais `OpenAPI 3.0.3` (`specs_openapi_31/*.json`),
   o catálogo padrão `apis.json` (`/.well-known/apis.json` — API Commons / APIs.guru v0.16),
   o `pricing_plans_manifest.json`, a coleção `postman_public_network_collection.json` e o
   Gateway Stateless (`rapidapi_zyla_gateway.py` + `cloudflare_worker_proxy.js`) nos repositórios
   `jesleytassili-glitch/b2b-quant-mcp-n8n-suite` e `jesleytassili-glitch/jesleytassili-glitch.github.io`;
2. Publica em um único commit atômico via GitHub Git Data API (Tree/Commit/Ref) todas as 31
   especificações em `https://jesleytassili-glitch.github.io/specs_openapi_31/<slug>.json` e
   `https://jesleytassili-glitch.github.io/apis.json`;
3. Publica a **GitHub Release `v2.2.0`** anexando o bundle `b2b-quant-mcp-n8n-suite-v2.2.0.zip`
   (31 specs OpenAPI 3.0.3 + Gateway Stateless + 37 workflows n8n + 31 servidores MCP);
4. Valida ao vivo a acessibilidade `HTTP 200` das 31 URLs públicas `OpenAPI 3.0.3` e do `/apis.json`,
   dispara o ping instantâneo `IndexNow` e salva `openapi_syndication_receipt.json`.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
import os
import shutil
import subprocess
import sys
import time
import zipfile
from pathlib import Path
from typing import Any

import httpx

SUITE_DIR = Path(__file__).resolve().parent
WORKSPACE_ROOT = SUITE_DIR.parent
APIFY_SUITE_DIR = WORKSPACE_ROOT / "apify_store_suite"

for p in (WORKSPACE_ROOT, APIFY_SUITE_DIR, SUITE_DIR):
    p_str = str(p)
    if p.exists() and p_str not in sys.path:
        sys.path.insert(0, p_str)

from deploy_apify_suite import ACTOR_SLUGS
from publish_github_distribution_repo import (
    DIST_DIR,
    GITHUB_OWNER,
    GITHUB_REPO,
    REPO_BUILD_DIR,
    load_env_token,
)
from rapidapi_zyla_hub_suite.generate_rapidapi_zyla_specs import (
    APIS_JSON_OUTPUT_PATH,
    DEFAULT_GATEWAY_BASE_URL,
    ENGINE_VERSION,
    GITHUB_RELEASE_TAG,
    POSTMAN_COLLECTION_OUTPUT_PATH,
    PUBLIC_APIS_JSON_URL,
    PUBLIC_GITHUB_PAGES_ORIGIN,
    PUBLIC_SPECS_BASE_URL,
    PUBLIC_SUITE_SPECS_BASE_URL,
    PUBLIC_WELL_KNOWN_APIS_JSON_URL,
    SPECS_OUTPUT_DIR,
    WISE_ACCOUNT_NUMBER,
    generate_all_31_openapi_specs,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("openapi_syndicator_2026")

INDEXNOW_KEY = "b2bquantapis2026indexnowkey890361"
RELEASE_TAG_V2_2 = GITHUB_RELEASE_TAG
SYNDICATION_RECEIPT_PATH = SUITE_DIR / "openapi_syndication_receipt.json"

OPENAPI_GITHUB_TOPICS: list[str] = [
    "mcp",
    "mcp-server",
    "model-context-protocol",
    "x402",
    "solana",
    "ai-agents",
    "b2b-api",
    "n8n",
    "n8n-workflows",
    "apify",
    "apify-actors",
    "kyb",
    "sec-edgar",
    "clinical-trials",
    "cisa-kev",
    "gleif",
    "claude-desktop",
    "cursor-mcp",
    "openapi",
    "rapidapi",
]


def sync_openapi_31_and_apis_json_to_repos(
    repo_dir: Path = REPO_BUILD_DIR,
    dist_dir: Path = DIST_DIR,
    specs_dir: Path = SPECS_OUTPUT_DIR,
    gateway_url: str = DEFAULT_GATEWAY_BASE_URL,
) -> dict[str, Any]:
    """
    Gera as 31 especificações OpenAPI 3.0.3, `apis.json`, `pricing_plans_manifest.json` e
    `postman_public_network_collection.json`, copiando todos os artefatos e o Gateway Stateless
    para `repo_dir`, `repo_dir/docs` e `dist_dir`.
    """
    from rapidapi_zyla_hub_suite.rapidapi_provider_deployer import (
        ACTIVATION_PLAYBOOK_PATH,
        PRICING_MANIFEST_PATH,
        build_activation_playbook_markdown,
        build_pricing_plans_manifest,
    )

    generate_all_31_openapi_specs(output_dir=specs_dir, gateway_url=gateway_url)
    manifest = build_pricing_plans_manifest(specs_dir=specs_dir, gateway_url=gateway_url)
    if PRICING_MANIFEST_PATH.exists():
        try:
            existing_manifest = json.loads(PRICING_MANIFEST_PATH.read_text(encoding="utf-8"))
            if (
                existing_manifest.get("manifestVersion") == manifest.get("manifestVersion")
                and existing_manifest.get("totalApis") == manifest.get("totalApis")
                and existing_manifest.get("generatedAtUtc")
            ):
                manifest["generatedAtUtc"] = existing_manifest["generatedAtUtc"]
        except Exception:
            pass

    PRICING_MANIFEST_PATH.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
        newline="\n",
    )
    ACTIVATION_PLAYBOOK_PATH.write_text(
        build_activation_playbook_markdown(manifest),
        encoding="utf-8",
        newline="\n",
    )

    repo_specs_dir = repo_dir / "specs_openapi_31"
    docs_specs_dir = repo_dir / "docs" / "specs_openapi_31"
    dist_specs_dir = dist_dir / "specs_openapi_31"
    repo_well_known = repo_dir / ".well-known"
    docs_well_known = repo_dir / "docs" / ".well-known"
    repo_suite_mirror = repo_dir / "rapidapi_zyla_hub_suite"
    repo_suite_specs = repo_suite_mirror / "specs_openapi_31"

    for d in (
        repo_specs_dir,
        docs_specs_dir,
        dist_specs_dir,
        repo_well_known,
        docs_well_known,
        repo_suite_mirror,
        repo_suite_specs,
    ):
        d.mkdir(parents=True, exist_ok=True)

    def _safe_copy2(src: Path, dst: Path) -> None:
        if src.resolve() != dst.resolve():
            shutil.copy2(src, dst)

    # 1. Copia as 31 especificações OpenAPI 3.0.3 individuais
    copied_specs: list[str] = []
    for slug in ACTOR_SLUGS:
        src_spec = specs_dir / f"{slug}.json"
        for target_folder in (repo_specs_dir, docs_specs_dir, dist_specs_dir, repo_suite_specs):
            _safe_copy2(src_spec, target_folder / f"{slug}.json")
        copied_specs.append(f"specs_openapi_31/{slug}.json")

    # 2. Copia apis.json (API Commons / APIs.guru) para raiz, .well-known, docs e dist
    for target_apis in (
        repo_dir / "apis.json",
        repo_well_known / "apis.json",
        repo_dir / "docs" / "apis.json",
        docs_well_known / "apis.json",
        dist_dir / "apis.json",
        repo_suite_mirror / "apis.json",
    ):
        _safe_copy2(APIS_JSON_OUTPUT_PATH, target_apis)

    # 3. Copia pricing_plans_manifest.json e postman_public_network_collection.json
    for target_dir in (repo_dir, repo_dir / "docs", dist_dir, repo_suite_mirror):
        _safe_copy2(PRICING_MANIFEST_PATH, target_dir / "pricing_plans_manifest.json")
        _safe_copy2(
            POSTMAN_COLLECTION_OUTPUT_PATH,
            target_dir / "postman_public_network_collection.json",
        )

    # 4. Copia os módulos do Gateway Stateless, Deployer, Sindicador e Importer para `rapidapi_zyla_hub_suite/`
    for filename in (
        "__init__.py",
        "rapidapi_zyla_gateway.py",
        "cloudflare_worker_proxy.js",
        "generate_rapidapi_zyla_specs.py",
        "rapidapi_provider_deployer.py",
        "openapi_syndicator_2026.py",
        "rapidapi_zyla_playwright_importer.py",
        "PUBLICAR_RAPIDAPI_ZYLA.bat",
        "RAPIDAPI_ZYLA_ACTIVATION_PLAYBOOK.md",
    ):
        src_file = SUITE_DIR / filename
        if src_file.exists():
            _safe_copy2(src_file, repo_suite_mirror / filename)

    # 5. Atualiza `docs/sitemap.xml` com as 32 páginas pSEO + catálogos + 31 specs OpenAPI 3.0.3 (66 URLs)
    suite_base_url = f"https://{GITHUB_OWNER}.github.io/{GITHUB_REPO}"
    sitemap_urls: list[str] = [
        f"{suite_base_url}/",
        *[f"{suite_base_url}/actors/{slug}.html" for slug in ACTOR_SLUGS],
        f"{suite_base_url}/apis.json",
        f"{suite_base_url}/pricing_plans_manifest.json",
        f"{suite_base_url}/postman_public_network_collection.json",
        *[f"{suite_base_url}/specs_openapi_31/{slug}.json" for slug in ACTOR_SLUGS],
    ]
    sitemap_entries = "\n".join(
        f"  <url>\n    <loc>{u}</loc>\n    <changefreq>daily</changefreq>\n    <priority>{'1.0' if u.endswith('/') else '0.9'}</priority>\n  </url>"
        for u in sitemap_urls
    )
    sitemap_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{sitemap_entries}\n"
        "</urlset>\n"
    )
    (repo_dir / "docs" / "sitemap.xml").write_text(sitemap_xml, encoding="utf-8", newline="\n")

    return {
        "totalSpecsSynced": len(copied_specs),
        "sitemapUrlsCount": len(sitemap_urls),
        "apisJsonPath": str(APIS_JSON_OUTPUT_PATH),
        "pricingManifestPath": str(PRICING_MANIFEST_PATH),
        "postmanCollectionPath": str(POSTMAN_COLLECTION_OUTPUT_PATH),
        "repoSpecsDir": str(repo_specs_dir),
        "docsSpecsDir": str(docs_specs_dir),
    }


def build_root_origin_index_html(origin_url: str = PUBLIC_GITHUB_PAGES_ORIGIN) -> str:
    """Gera o `index.html` da origem `jesleytassili-glitch.github.io` com links diretos para as 31 specs e `apis.json`."""
    clean_origin = origin_url.rstrip("/")
    suite_url = f"{clean_origin}/b2b-quant-mcp-n8n-suite"
    spec_links = "\n".join(
        f"<li><a href='/specs_openapi_31/{slug}.json'><code>/specs_openapi_31/{slug}.json</code></a> — {slug}</li>"
        for slug in ACTOR_SLUGS
    )
    return (
        "<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>"
        "<title>B2B Quant & Regulatory Compliance Suite — OpenAPI 3.0.3, APIs.guru, x402 & MCP Hub (31 APIs)</title>"
        "<link rel='icon' href='/favicon.ico'>"
        "<link rel='openapi' href='/openapi.json' type='application/json'>"
        "<link rel='api-catalog' href='/apis.json' type='application/apis+json'>"
        "</head><body>"
        "<h1>B2B Quant & Regulatory Compliance Suite (@b2b-quant-apis — 31 OpenAPI 3.0.3 APIs & MCP Servers)</h1>"
        f"<p><a href='{suite_url}/'>Enter Main Portal</a> | "
        "<a href='/apis.json'>apis.json (APIs.guru / API Commons v0.16)</a> | "
        "<a href='/.well-known/apis.json'>/.well-known/apis.json</a> | "
        "<a href='/pricing_plans_manifest.json'>Pricing Plans Manifest (USD -> Wise #890361113)</a> | "
        "<a href='/postman_public_network_collection.json'>Postman v2.1 Collection (31 APIs)</a> | "
        "<a href='/openapi.json'>OpenAPI 3.1.0 (AgentCash x402 + $0.00 Free Tier)</a> | "
        "<a href='/.well-known/x402.json'>x402 Manifest</a> | "
        "<a href='/.well-known/mcp.json'>MCP Registry Manifest</a> | "
        "<a href='/.well-known/agent.json'>A2A Agent Card</a> | "
        "<a href='/llms.txt'>llms.txt</a> | "
        "<a href='/llms-full.txt'>llms-full.txt</a></p>"
        "<h2>31 Individual OpenAPI 3.0.3 Specifications (1-Click Import for RapidAPI, Zyla Hub & Postman)</h2>"
        f"<ul>{spec_links}</ul>"
        "</body></html>"
    )


def publish_openapi_31_to_root_github_pages(
    token: str | None = None,
    specs_dir: Path = SPECS_OUTPUT_DIR,
    http_client: httpx.Client | None = None,
) -> dict[str, Any]:
    """
    Publica as 31 especificações `specs_openapi_31/<slug>.json`, `apis.json`, `.well-known/apis.json`,
    `pricing_plans_manifest.json`, `postman_public_network_collection.json` e `index.html` no repositório
    raiz `jesleytassili-glitch/jesleytassili-glitch.github.io` em um único commit atômico via Git Trees API.
    """
    from rapidapi_zyla_hub_suite.rapidapi_provider_deployer import PRICING_MANIFEST_PATH

    gh_token = token or load_env_token()
    root_repo = f"{GITHUB_OWNER}.github.io"
    headers = {
        "Authorization": f"Bearer {gh_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    text_files_to_publish: dict[str, str] = {
        ".nojekyll": "",
        f"{INDEXNOW_KEY}.txt": INDEXNOW_KEY,
        "apis.json": APIS_JSON_OUTPUT_PATH.read_text(encoding="utf-8"),
        ".well-known/apis.json": APIS_JSON_OUTPUT_PATH.read_text(encoding="utf-8"),
        "pricing_plans_manifest.json": PRICING_MANIFEST_PATH.read_text(encoding="utf-8"),
        "postman_public_network_collection.json": POSTMAN_COLLECTION_OUTPUT_PATH.read_text(encoding="utf-8"),
        "index.html": build_root_origin_index_html(PUBLIC_GITHUB_PAGES_ORIGIN),
    }

    for slug in ACTOR_SLUGS:
        spec_path = specs_dir / f"{slug}.json"
        text_files_to_publish[f"specs_openapi_31/{slug}.json"] = spec_path.read_text(encoding="utf-8")

    tree_entries = [
        {
            "path": rel_path,
            "mode": "100644",
            "type": "blob",
            "content": content_str,
        }
        for rel_path, content_str in text_files_to_publish.items()
    ]

    def _execute_git_tree_push(client: httpx.Client) -> dict[str, Any]:
        ref_url = f"https://api.github.com/repos/{GITHUB_OWNER}/{root_repo}/git/ref/heads/main"
        ref_resp = client.get(ref_url)
        ref_resp.raise_for_status()
        head_commit_sha = ref_resp.json()["object"]["sha"]

        commit_resp = client.get(
            f"https://api.github.com/repos/{GITHUB_OWNER}/{root_repo}/git/commits/{head_commit_sha}"
        )
        commit_resp.raise_for_status()
        base_tree_sha = commit_resp.json()["tree"]["sha"]

        tree_resp = client.post(
            f"https://api.github.com/repos/{GITHUB_OWNER}/{root_repo}/git/trees",
            json={"base_tree": base_tree_sha, "tree": tree_entries},
        )
        tree_resp.raise_for_status()
        new_tree_sha = tree_resp.json()["sha"]

        new_commit_resp = client.post(
            f"https://api.github.com/repos/{GITHUB_OWNER}/{root_repo}/git/commits",
            json={
                "message": (
                    "feat(v3.0): publish 31 OpenAPI 3.0.3 specs, apis.json (APIs.guru v0.16), "
                    "Postman Collection & RapidAPI/Zyla pricing manifest"
                ),
                "tree": new_tree_sha,
                "parents": [head_commit_sha],
            },
        )
        new_commit_resp.raise_for_status()
        new_commit_sha = new_commit_resp.json()["sha"]

        update_ref_resp = client.patch(
            f"https://api.github.com/repos/{GITHUB_OWNER}/{root_repo}/git/refs/heads/main",
            json={"sha": new_commit_sha, "force": False},
        )
        update_ref_resp.raise_for_status()

        return {
            "status": "published_atomic_tree",
            "repository": f"{GITHUB_OWNER}/{root_repo}",
            "commitSha": new_commit_sha,
            "filesPublishedCount": len(tree_entries),
            "specsBaseUrl": PUBLIC_SPECS_BASE_URL,
            "apisJsonUrl": PUBLIC_APIS_JSON_URL,
            "wellKnownApisJsonUrl": PUBLIC_WELL_KNOWN_APIS_JSON_URL,
        }

    if http_client is not None:
        return _execute_git_tree_push(http_client)
    with httpx.Client(headers=headers, timeout=60.0) as local_client:
        return _execute_git_tree_push(local_client)


def build_release_v2_2_0_zip_bundle(
    repo_dir: Path = REPO_BUILD_DIR,
    dist_dir: Path = DIST_DIR,
) -> Path:
    """Empacota o repositório `b2b-quant-mcp-n8n-suite` em `b2b-quant-mcp-n8n-suite-v2.2.0.zip` sem caches nem dumps sensíveis."""
    dist_dir.mkdir(parents=True, exist_ok=True)
    zip_path = dist_dir / f"{GITHUB_REPO}-{RELEASE_TAG_V2_2}.zip"
    forbidden_names = {
        "batch_import_status_report.json",
        "rapidapi_live_apis_dump.json",
        "zyla_live_apis_dump.json",
        ".env",
    }
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in repo_dir.rglob("*"):
            if not file_path.is_file():
                continue
            if ".git" in file_path.parts or "__pycache__" in file_path.parts:
                continue
            if file_path.suffix.lower() in (".pyc", ".pyo") or file_path.name in forbidden_names:
                continue
            zf.write(file_path, file_path.relative_to(repo_dir))
    return zip_path


def publish_github_release_v2_2_0(
    token: str | None = None,
    repo_dir: Path = REPO_BUILD_DIR,
    dist_dir: Path = DIST_DIR,
    push_git: bool = True,
    http_client: httpx.Client | None = None,
) -> dict[str, Any]:
    """
    Faz commit/push do repositório `b2b-quant-mcp-n8n-suite` (quando `push_git=True`) e cria/atualiza
    a **GitHub Release `v2.2.0`** anexando o bundle `b2b-quant-mcp-n8n-suite-v2.2.0.zip`.
    """
    gh_token = token or load_env_token()
    zip_path = build_release_v2_2_0_zip_bundle(repo_dir=repo_dir, dist_dir=dist_dir)
    commit_sha = "local_dry_run"

    if push_git and http_client is None and (repo_dir / ".git").exists():
        remote_url = f"https://x-access-token:{gh_token}@github.com/{GITHUB_OWNER}/{GITHUB_REPO}.git"
        git_env = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}
        subprocess.run(["git", "add", "-A"], cwd=str(repo_dir), check=True, env=git_env)
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(repo_dir),
            capture_output=True,
            text=True,
            check=True,
            env=git_env,
        )
        if status.stdout.strip():
            subprocess.run(
                [
                    "git",
                    "commit",
                    "-m",
                    "feat(v2.2.0): publish 31 OpenAPI 3.0.3 specs, apis.json, Postman Collection & RapidAPI/Zyla Stateless Gateway",
                ],
                cwd=str(repo_dir),
                check=True,
                env=git_env,
            )
        subprocess.run(["git", "push", remote_url, "HEAD:main"], cwd=str(repo_dir), check=True, env=git_env)
        rev = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(repo_dir),
            capture_output=True,
            text=True,
            check=True,
        )
        commit_sha = rev.stdout.strip()

    headers = {
        "Authorization": f"Bearer {gh_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    release_name = (
        "v2.2.0 — 31 OpenAPI 3.0.3 B2B Specs (RapidAPI & Zyla Hub), apis.json (APIs.guru), "
        "Stateless Gateway, 37 n8n Workflows & 31 MCP Servers"
    )
    release_body = (
        "Major **v2.2.0** release of the **@b2b-quant-apis** Multi-Marketplace B2B API, MCP & M2M Suite:\n"
        f"- **31 Individual OpenAPI 3.0.3 Specifications (`specs_openapi_31/*.json`)**: Hosted at `{PUBLIC_SPECS_BASE_URL}/<slug>.json` for 1-Click URL Import on **RapidAPI Studio (Nokia Rapid)**, **Zyla API Hub**, and **Postman Public API Network**;\n"
        f"- **Official `apis.json` Discovery Catalog (`specificationVersion: 0.16`)**: Live at `{PUBLIC_APIS_JSON_URL}` and `{PUBLIC_WELL_KNOWN_APIS_JSON_URL}` for **APIs.guru** and OpenAPI directory crawlers;\n"
        f"- **Stateless Anti-Bypass Gateway (`rapidapi_zyla_gateway.py` + `cloudflare_worker_proxy.js`)**: Constant-time `hmac.compare_digest` verification of `X-RapidAPI-Proxy-Secret` and `X-Zyla-Proxy-Secret` (`HTTP 403` anti-bypass) + 4-tier USD pricing (`BASIC $0/15 req hard limit`, `PRO $19/1k`, `ULTRA $49/5k`, `MEGA $149/25k` -> `Wise #{WISE_ACCOUNT_NUMBER}`);\n"
        "- **37 n8n Automated Workflows & 31 MCP Servers**: 31 Single-Actor Daily Scheduled Templates + 6 Multi-Actor Enterprise Waterfall Pipelines + x402 Solana USDC Gateway."
    )

    def _upsert_release(client: httpx.Client) -> dict[str, Any]:
        rel_check = client.get(
            f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/tags/{RELEASE_TAG_V2_2}"
        )
        if rel_check.status_code == 404:
            rel_resp = client.post(
                f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases",
                json={
                    "tag_name": RELEASE_TAG_V2_2,
                    "target_commitish": "main",
                    "name": release_name,
                    "body": release_body,
                    "draft": False,
                    "prerelease": False,
                },
            )
            rel_resp.raise_for_status()
            rel_data = rel_resp.json()
        else:
            rel_id = rel_check.json().get("id")
            rel_resp = client.patch(
                f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/{rel_id}",
                json={"name": release_name, "body": release_body},
            )
            rel_data = rel_resp.json() if rel_resp.status_code == 200 else rel_check.json()

        upload_url_tmpl = rel_data.get("upload_url", "")
        asset_uploaded = False
        if upload_url_tmpl:
            upload_url = upload_url_tmpl.split("{")[0] + f"?name={zip_path.name}"
            existing_assets = rel_data.get("assets", [])
            for asset in existing_assets:
                if asset.get("name") == zip_path.name and asset.get("id"):
                    client.delete(
                        f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/assets/{asset['id']}"
                    )
            up_headers = {**headers, "Content-Type": "application/zip"}
            up_resp = client.post(upload_url, headers=up_headers, content=zip_path.read_bytes())
            asset_uploaded = up_resp.status_code in (200, 201)

        return {
            "tag": RELEASE_TAG_V2_2,
            "commitSha": commit_sha,
            "releaseUrl": f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}/releases/tag/{RELEASE_TAG_V2_2}",
            "zipBundlePath": str(zip_path),
            "zipBundleSizeBytes": zip_path.stat().st_size,
            "assetUploaded": asset_uploaded,
        }

    if http_client is not None:
        return _upsert_release(http_client)
    with httpx.Client(headers=headers, timeout=90.0, follow_redirects=True) as local_client:
        return _upsert_release(local_client)


def update_github_openapi_discovery_topics(
    token: str | None = None,
    http_client: httpx.Client | None = None,
) -> dict[str, Any]:
    """Atualiza os 20 Topics de indexação OpenAPI, RapidAPI, MCP e x402 nos 2 repositórios oficiais."""
    gh_token = token or load_env_token()
    headers = {
        "Authorization": f"Bearer {gh_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    repos = [
        f"{GITHUB_OWNER}/{GITHUB_REPO}",
        f"{GITHUB_OWNER}/{GITHUB_OWNER}.github.io",
    ]

    def _put_topics(client: httpx.Client) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for repo_full in repos:
            resp = client.put(
                f"https://api.github.com/repos/{repo_full}/topics",
                json={"names": OPENAPI_GITHUB_TOPICS},
            )
            out[repo_full] = {
                "statusCode": resp.status_code,
                "topicsCount": len(OPENAPI_GITHUB_TOPICS),
            }
        return out

    if http_client is not None:
        return _put_topics(http_client)
    with httpx.Client(headers=headers, timeout=25.0) as local_client:
        return _put_topics(local_client)


def verify_public_openapi_31_urls(
    origin_url: str = PUBLIC_GITHUB_PAGES_ORIGIN,
    http_client: httpx.Client | None = None,
    max_retries: int = 6,
    retry_delay_sec: float = 3.0,
) -> dict[str, Any]:
    """
    Valida a acessibilidade `HTTP 200` das 31 URLs públicas `OpenAPI 3.0.3`
    (`https://jesleytassili-glitch.github.io/specs_openapi_31/<slug>.json`),
    do catálogo `/apis.json` (`/.well-known/apis.json`) e do `/pricing_plans_manifest.json`.
    """
    clean_origin = origin_url.rstrip("/")
    catalog_urls = {
        "apis_json": f"{clean_origin}/apis.json",
        "well_known_apis_json": f"{clean_origin}/.well-known/apis.json",
        "pricing_manifest": f"{clean_origin}/pricing_plans_manifest.json",
        "postman_collection": f"{clean_origin}/postman_public_network_collection.json",
    }
    spec_urls = {slug: f"{clean_origin}/specs_openapi_31/{slug}.json" for slug in ACTOR_SLUGS}

    def _check_all(client: httpx.Client) -> dict[str, Any]:
        catalog_results: dict[str, dict[str, Any]] = {}
        for key, url in catalog_urls.items():
            status_code = 0
            valid_json = False
            for attempt in range(max_retries):
                try:
                    resp = client.get(url)
                    status_code = resp.status_code
                    if status_code == 200:
                        data = resp.json()
                        valid_json = isinstance(data, dict)
                        break
                except Exception:
                    pass
                if attempt + 1 < max_retries and http_client is None:
                    time.sleep(retry_delay_sec)
            catalog_results[key] = {
                "url": url,
                "httpStatus": status_code,
                "validJson": valid_json,
            }

        spec_results: list[dict[str, Any]] = []
        for slug, url in spec_urls.items():
            status_code = 0
            openapi_ver = ""
            for attempt in range(max_retries):
                try:
                    resp = client.get(url)
                    status_code = resp.status_code
                    if status_code == 200:
                        body = resp.json()
                        openapi_ver = str(body.get("openapi", ""))
                        break
                except Exception:
                    pass
                if attempt + 1 < max_retries and http_client is None:
                    time.sleep(retry_delay_sec)
            spec_results.append(
                {
                    "slug": slug,
                    "url": url,
                    "httpStatus": status_code,
                    "openapiVersion": openapi_ver,
                    "ok": status_code == 200 and openapi_ver == "3.0.3",
                }
            )

        verified_specs_count = sum(1 for item in spec_results if item["ok"])
        all_catalogs_ok = all(
            v["httpStatus"] == 200 and v["validJson"] for v in catalog_results.values()
        )
        return {
            "all31SpecsHttp200": verified_specs_count == len(ACTOR_SLUGS),
            "verifiedSpecsCount": verified_specs_count,
            "totalSpecs": len(ACTOR_SLUGS),
            "allCatalogsHttp200": all_catalogs_ok,
            "catalogs": catalog_results,
            "specs": spec_results,
        }

    if http_client is not None:
        return _check_all(http_client)
    with httpx.Client(timeout=20.0, follow_redirects=True) as local_client:
        return _check_all(local_client)


def ping_indexnow_openapi_31_urls(
    origin_url: str = PUBLIC_GITHUB_PAGES_ORIGIN,
    http_client: httpx.Client | None = None,
) -> dict[str, Any]:
    """Dispara notificação IndexNow para todas as 31 especificações OpenAPI 3.0.3, `apis.json` e `pricing_plans_manifest.json`."""
    clean_origin = origin_url.rstrip("/")
    suite_origin = f"{clean_origin}/{GITHUB_REPO}"
    url_list = [
        f"{clean_origin}/",
        f"{clean_origin}/apis.json",
        f"{clean_origin}/.well-known/apis.json",
        f"{clean_origin}/pricing_plans_manifest.json",
        f"{clean_origin}/postman_public_network_collection.json",
        f"{suite_origin}/",
        f"{suite_origin}/apis.json",
        f"{suite_origin}/.well-known/apis.json",
        f"{suite_origin}/pricing_plans_manifest.json",
        *[f"{clean_origin}/specs_openapi_31/{slug}.json" for slug in ACTOR_SLUGS],
        *[f"{suite_origin}/specs_openapi_31/{slug}.json" for slug in ACTOR_SLUGS],
    ]
    payload = {
        "host": f"{GITHUB_OWNER}.github.io",
        "key": INDEXNOW_KEY,
        "keyLocation": f"{clean_origin}/{INDEXNOW_KEY}.txt",
        "urlList": url_list,
    }

    def _send(client: httpx.Client) -> dict[str, Any]:
        try:
            resp = client.post("https://api.indexnow.org/indexnow", json=payload)
            return {
                "httpStatus": resp.status_code,
                "submittedUrlsCount": len(url_list),
            }
        except Exception as exc:
            logger.warning("Aviso no ping IndexNow OpenAPI 3.0.3: %s", exc)
            return {"httpStatus": 0, "submittedUrlsCount": len(url_list), "error": str(exc)}

    if http_client is not None:
        return _send(http_client)
    with httpx.Client(timeout=20.0) as local_client:
        return _send(local_client)


def run_full_openapi_2026_syndication(
    push_live: bool = True,
    verify_live_urls: bool = True,
    http_client: httpx.Client | None = None,
    receipt_path: Path = SYNDICATION_RECEIPT_PATH,
) -> dict[str, Any]:
    """
    Executa a sindicância externa completa da Frente #6 (`RE-06`):
    1. Sincroniza as 31 specs `OpenAPI 3.0.3`, `apis.json`, `pricing_plans_manifest.json` e `postman_public_network_collection.json`;
    2. Se `push_live=True`, publica no GitHub Pages raiz (`jesleytassili-glitch.github.io`) e no repositório
       `b2b-quant-mcp-n8n-suite` com a **GitHub Release `v2.2.0`** e Topics atualizados;
    3. Se `verify_live_urls=True`, valida `HTTP 200` das 31 URLs públicas + `apis.json` e dispara `IndexNow`;
    4. Persiste o recibo auditável em `rapidapi_zyla_hub_suite/openapi_syndication_receipt.json`.
    """
    sync_report = sync_openapi_31_and_apis_json_to_repos()

    if not push_live:
        receipt = {
            "status": "local_synced",
            "generatedAtUtc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "engineVersion": ENGINE_VERSION,
            "releaseTag": RELEASE_TAG_V2_2,
            "payoutDestination": f"Wise #{WISE_ACCOUNT_NUMBER}",
            "publicSpecsBaseUrl": PUBLIC_SPECS_BASE_URL,
            "publicSuiteSpecsBaseUrl": PUBLIC_SUITE_SPECS_BASE_URL,
            "apisJsonUrl": PUBLIC_APIS_JSON_URL,
            "wellKnownApisJsonUrl": PUBLIC_WELL_KNOWN_APIS_JSON_URL,
            "localSync": sync_report,
        }
        receipt_path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")
        return receipt

    root_pages_report = publish_openapi_31_to_root_github_pages(http_client=http_client)
    release_report = publish_github_release_v2_2_0(http_client=http_client)
    topics_report = update_github_openapi_discovery_topics(http_client=http_client)
    verification_report = (
        verify_public_openapi_31_urls(http_client=http_client)
        if verify_live_urls
        else {"all31SpecsHttp200": False, "verifiedSpecsCount": 0, "totalSpecs": len(ACTOR_SLUGS)}
    )
    indexnow_report = ping_indexnow_openapi_31_urls(http_client=http_client)

    receipt = {
        "status": "syndicated_live",
        "generatedAtUtc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "engineVersion": ENGINE_VERSION,
        "releaseTag": RELEASE_TAG_V2_2,
        "payoutDestination": f"Wise #{WISE_ACCOUNT_NUMBER}",
        "publicSpecsBaseUrl": PUBLIC_SPECS_BASE_URL,
        "publicSuiteSpecsBaseUrl": PUBLIC_SUITE_SPECS_BASE_URL,
        "apisJsonUrl": PUBLIC_APIS_JSON_URL,
        "wellKnownApisJsonUrl": PUBLIC_WELL_KNOWN_APIS_JSON_URL,
        "localSync": sync_report,
        "rootGithubPages": root_pages_report,
        "githubReleaseV220": release_report,
        "githubTopics": topics_report,
        "urlVerification": verification_report,
        "indexNow": indexnow_report,
    }
    receipt_path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Sindicador Externo OpenAPI 3.0.3, apis.json (APIs.guru), GitHub Pages & Release v2.2.0"
    )
    parser.add_argument("--local-only", action="store_true", help="Apenas gera e sincroniza os arquivos localmente.")
    parser.add_argument("--skip-verify", action="store_true", help="Pula a verificação HTTP 200 pós-deploy.")
    args = parser.parse_args()

    res = run_full_openapi_2026_syndication(
        push_live=not args.local_only,
        verify_live_urls=not args.skip_verify,
    )
    print(json.dumps(res, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
