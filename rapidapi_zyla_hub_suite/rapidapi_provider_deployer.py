#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cliente Automatizado de Publicação & Matriz de Precificação Recorrente em USD
(`rapidapi_provider_deployer.py` -> `pricing_plans_manifest.json` + `RAPIDAPI_ZYLA_ACTIVATION_PLAYBOOK.md`).

Responsabilidades:
1. Gera e valida o manifesto `pricing_plans_manifest.json` com a matriz padrão de 4 tiers
   em Dólar (payout direto na conta Wise #890361113) para todas as 31 APIs B2B:
   - BASIC (Freemium): US$ 0.00/mês | Hard Limit de 15 req/mês (zero risco de custo);
   - PRO: US$ 19.00/mês | 1.000 req/mês (+ US$ 0.02/req extra);
   - ULTRA: US$ 49.00/mês | 5.000 req/mês (+ US$ 0.015/req extra);
   - MEGA: US$ 149.00/mês | 25.000 req/mês (+ US$ 0.010/req extra).
2. Implementa o cliente automatizado `RapidAPIProviderDeployer` com suporte completo à
   Platform API (PAPI REST & GraphQL `https://graphql.rapidapi.com`) do RapidAPI Studio
   quando `RAPIDAPI_API_KEY` estiver configurada no `.env`;
3. Gera o manifesto passo a passo de ativação rápida (`RAPIDAPI_ZYLA_ACTIVATION_PLAYBOOK.md`).
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
import os
import sys
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

from deploy_apify_suite import ACTOR_SLUGS, ACTORS_DIR, MONETIZATION_CONFIG
from export_mcp_rapidapi_manifests import load_actor_metadata
from rapidapi_zyla_hub_suite.generate_rapidapi_zyla_specs import (
    APIFY_USERNAME,
    DEFAULT_GATEWAY_BASE_URL,
    ENGINE_VERSION,
    GITHUB_RELEASE_TAG,
    MARKETPLACE_TAXONOMY,
    PUBLIC_APIS_JSON_URL,
    PUBLIC_SPECS_BASE_URL,
    PUBLIC_SUITE_SPECS_BASE_URL,
    PUBLIC_WELL_KNOWN_APIS_JSON_URL,
    SPECS_OUTPUT_DIR,
    WISE_ACCOUNT_NUMBER,
    generate_all_31_openapi_specs,
)
from rapidapi_zyla_hub_suite.rapidapi_zyla_gateway import (
    DEFAULT_RAPIDAPI_PROXY_SECRET,
    DEFAULT_ZYLA_PROXY_SECRET,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("rapidapi_provider_deployer")

PRICING_MANIFEST_PATH = SUITE_DIR / "pricing_plans_manifest.json"
ACTIVATION_PLAYBOOK_PATH = SUITE_DIR / "RAPIDAPI_ZYLA_ACTIVATION_PLAYBOOK.md"
RAPIDAPI_GRAPHQL_URL = "https://graphql.rapidapi.com"
RAPIDAPI_OAS_INGESTION_URL = "https://openapi-ingestion.p.rapidapi.com/v1/apis"


def load_env_variables() -> dict[str, str]:
    """Carrega variáveis do arquivo `.env` na raiz do workspace e variáveis de ambiente do sistema."""
    env_map: dict[str, str] = {}
    env_file = WORKSPACE_ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8", errors="ignore").splitlines():
            clean = line.strip()
            if "=" in clean and not clean.startswith("#"):
                k, v = clean.split("=", 1)
                env_map[k.strip()] = v.strip().strip('"').strip("'")
    for k, v in os.environ.items():
        if k not in env_map:
            env_map[k] = v
    return env_map


def build_4tier_pricing_matrix() -> dict[str, dict[str, Any]]:
    """
    Retorna a matriz oficial de precificação recorrente em Dólar (4 tiers) para as 31 APIs B2B.
    """
    return {
        "BASIC": {
            "tier": "BASIC",
            "planType": "FREEMIUM",
            "monthlyPriceUsd": 0.00,
            "monthlyQuotaRequests": 15,
            "overagePricePerRequestUsd": 0.00,
            "hardLimit": True,
            "rateLimitPerMinute": 5,
            "description": "US$ 0.00/mês | Hard Limit de 15 req/mês (zero risco de custo)",
        },
        "PRO": {
            "tier": "PRO",
            "planType": "RECURRING_PLUS_OVERAGE",
            "monthlyPriceUsd": 19.00,
            "monthlyQuotaRequests": 1000,
            "overagePricePerRequestUsd": 0.02,
            "hardLimit": False,
            "rateLimitPerMinute": 60,
            "description": "US$ 19.00/mês | 1.000 req/mês (+ US$ 0.02/req extra)",
        },
        "ULTRA": {
            "tier": "ULTRA",
            "planType": "RECURRING_PLUS_OVERAGE",
            "monthlyPriceUsd": 49.00,
            "monthlyQuotaRequests": 5000,
            "overagePricePerRequestUsd": 0.015,
            "hardLimit": False,
            "rateLimitPerMinute": 180,
            "description": "US$ 49.00/mês | 5.000 req/mês (+ US$ 0.015/req extra)",
        },
        "MEGA": {
            "tier": "MEGA",
            "planType": "RECURRING_PLUS_OVERAGE",
            "monthlyPriceUsd": 149.00,
            "monthlyQuotaRequests": 25000,
            "overagePricePerRequestUsd": 0.010,
            "hardLimit": False,
            "rateLimitPerMinute": 600,
            "description": "US$ 149.00/mês | 25.000 req/mês (+ US$ 0.010/req extra)",
        },
    }


def build_pricing_plans_manifest(
    specs_dir: Path = SPECS_OUTPUT_DIR,
    actors_dir: Path = ACTORS_DIR,
    gateway_url: str = DEFAULT_GATEWAY_BASE_URL,
) -> dict[str, Any]:
    """
    Constrói a estrutura completa do arquivo `pricing_plans_manifest.json` para as 31 APIs B2B.
    """
    pricing_matrix = build_4tier_pricing_matrix()
    apis_catalog: list[dict[str, Any]] = []

    for idx, slug in enumerate(ACTOR_SLUGS, start=1):
        meta = load_actor_metadata(slug, actors_dir=actors_dir)
        actor_info = meta["actor"]
        mon = MONETIZATION_CONFIG.get(slug, {})
        tax = MARKETPLACE_TAXONOMY.get(slug, {})
        spec_path = specs_dir / f"{slug}.json"

        apis_catalog.append(
            {
                "index": idx,
                "slug": slug,
                "title": actor_info.get("title", slug),
                "rapidapiCategory": tax.get("rapidapi_category", "Business"),
                "zylaCategory": tax.get("zyla_category", "Company Data"),
                "seoTags": tax.get("seo_tags", [slug]),
                "openapiVersion": "3.0.3",
                "openapiSpecFile": f"specs_openapi_31/{slug}.json",
                "openapiSpecPublicUrl": f"{PUBLIC_SPECS_BASE_URL}/{slug}.json",
                "openapiSpecSuiteUrl": f"{PUBLIC_SUITE_SPECS_BASE_URL}/{slug}.json",
                "openapiSpecExists": spec_path.exists(),
                "gatewayEndpoint": f"{gateway_url.rstrip('/')}/v1/{slug}",
                "apifyCloudSyncEndpoint": f"https://api.apify.com/v2/acts/{APIFY_USERNAME}~{slug}/run-sync-get-dataset-items",
                "baseUnitCostUsd": float(mon.get("price_usd", 0.02)),
                "payoutDestination": f"Wise #{WISE_ACCOUNT_NUMBER}",
                "pricingPlans": pricing_matrix,
            }
        )

    return {
        "manifestVersion": ENGINE_VERSION,
        "githubReleaseTag": GITHUB_RELEASE_TAG,
        "generatedAtUtc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "publicDiscovery": {
            "specsBaseUrl": PUBLIC_SPECS_BASE_URL,
            "suiteSpecsBaseUrl": PUBLIC_SUITE_SPECS_BASE_URL,
            "apisJsonCatalogUrl": PUBLIC_APIS_JSON_URL,
            "wellKnownApisJsonUrl": PUBLIC_WELL_KNOWN_APIS_JSON_URL,
            "postmanCollectionFile": "postman_public_network_collection.json",
        },
        "payoutConfiguration": {
            "accountHolder": "Jesley Aguileira",
            "wiseAccountNumber": WISE_ACCOUNT_NUMBER,
            "payoutDestination": f"Wise #{WISE_ACCOUNT_NUMBER}",
            "payoutEmail": "jesleytassili@gmail.com",
            "currency": "USD",
            "marketplaces": [
                "RapidAPI Hub (Nokia Rapid)",
                "Zyla API Hub",
                "Postman Public API Network",
                "APIs.guru (apis.json v0.16)",
            ],
        },
        "antiBypassSecurity": {
            "validationAlgorithm": "hmac.compare_digest (constant-time)",
            "rapidapiSecretHeader": "X-RapidAPI-Proxy-Secret",
            "zylaSecretHeader": "X-Zyla-Proxy-Secret",
            "rejectedHttpStatus": 403,
            "quotaExceededHttpStatus": 429,
            "injectedTelemetryHeaders": [
                "X-RateLimit-Remaining",
                "X-Engine-Version",
                "X-RateLimit-Limit",
                "X-Subscription-Tier",
                "X-Marketplace-Provider",
                "X-Payout-Destination",
            ],
        },
        "pricingPlans": pricing_matrix,
        "totalApis": len(apis_catalog),
        "apis": apis_catalog,
        "quickActivationSteps": [
            "1. Gerar/atualizar as 31 specs OpenAPI 3.0.3 e apis.json: python rapidapi_zyla_hub_suite/generate_rapidapi_zyla_specs.py",
            "2. Sindicar URLs públicas no GitHub Pages + Release v2.2.0: python rapidapi_zyla_hub_suite/openapi_syndicator_2026.py",
            "3. Se RAPIDAPI_API_KEY estiver no .env, executar: python rapidapi_zyla_hub_suite/rapidapi_provider_deployer.py --deploy",
            "4. Ou importar em 1 clique por URL (https://jesleytassili-glitch.github.io/specs_openapi_31/<slug>.json) no RapidAPI Studio, Zyla Hub e Postman apontando payout para Wise #890361113",
        ],
    }


class RapidAPIProviderDeployer:
    """
    Cliente automatizado para a Platform API (PAPI / GraphQL) do RapidAPI Hub e Zyla API Hub.
    Suporta importação 1-Clique de especificações OpenAPI 3.0.3 (via URL pública ou JSON inline)
    e criação dos 4 planos de preços (`BASIC`, `PRO`, `ULTRA`, `MEGA`) via GraphQL / REST.
    """

    def __init__(
        self,
        rapidapi_api_key: str | None = None,
        zyla_api_key: str | None = None,
        gateway_url: str = DEFAULT_GATEWAY_BASE_URL,
        graphql_url: str = RAPIDAPI_GRAPHQL_URL,
        oas_ingestion_url: str = RAPIDAPI_OAS_INGESTION_URL,
    ) -> None:
        env_vars = load_env_variables()
        self.rapidapi_api_key = (
            rapidapi_api_key
            if rapidapi_api_key is not None
            else env_vars.get("RAPIDAPI_API_KEY", "")
        ).strip()
        self.zyla_api_key = (
            zyla_api_key
            if zyla_api_key is not None
            else env_vars.get("ZYLA_API_KEY", "")
        ).strip()
        self.gateway_url = gateway_url.rstrip("/")
        self.graphql_url = graphql_url
        self.oas_ingestion_url = oas_ingestion_url

    def build_graphql_upsert_api_payload(self, slug: str, spec_dict: dict[str, Any]) -> dict[str, Any]:
        """
        Constrói a mutation GraphQL oficial do RapidAPI Platform API (PAPI) para criação/atualização
        de uma API a partir da especificação OpenAPI 3.0.3 (URL canônica + JSON) e configuração dos 4 planos.
        """
        info = spec_dict.get("info", {})
        tax = MARKETPLACE_TAXONOMY.get(slug, {})
        pricing = build_4tier_pricing_matrix()
        public_spec_url = f"{PUBLIC_SPECS_BASE_URL}/{slug}.json"

        query = """
        mutation UpsertB2BApiFromOpenApi($input: UpsertApiFromOasInput!) {
          upsertApiFromOas(input: $input) {
            apiId
            slug
            name
            category
            visibility
            status
          }
        }
        """.strip()

        return {
            "operationName": "UpsertB2BApiFromOpenApi",
            "query": query,
            "variables": {
                "input": {
                    "slug": slug,
                    "name": info.get("title", slug),
                    "description": info.get("description", ""),
                    "category": tax.get("rapidapi_category", "Business"),
                    "tags": tax.get("seo_tags", [slug]),
                    "baseUrl": self.gateway_url,
                    "proxySecretHeader": "X-RapidAPI-Proxy-Secret",
                    "proxySecretValue": DEFAULT_RAPIDAPI_PROXY_SECRET,
                    "payoutAccount": f"Wise #{WISE_ACCOUNT_NUMBER}",
                    "openapiSpecUrl": public_spec_url,
                    "openapiSpecJson": json.dumps(spec_dict, ensure_ascii=False),
                    "pricingPlans": list(pricing.values()),
                }
            },
        }


    def deploy_single_api(
        self,
        slug: str,
        specs_dir: Path = SPECS_OUTPUT_DIR,
        dry_run: bool = False,
        http_client: httpx.Client | None = None,
    ) -> dict[str, Any]:
        """
        Implanta ou atualiza 1 API B2B no RapidAPI PAPI/GraphQL.
        Se `RAPIDAPI_API_KEY` não estiver presente ou `dry_run=True`, executa validação
        completa local sem chamadas externas.
        """
        spec_file = specs_dir / f"{slug}.json"
        if not spec_file.exists():
            generate_all_31_openapi_specs(output_dir=specs_dir, gateway_url=self.gateway_url)

        spec_dict = json.loads(spec_file.read_text(encoding="utf-8"))
        gql_payload = self.build_graphql_upsert_api_payload(slug, spec_dict)

        if dry_run or not self.rapidapi_api_key:
            return {
                "slug": slug,
                "status": "prepared_offline" if not self.rapidapi_api_key else "dry_run_validated",
                "openapiVersion": spec_dict.get("openapi"),
                "category": MARKETPLACE_TAXONOMY.get(slug, {}).get("rapidapi_category", "Business"),
                "zylaCategory": MARKETPLACE_TAXONOMY.get(slug, {}).get("zyla_category", "Company Data"),
                "graphqlOperation": gql_payload["operationName"],
                "tiersConfigured": list(build_4tier_pricing_matrix().keys()),
                "specFile": str(spec_file),
            }

        headers = {
            "X-RapidAPI-Key": self.rapidapi_api_key,
            "Authorization": f"Bearer {self.rapidapi_api_key}",
            "Content-Type": "application/json",
        }

        try:
            if http_client is not None:
                resp = http_client.post(self.graphql_url, json=gql_payload, headers=headers)
            else:
                with httpx.Client(timeout=25.0) as client:
                    resp = client.post(self.graphql_url, json=gql_payload, headers=headers)

            resp.raise_for_status()
            body = resp.json()
            api_data = (body.get("data") or {}).get("upsertApiFromOas") or {}
            return {
                "slug": slug,
                "status": "deployed_papi",
                "httpStatus": resp.status_code,
                "apiId": api_data.get("apiId", f"rapidapi_{slug}"),
                "tiersConfigured": list(build_4tier_pricing_matrix().keys()),
                "specFile": str(spec_file),
            }
        except Exception as exc:
            logger.warning("Aviso PAPI GraphQL para %s: %s", slug, exc)
            return {
                "slug": slug,
                "status": f"papi_error: {exc}",
                "tiersConfigured": list(build_4tier_pricing_matrix().keys()),
                "specFile": str(spec_file),
            }

    def deploy_all_31_apis(
        self,
        specs_dir: Path = SPECS_OUTPUT_DIR,
        manifest_path: Path = PRICING_MANIFEST_PATH,
        playbook_path: Path = ACTIVATION_PLAYBOOK_PATH,
        dry_run: bool = False,
        http_client: httpx.Client | None = None,
    ) -> dict[str, Any]:
        """
        Gera as 31 especificações OpenAPI 3.0.3, persiste `pricing_plans_manifest.json` e
        `RAPIDAPI_ZYLA_ACTIVATION_PLAYBOOK.md`, e sincroniza via PAPI/GraphQL quando
        `RAPIDAPI_API_KEY` estiver configurada no `.env`.
        """
        generate_all_31_openapi_specs(output_dir=specs_dir, gateway_url=self.gateway_url)
        manifest = build_pricing_plans_manifest(specs_dir=specs_dir, gateway_url=self.gateway_url)

        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")

        playbook_md = build_activation_playbook_markdown(manifest)
        playbook_path.write_text(playbook_md, encoding="utf-8", newline="\n")

        results: list[dict[str, Any]] = []
        for slug in ACTOR_SLUGS:
            res = self.deploy_single_api(
                slug=slug,
                specs_dir=specs_dir,
                dry_run=dry_run,
                http_client=http_client,
            )
            results.append(res)

        deployed_count = sum(1 for r in results if r["status"] == "deployed_papi")
        return {
            "status": "deployed_live" if deployed_count == len(ACTOR_SLUGS) else "ready_for_activation",
            "rapidapiKeyConfigured": bool(self.rapidapi_api_key),
            "zylaKeyConfigured": bool(self.zyla_api_key),
            "totalApis": len(results),
            "deployedLiveCount": deployed_count,
            "payoutDestination": f"Wise #{WISE_ACCOUNT_NUMBER}",
            "manifestPath": str(manifest_path),
            "playbookPath": str(playbook_path),
            "specsDirectory": str(specs_dir),
            "results": results,
        }


def build_activation_playbook_markdown(manifest: dict[str, Any]) -> str:
    """Gera o guia passo a passo de ativação rápida para RapidAPI Studio, Zyla API Hub, Postman e APIs.guru."""
    rows: list[str] = []
    for item in manifest.get("apis", []):
        pub_url = item.get("openapiSpecPublicUrl", f"{PUBLIC_SPECS_BASE_URL}/{item['slug']}.json")
        rows.append(
            f"| {item['index']:02d} | `{item['slug']}` | {item['rapidapiCategory']} | "
            f"{item['zylaCategory']} | [`{item['openapiSpecFile']}`]({pub_url}) |"
        )
    table_str = "\n".join(rows)

    return f"""# PLAYBOOK DE ATIVAÇÃO RÁPIDA — FRENTE #6 (RAPIDAPI HUB, ZYLA HUB, POSTMAN & APIS.GURU -> WISE #{WISE_ACCOUNT_NUMBER})

## 1. Resumo Executivo, URLs Públicas Estáticas e Destino de Payout
- **Conta Recebedora em Dólar (USD):** **Wise `#{WISE_ACCOUNT_NUMBER}`** (`Jesley Aguileira` | `jesleytassili@gmail.com`)
- **Total de Motores B2B Empacotados:** **31 APIs (`OpenAPI 3.0.3`)** em `rapidapi_zyla_hub_suite/specs_openapi_31/*.json`
- **URL Pública Canônica (Importação 1-Clique HTTPS):** `{PUBLIC_SPECS_BASE_URL}/<slug>.json`
- **Catálogo Oficial `apis.json` (`APIs.guru` / `API Commons v0.16`):** `{PUBLIC_APIS_JSON_URL}` e `{PUBLIC_WELL_KNOWN_APIS_JSON_URL}`
- **GitHub Release Oficial:** `https://github.com/jesleytassili-glitch/b2b-quant-mcp-n8n-suite/releases/tag/{GITHUB_RELEASE_TAG}`
- **Gateway Anti-Bypass (`R$ 0,00` CAPEX):** `rapidapi_zyla_gateway.py` + `cloudflare_worker_proxy.js`
  - Validação em tempo constante (`hmac.compare_digest`) de `X-RapidAPI-Proxy-Secret` e `X-Zyla-Proxy-Secret` (`HTTP 403` para acessos diretos fora do marketplace).
  - Injeção automática de `X-RateLimit-Remaining` e `X-Engine-Version: {ENGINE_VERSION}`.

---

## 2. Matriz Padrão de Precificação Recorrente (USD)

| Tier | Preço Mensal (USD) | Franquia Mensal | Preço por Requisição Extra | Tipo de Limite |
| :--- | :---: | :---: | :---: | :--- |
| **`BASIC` (Freemium)** | **US$ 0.00 / mês** | `15 req / mês` | `US$ 0.00` (Bloqueado) | **Hard Limit (`HTTP 429` na 16ª chamada)** |
| **`PRO`** | **US$ 19.00 / mês** | `1.000 req / mês` | `+ US$ 0.020 / req` | Soft Limit (Cobrança automática de overage) |
| **`ULTRA`** | **US$ 49.00 / mês** | `5.000 req / mês` | `+ US$ 0.015 / req` | Soft Limit (Cobrança automática de overage) |
| **`MEGA`** | **US$ 149.00 / mês** | `25.000 req / mês` | `+ US$ 0.010 / req` | Soft Limit (Cobrança automática de overage) |

---

## 3. Passo a Passo de Publicação (PAPI Automatizado, URL 1-Clique ou Assistente Playwright + Gmail OTP)

### Opção A — Automática via Platform API (`RAPIDAPI_API_KEY` no `.env`)
1. Adicione `RAPIDAPI_API_KEY=sua_chave_rapidapi` no arquivo `.env` na raiz do workspace;
2. Execute `PUBLICAR_RAPIDAPI_ZYLA.bat` ou:
   ```powershell
   python rapidapi_zyla_hub_suite/rapidapi_provider_deployer.py --deploy
   ```

### Opção B — Importação 1-Clique por URL Pública no RapidAPI Studio (`studio.rapidapi.com`), Zyla Hub (`zylalabs.com`) & Postman
1. No **RapidAPI Studio** (`https://studio.rapidapi.com`), clique em **Add API Project** -> **OpenAPI** -> **Import from URL** (ou File);
2. Informe a URL canônica HTTPS `https://jesleytassili-glitch.github.io/specs_openapi_31/<slug>.json` (ou o arquivo local `rapidapi_zyla_hub_suite/specs_openapi_31/<slug>.json`);
3. Na aba **Gateway / Security**, copie o `X-RapidAPI-Proxy-Secret` gerado e configure no Worker (`RAPIDAPI_PROXY_SECRET`);
4. Na aba **Monetize / Plans**, aplique os 4 tiers (`BASIC $0/15`, `PRO $19/1000`, `ULTRA $49/5000`, `MEGA $149/25000`) e vincule o payout à conta **Wise `#{WISE_ACCOUNT_NUMBER}`**.

### Opção C — Assistente em Lote com Leitura Automática de 2FA/OTP via Gmail IMAP
```powershell
python rapidapi_zyla_hub_suite/rapidapi_zyla_playwright_importer.py --check-otp
```

---

## 4. Catálogo das 31 Especificações Individuais OpenAPI 3.0.3 (URLs Canônicas)

| # | Slug da API B2B | Categoria RapidAPI | Categoria Zyla Hub | Especificação OpenAPI 3.0.3 (URL Pública) |
| :-: | :--- | :--- | :--- | :--- |
{table_str}
"""


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Gerador, Sindicador e Publicador Automatizado das 31 APIs B2B no RapidAPI Hub, Zyla API Hub, Postman e APIs.guru"
    )
    parser.add_argument(
        "--deploy",
        action="store_true",
        help="Dispara sincronização ao vivo via PAPI/GraphQL quando RAPIDAPI_API_KEY estiver configurada no .env.",
    )
    parser.add_argument(
        "--syndicate",
        action="store_true",
        help="Publica as 31 specs OpenAPI 3.0.3, apis.json e Release v2.2.0 no GitHub Pages e valida HTTP 200.",
    )
    parser.add_argument(
        "--batch-import",
        action="store_true",
        help="Executa o automatizador em lote (URL Import + PAPI + Gmail IMAP OTP).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Executa apenas geração e validação local das 31 specs e manifestos.",
    )
    args = parser.parse_args()

    deployer = RapidAPIProviderDeployer()
    report = deployer.deploy_all_31_apis(dry_run=args.dry_run or not args.deploy)

    if args.syndicate:
        from rapidapi_zyla_hub_suite.openapi_syndicator_2026 import run_full_openapi_2026_syndication

        report["openapiSyndication"] = run_full_openapi_2026_syndication(
            push_live=not args.dry_run,
            verify_live_urls=not args.dry_run,
        )

    if args.batch_import:
        from rapidapi_zyla_hub_suite.rapidapi_zyla_playwright_importer import RapidAPIZylaPlaywrightBatchImporter

        importer = RapidAPIZylaPlaywrightBatchImporter()
        report["batchImport"] = importer.run_batch_import(dry_run=args.dry_run)

    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

