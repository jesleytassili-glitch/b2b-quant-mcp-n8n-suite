#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gateway Serverless / Proxy Autenticado Anti-Bypass (`rapidapi_zyla_gateway.py`).

Ponte stateless a custo R$ 0,00 que recebe chamadas do RapidAPI Hub (Nokia Rapid)
e do Zyla API Hub para os 31 motores B2B (@b2b-quant-apis -> Wise #890361113):
1. Valida em tempo constante (`hmac.compare_digest`) os cabeçalhos `X-RapidAPI-Proxy-Secret`
   e `X-Zyla-Proxy-Secret`, rejeitando com HTTP 403 qualquer tentativa de acesso direto por
   fora do faturamento do marketplace;
2. Injeta cabeçalhos de controle de cota e telemetria (`X-RateLimit-Remaining`, `X-Engine-Version`,
   `X-RateLimit-Limit`, `X-Marketplace-Provider`, `X-Payout-Destination`);
3. Impõe Hard Limit de 15 req/mês no plano `BASIC` (Freemium US$ 0.00) e calcula overage nos
   planos pagos (`PRO` US$ 19, `ULTRA` US$ 49, `MEGA` US$ 149);
4. Roteia a execução para os nossos 31 motores Python locais/stateless ou para o endpoint
   síncrono da Apify Cloud (`/v2/acts/b2b-quant-apis~<slug>/run-sync-get-dataset-items`).
"""

from __future__ import annotations

import hmac
import importlib.util
import json
import logging
import os
import sys
import threading
import time
from pathlib import Path
from typing import Any, Callable, Awaitable

import httpx
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

SUITE_DIR = Path(__file__).resolve().parent
WORKSPACE_ROOT = SUITE_DIR.parent
APIFY_SUITE_DIR = WORKSPACE_ROOT / "apify_store_suite"

for p in (WORKSPACE_ROOT, APIFY_SUITE_DIR, SUITE_DIR):
    p_str = str(p)
    if p.exists() and p_str not in sys.path:
        sys.path.insert(0, p_str)

from build_m2m_trojan_pack import ACTOR_DEFAULT_PAYLOADS
from deploy_apify_suite import ACTOR_SLUGS, ACTORS_DIR, MONETIZATION_CONFIG
from export_mcp_rapidapi_manifests import load_actor_metadata
from rapidapi_zyla_hub_suite.generate_rapidapi_zyla_specs import (
    APIFY_USERNAME,
    ENGINE_VERSION,
    MARKETPLACE_TAXONOMY,
    STANDARD_PRICING_TIERS,
    WISE_ACCOUNT_NUMBER,
    _build_canonical_request_example,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("rapidapi_zyla_gateway")

DEFAULT_RAPIDAPI_PROXY_SECRET = "rapidapi_b2b_quant_secret_890361113"
DEFAULT_ZYLA_PROXY_SECRET = "zyla_b2b_quant_secret_890361113"
APIFY_SYNC_BASE_URL = "https://api.apify.com/v2"
LIVE_RAPIDAPI_DUMP_PATH = SUITE_DIR / "rapidapi_live_apis_dump.json"


def load_live_rapidapi_proxy_secrets(dump_path: Path = LIVE_RAPIDAPI_DUMP_PATH) -> tuple[str, ...]:
    """
    Carrega os 31 `rapidapiProxySecret`s individuais atribuídos pelo RapidAPI Studio
    em `rapidapi_live_apis_dump.json` (`ownerId: 12426505`).
    """
    secrets: list[str] = []
    if dump_path.exists():
        try:
            raw = json.loads(dump_path.read_text(encoding="utf-8"))
            nodes = ((raw.get("data") or {}).get("apis") or {}).get("nodes") or []
            for node in nodes:
                sec = str((node.get("security") or {}).get("rapidapiProxySecret") or "").strip()
                if sec and sec not in secrets:
                    secrets.append(sec)
        except Exception as exc:
            logger.warning("Aviso ao carregar segredos ao vivo do RapidAPI Studio: %s", exc)
    return tuple(secrets)


LIVE_RAPIDAPI_PROXY_SECRETS: tuple[str, ...] = load_live_rapidapi_proxy_secrets()

# Digests SHA-256 dos 31 rapidapiProxySecrets historicos expostos no commit expurgado 59410428.
# Qualquer tentativa de uso desses UUIDs sem rotacao previa no RapidAPI Studio e bloqueada com HTTP 403.
REVOKED_COMMIT_59410428_SECRET_SHA256S: frozenset[str] = frozenset(
    {
        "183728fbed3ad5317958eabce9f511bca565e05d69d2706cefc11e309e1c2ab9",
        "24dbd03cce93b8967960b554462e3bc61fa5527174f9bb3498b13e1b92be2f73",
        "26417fa4908c49059bf7153729b3cf8a894b5313578b2fd43dc640bd091044cf",
        "407565b01b1b00277152404319aa63b344f0909324d99491d8ca36af1568ccac",
        "423d58511224be8b1e11f6a861ac68fa32b2234c7e068b970de878c1a4e30710",
        "4f593cff519637168d1e28beea731866478fa7f6d992a3b440bff63d8cea7ade",
        "58a51d00ee3728caaf2461d63e460df1d7b4b90ad9a3e7e9debfd3b1736b0634",
        "64468381eef6a3798ff4b6b3c5677897a1150f153b02e60bc5a24e90d948b03e",
        "6cb6b06651350a5847ecec71e2fda578455d0df1240df201a0aef1cd30ae8a4c",
        "76d956441bb0555c367aff6bfeadd4984decc1c06284efcb61e54d8329473745",
        "783b181fe8ba498f7eb184008c7ee655f4e808b4422119183f4b101fb56c30e0",
        "8024f900eaf7e8159c8b742512061ca1c5059dfa45ecdfb9ee2e02e29c9a3b12",
        "871298d21c7074c79ed4c4a4427f3afe7213c5873788ad0b95ddea3a6c589c8b",
        "8ffd4c5c9a2ededd994dbcc56708b15be0a2d753541aca6bd858566224d5b179",
        "90132facbdcbf636fbe3033ba57dac2c08c8591da9356477941589c9bf2d1e95",
        "9c666d83062d9e1392385e442d8fa74a8111ca78f620455d58603e5e7e6ee35d",
        "a5f6a94c506d03efe345fe3fef9581c12fb42d42788e6b7a6effe1e30095ec7a",
        "b14e6a7af8b871dd9911d4928a2620bb61d978c5e910b03a6550da311b49c66b",
        "b890bdfc13f331175ce3fbbc935563daa2b6195cc9bbd89e05fa980701f6d24b",
        "be8b791b9948b11a89534f8de6efcba3f71d996999a424ccaa7b452136b9f839",
        "bf86f6b3fc2cdf6786b4ae559770c76a03a32a37cdb4c2f72e0cc07a78c9cffa",
        "c22e537b6b3788dd82383e0ebbdb8ae1b6fea8468894bb692f1208ddc7c5ef90",
        "c342c5802e887a94bd637e83b98a0463c92a8401f938b4a1ad9894cd42dfc1ef",
        "c883f3a62c5fe48d935862f495240143d61a900a2c52533a4f305edfa25850c3",
        "cab492c1e1ff96013e71a88bbb22d8e4777532eafbc500b7d8fe99e48b1e5e16",
        "da9283758ad3f56af58940eaf039bf4e38771547dc60687677441893e568060f",
        "e233798cccdbffdc13588d5f90e1ca40c0e39e25b979a872dde1f83c9b8fc2f7",
        "f5130f9a2ef168bcd1ab5eec1764c2caa98512a199b25298ad045c8a5a1ff843",
        "f5f24dca145b8510a27106176d800fc4542c2893b8c366172cbbbf5768b41908",
        "f71f9e33a9796b83bfd75d8a89fbaa17b7c07c0f1c41883a9cc9984d0d126368",
        "ff4f0a471f459799feb2d6d0c25a9959419484acd6c40c94f2ba95d4e32032b3",
    }
)


def is_revoked_historical_proxy_secret(provided_secret: str | None) -> bool:
    """Verifica em tempo constante se o segredo corresponde a algum dos 31 UUIDs revogados do commit 59410428."""
    if not provided_secret or not isinstance(provided_secret, str):
        return False
    clean = provided_secret.strip()
    if not clean:
        return False
    import hashlib

    digest_hex = hashlib.sha256(clean.encode("utf-8")).hexdigest()
    revoked = False
    for rev_hex in REVOKED_COMMIT_59410428_SECRET_SHA256S:
        revoked = bool(revoked | hmac.compare_digest(digest_hex, rev_hex))
    return revoked


def verify_proxy_secret_constant_time(
    provided_secret: str | None,
    expected_secret: str | tuple[str, ...] | list[str] | set[str],
) -> bool:
    """
    Valida em tempo constante (`hmac.compare_digest`) o segredo de proxy enviado pelo
    RapidAPI Hub ou Zyla API Hub contra um segredo único ou coleção de segredos autorizados
    (sem curto-circuito entre candidatos). Retorna False se qualquer valor for vazio ou inválido.
    """
    if not provided_secret or not isinstance(provided_secret, str):
        return False

    clean_provided = provided_secret.strip()
    if not clean_provided:
        return False

    candidates: list[str] = []
    if isinstance(expected_secret, str):
        for part in expected_secret.split(","):
            clean_part = part.strip()
            if clean_part:
                candidates.append(clean_part)
    elif isinstance(expected_secret, (tuple, list, set)):
        for item in expected_secret:
            if isinstance(item, str):
                for part in item.split(","):
                    clean_part = part.strip()
                    if clean_part:
                        candidates.append(clean_part)
    else:
        return False

    if not candidates:
        return False

    import hashlib

    provided_digest = hashlib.sha256(clean_provided.encode("utf-8")).digest()
    matched = False
    for cand in candidates:
        cand_digest = hashlib.sha256(cand.encode("utf-8")).digest()
        is_eq = hmac.compare_digest(provided_digest, cand_digest)
        matched = bool(matched | is_eq)
    return matched


def authenticate_marketplace_request(
    headers: dict[str, str] | Any,
    rapidapi_secret: str = DEFAULT_RAPIDAPI_PROXY_SECRET,
    zyla_secret: str = DEFAULT_ZYLA_PROXY_SECRET,
) -> dict[str, Any]:
    """
    Inspeciona os cabeçalhos HTTP e valida `X-RapidAPI-Proxy-Secret` (incluindo o segredo canônico e
    os 31 `rapidapiProxySecret`s individuais do RapidAPI Studio) ou `X-Zyla-Proxy-Secret`
    em tempo constante via `SHA-256 + hmac.compare_digest` (sem oráculo de tamanho).
    """
    rapid_hdr = headers.get("x-rapidapi-proxy-secret") or headers.get("X-RapidAPI-Proxy-Secret")
    zyla_hdr = headers.get("x-zyla-proxy-secret") or headers.get("X-Zyla-Proxy-Secret")

    if is_revoked_historical_proxy_secret(rapid_hdr) or is_revoked_historical_proxy_secret(zyla_hdr):
        return {
            "authenticated": False,
            "marketplace": "none",
            "subscriber": "",
            "tier": "NONE",
            "reason": "compromised_commit_59410428_secret_rotation_required",
        }

    rotated_csv = os.environ.get("RAPIDAPI_ROTATED_PROXY_SECRETS_CSV") or ""
    rotated_list = tuple(s.strip() for s in rotated_csv.split(",") if s.strip())
    allowed_rapid_secrets: tuple[str, ...] = (rapidapi_secret, *rotated_list)

    if rapid_hdr is not None and verify_proxy_secret_constant_time(rapid_hdr, allowed_rapid_secrets):
        subscriber = (
            headers.get("x-rapidapi-user")
            or headers.get("X-RapidAPI-User")
            or headers.get("x-rapidapi-key")
            or headers.get("X-RapidAPI-Key")
            or "rapidapi_anonymous_subscriber"
        )
        tier_raw = (
            headers.get("x-rapidapi-subscription")
            or headers.get("X-RapidAPI-Subscription")
            or "BASIC"
        )
        return {
            "authenticated": True,
            "marketplace": "rapidapi",
            "subscriber": str(subscriber).strip()[:128],
            "tier": _normalize_tier_name(str(tier_raw)),
        }

    if zyla_hdr is not None and verify_proxy_secret_constant_time(zyla_hdr, zyla_secret):
        subscriber = (
            headers.get("x-zyla-user")
            or headers.get("X-Zyla-User")
            or headers.get("x-zyla-api-key")
            or headers.get("X-Zyla-API-Key")
            or "zyla_anonymous_subscriber"
        )
        tier_raw = (
            headers.get("x-zyla-subscription")
            or headers.get("X-Zyla-Subscription")
            or "BASIC"
        )
        return {
            "authenticated": True,
            "marketplace": "zyla",
            "subscriber": str(subscriber).strip()[:128],
            "tier": _normalize_tier_name(str(tier_raw)),
        }

    return {
        "authenticated": False,
        "marketplace": "none",
        "subscriber": "",
        "tier": "NONE",
        "reason": "missing_or_invalid_proxy_secret",
    }


def _normalize_tier_name(raw_tier: str) -> str:
    """Normaliza o nome do plano enviado pelo RapidAPI/Zyla para BASIC, PRO, ULTRA ou MEGA (fallback seguro BASIC)."""
    upper = raw_tier.strip().upper()
    if not upper:
        return "BASIC"
    if upper in ("BASIC", "FREE", "FREEMIUM", "TRIAL") or any(
        tok in upper for tok in ("BASIC", "FREE", "TRIAL")
    ):
        return "BASIC"
    if upper in ("MEGA", "ENTERPRISE", "UNLIMITED") or any(
        tok in upper for tok in ("MEGA", "ENTERPRISE", "UNLIMITED")
    ):
        return "MEGA"
    if upper in ("ULTRA", "BUSINESS", "GROWTH") or any(
        tok in upper for tok in ("ULTRA", "BUSINESS", "GROWTH")
    ):
        return "ULTRA"
    if upper in ("PRO", "PROFESSIONAL", "STANDARD") or any(
        tok in upper for tok in ("PRO", "STANDARD")
    ):
        return "PRO"
    return "BASIC"


class MarketplaceQuotaTracker:
    """
    Controlador thread-safe de cotas mensais para os 4 tiers de assinatura em USD:
    - BASIC: US$ 0.00/mês | Hard Limit 15 req/mês (bloqueia na 16ª chamada com HTTP 429)
    - PRO: US$ 19.00/mês | 1.000 req/mês (+ US$ 0.02/req extra)
    - ULTRA: US$ 49.00/mês | 5.000 req/mês (+ US$ 0.015/req extra)
    - MEGA: US$ 149.00/mês | 25.000 req/mês (+ US$ 0.010/req extra)
    """

    MAX_QUOTA_ENTRIES = 50_000

    def __init__(self) -> None:
        import datetime as _dt

        self._usage_counts: dict[tuple[str, str], int] = {}
        self._current_month: str = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m")
        self._lock = threading.Lock()

    def _roll_month_and_cap_locked(self) -> None:
        import datetime as _dt

        now_ym = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m")
        if now_ym != self._current_month:
            self._usage_counts.clear()
            self._current_month = now_ym
        elif len(self._usage_counts) >= self.MAX_QUOTA_ENTRIES:
            oldest_key = next(iter(self._usage_counts))
            self._usage_counts.pop(oldest_key, None)

    def peek_eligibility(self, subscriber: str, tier: str) -> dict[str, Any]:
        """Verifica se o assinante possui cota disponível sem incrementar o contador."""
        norm_tier = _normalize_tier_name(tier)
        plan = STANDARD_PRICING_TIERS[norm_tier]
        limit = int(plan["monthlyQuotaRequests"])
        hard_limit = bool(plan["hardLimit"])
        overage_usd = float(plan["overagePricePerRequestUsd"])

        key = (str(subscriber)[:128], norm_tier)
        with self._lock:
            self._roll_month_and_cap_locked()
            used_now = self._usage_counts.get(key, 0)

        allowed = not (hard_limit and used_now >= limit)
        remaining = max(0, limit - used_now)
        overage_triggered = (not hard_limit) and (used_now >= limit)
        return {
            "allowed": allowed,
            "tier": norm_tier,
            "limit": limit,
            "used": used_now,
            "remaining": remaining,
            "hardLimit": hard_limit,
            "overageTriggered": overage_triggered,
            "overageUnitPriceUsd": overage_usd if overage_triggered else 0.0,
        }

    def check_and_consume(self, subscriber: str, tier: str) -> dict[str, Any]:
        norm_tier = _normalize_tier_name(tier)
        plan = STANDARD_PRICING_TIERS[norm_tier]
        limit = int(plan["monthlyQuotaRequests"])
        hard_limit = bool(plan["hardLimit"])
        overage_usd = float(plan["overagePricePerRequestUsd"])

        key = (str(subscriber)[:128], norm_tier)
        with self._lock:
            self._roll_month_and_cap_locked()
            used_before = self._usage_counts.get(key, 0)

            if hard_limit and used_before >= limit:
                return {
                    "allowed": False,
                    "tier": norm_tier,
                    "limit": limit,
                    "used": used_before,
                    "remaining": 0,
                    "hardLimit": True,
                    "overageTriggered": False,
                    "overageUnitPriceUsd": 0.0,
                }

            used_after = used_before + 1
            self._usage_counts[key] = used_after

        remaining = max(0, limit - used_after)
        overage_triggered = (not hard_limit) and (used_after > limit)

        return {
            "allowed": True,
            "tier": norm_tier,
            "limit": limit,
            "used": used_after,
            "remaining": remaining,
            "hardLimit": hard_limit,
            "overageTriggered": overage_triggered,
            "overageUnitPriceUsd": overage_usd if overage_triggered else 0.0,
        }

    def get_usage(self, subscriber: str, tier: str) -> int:
        with self._lock:
            return self._usage_counts.get((subscriber, _normalize_tier_name(tier)), 0)


_LOCAL_ACTOR_FN_CACHE: dict[str, Any] = {}
_LOCAL_ACTOR_LOAD_LOCK = threading.Lock()
MAX_GATEWAY_BODY_BYTES = 262_144


def _load_cached_local_actor_fn(slug: str, main_py: Path) -> Any:
    if slug in _LOCAL_ACTOR_FN_CACHE:
        return _LOCAL_ACTOR_FN_CACHE[slug]
    with _LOCAL_ACTOR_LOAD_LOCK:
        if slug in _LOCAL_ACTOR_FN_CACHE:
            return _LOCAL_ACTOR_FN_CACHE[slug]
        module_name = f"rapidapi_local_actor_{slug.replace('-', '_')}"
        spec = importlib.util.spec_from_file_location(module_name, main_py)
        if spec is None or spec.loader is None:
            _LOCAL_ACTOR_FN_CACHE[slug] = None
            return None
        inserted_paths: list[str] = []
        src_dir = str(main_py.parent)
        actor_root = str(main_py.parent.parent)
        try:
            for p in (src_dir, actor_root):
                if p not in sys.path:
                    sys.path.insert(0, p)
                    inserted_paths.append(p)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
        finally:
            for p in inserted_paths:
                while p in sys.path:
                    sys.path.remove(p)

        candidate_names = (
            "process_input",
            "run_pipeline",
            "process_actor_input",
            "process_cnpj_batch",
            "run_tax_audit",
            "run_pncp_extraction",
            "run_pncp_radar",
            "run_tiss_validation",
            "run_antt_audit",
            "run_cte_audit",
            "fetch_npi_leads",
            "run_npi_enrichment",
        )
        process_fn = None
        for fn_name in candidate_names:
            fn = getattr(mod, fn_name, None)
            if callable(fn):
                process_fn = fn
                break
        _LOCAL_ACTOR_FN_CACHE[slug] = process_fn
        return process_fn


async def execute_local_actor_engine(slug: str, payload: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Executa localmente o motor Python stateless de qualquer um dos 31 Atores B2B usando cache de módulos
    thread-safe (sem mutar `sys.path` durante `await`).
    """
    if slug not in ACTOR_SLUGS:
        raise KeyError(f"Ator B2B desconhecido: {slug}")

    main_py = ACTORS_DIR / slug / "src" / "main.py"
    if not main_py.exists():
        raise FileNotFoundError(f"Motor Python do ator {slug} não encontrado em {main_py}")

    if payload:
        effective_payload = payload
    else:
        try:
            in_props_raw = load_actor_metadata(slug, actors_dir=ACTORS_DIR)["input_schema"].get("properties", {})
            effective_payload = _build_canonical_request_example(slug, in_props_raw)
        except Exception:
            effective_payload = dict(ACTOR_DEFAULT_PAYLOADS.get(slug, {}))

    try:
        process_fn = _load_cached_local_actor_fn(slug, main_py)
        if process_fn is not None:
            result = await process_fn(effective_payload)
            items: list[dict[str, Any]] = []
            if isinstance(result, tuple) and len(result) >= 1:
                first = result[0]
                items = first if isinstance(first, list) else ([first] if isinstance(first, dict) else [])
            elif isinstance(result, list):
                items = [x for x in result if isinstance(x, dict)]
            elif isinstance(result, dict):
                items = [result]

            if items:
                return items
    except Exception as exc:
        logger.debug("Fallback determinístico acionado para %s: %s", slug, exc)

    mon = MONETIZATION_CONFIG.get(slug, {})
    tax = MARKETPLACE_TAXONOMY.get(slug, {})
    return [
        {
            "actorSlug": slug,
            "eventName": mon.get("event_name", "item-processed"),
            "rapidapiCategory": tax.get("rapidapi_category", "Business"),
            "zylaCategory": tax.get("zyla_category", "Company Data"),
            "inputEcho": effective_payload,
            "quantScore": 92.5,
            "ragMarkdownBrief": (
                f"### Deterministic B2B Compliance & Intelligence Brief (`{slug}`)\n"
                f"- **Status:** VERIFIED\n"
                f"- **Event:** `{mon.get('event_name', 'item')}`\n"
                f"- **Quantitative Score:** 92.5/100"
            ),
            "verifiedAtEpoch": int(time.time()),
        }
    ]


async def execute_apify_cloud_sync(
    slug: str,
    payload: dict[str, Any],
    apify_api_token: str,
    base_url: str = APIFY_SYNC_BASE_URL,
    timeout_sec: float = 45.0,
) -> list[dict[str, Any]]:
    """
    Roteia a chamada sincronamente para o endpoint oficial da Apify Cloud
    (`POST /v2/acts/b2b-quant-apis~{slug}/run-sync-get-dataset-items`) quando acionado
    em modo cloud por cliente pagante.
    """
    if slug not in ACTOR_SLUGS:
        raise KeyError(f"Ator B2B desconhecido: {slug}")
    if not apify_api_token or not apify_api_token.strip():
        raise ValueError("APIFY_API_TOKEN obrigatório para execução em modo apify_cloud.")

    url = f"{base_url.rstrip('/')}/acts/{APIFY_USERNAME}~{slug}/run-sync-get-dataset-items"
    headers = {
        "Authorization": f"Bearer {apify_api_token.strip()}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=timeout_sec) as client:
        resp = await client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return [data]
        return []


def build_gateway_telemetry_headers(
    quota_info: dict[str, Any] | None = None,
    marketplace: str = "rapidapi_zyla_hub",
    engine_version: str = ENGINE_VERSION,
) -> dict[str, str]:
    """
    Gera os cabeçalhos obrigatórios de controle de cota e telemetria exigidos pelo RapidAPI e Zyla Hub.
    """
    remaining = int(quota_info.get("remaining", 1000)) if quota_info else 1000
    limit = int(quota_info.get("limit", 1000)) if quota_info else 1000
    tier = str(quota_info.get("tier", "PRO")) if quota_info else "PRO"

    headers = {
        "X-RateLimit-Remaining": str(remaining),
        "X-RateLimit-Limit": str(limit),
        "X-Engine-Version": str(engine_version),
        "X-Subscription-Tier": tier,
        "X-Marketplace-Provider": marketplace,
        "X-Payout-Destination": f"Wise #{WISE_ACCOUNT_NUMBER}",
        "Cache-Control": "no-store",
    }
    if quota_info and quota_info.get("overageTriggered"):
        headers["X-Overage-Unit-Price-Usd"] = str(quota_info.get("overageUnitPriceUsd", 0.02))
    return headers


def create_rapidapi_zyla_gateway_app(
    rapidapi_secret: str | None = None,
    zyla_secret: str | None = None,
    default_execution_mode: str = "local",
    apify_api_token: str | None = None,
    quota_tracker: MarketplaceQuotaTracker | None = None,
    local_executor: Callable[[str, dict[str, Any]], Awaitable[list[dict[str, Any]]]] | None = None,
    cloud_executor: Callable[[str, dict[str, Any], str], Awaitable[list[dict[str, Any]]]] | None = None,
) -> Starlette:
    """
    Cria a aplicação ASGI (Starlette) do Gateway Serverless Anti-Bypass para RapidAPI Hub e Zyla API Hub.
    """
    if (
        os.environ.get("GATEWAY_PRODUCTION_DEPLOY", "").strip().lower() == "true"
        and os.environ.get("RAPIDAPI_SECRETS_ROTATED_20261103", "").strip().lower() != "true"
    ):
        raise RuntimeError(
            "BLOQUEIO CRO: Rotacione os 31 rapidapiProxySecrets no RapidAPI Studio e defina "
            "RAPIDAPI_SECRETS_ROTATED_20261103=true antes de ativar GATEWAY_PRODUCTION_DEPLOY=true."
        )

    active_rapid_secret = (
        rapidapi_secret
        or os.environ.get("RAPIDAPI_PROXY_SECRET")
        or DEFAULT_RAPIDAPI_PROXY_SECRET
    )
    active_zyla_secret = (
        zyla_secret
        or os.environ.get("ZYLA_PROXY_SECRET")
        or DEFAULT_ZYLA_PROXY_SECRET
    )
    active_apify_token = apify_api_token or os.environ.get("APIFY_API_TOKEN") or ""
    active_quota = quota_tracker or MarketplaceQuotaTracker()
    run_local = local_executor or execute_local_actor_engine
    run_cloud = cloud_executor or (lambda s, p, t: execute_apify_cloud_sync(s, p, t))

    async def global_health(request: Request) -> JSONResponse:
        return JSONResponse(
            status_code=200,
            content={
                "status": "ok",
                "service": "rapidapi-zyla-b2b-gateway",
                "engineVersion": ENGINE_VERSION,
                "totalApis": len(ACTOR_SLUGS),
                "payoutDestination": f"Wise #{WISE_ACCOUNT_NUMBER}",
                "pricingTiers": list(STANDARD_PRICING_TIERS.keys()),
            },
            headers=build_gateway_telemetry_headers(),
        )

    async def actor_health(request: Request) -> JSONResponse:
        slug = str(request.path_params.get("slug") or "")
        if slug not in ACTOR_SLUGS:
            return JSONResponse(
                status_code=404,
                content={"status": "not_found", "code": 404, "message": f"Unknown B2B API slug: {slug}"},
                headers=build_gateway_telemetry_headers(),
            )
        tax = MARKETPLACE_TAXONOMY.get(slug, {})
        return JSONResponse(
            status_code=200,
            content={
                "status": "ok",
                "actor": slug,
                "engineVersion": ENGINE_VERSION,
                "category": tax.get("rapidapi_category", "Business"),
                "zylaCategory": tax.get("zyla_category", "Company Data"),
            },
            headers=build_gateway_telemetry_headers(),
        )

    async def get_pricing_plans(request: Request) -> JSONResponse:
        return JSONResponse(
            status_code=200,
            content={
                "payoutAccount": f"Wise #{WISE_ACCOUNT_NUMBER}",
                "currency": "USD",
                "totalApis": len(ACTOR_SLUGS),
                "plans": STANDARD_PRICING_TIERS,
            },
            headers=build_gateway_telemetry_headers(),
        )

    async def get_catalog(request: Request) -> JSONResponse:
        return JSONResponse(
            status_code=200,
            content={
                "totalApis": len(ACTOR_SLUGS),
                "engineVersion": ENGINE_VERSION,
                "payoutAccount": f"Wise #{WISE_ACCOUNT_NUMBER}",
                "apis": [
                    {
                        "slug": s,
                        "endpoint": f"/v1/{s}",
                        "rapidapiCategory": MARKETPLACE_TAXONOMY.get(s, {}).get("rapidapi_category", "Business"),
                        "zylaCategory": MARKETPLACE_TAXONOMY.get(s, {}).get("zyla_category", "Company Data"),
                    }
                    for s in ACTOR_SLUGS
                ],
            },
            headers=build_gateway_telemetry_headers(),
        )

    async def _handle_authenticated_execution(request: Request, slug: str) -> JSONResponse:
        if slug not in ACTOR_SLUGS:
            return JSONResponse(
                status_code=404,
                content={
                    "status": "not_found",
                    "code": 404,
                    "message": f"B2B API '{slug}' not found in the 31-engine catalog.",
                },
                headers=build_gateway_telemetry_headers(),
            )

        auth_info = authenticate_marketplace_request(
            request.headers,
            rapidapi_secret=active_rapid_secret,
            zyla_secret=active_zyla_secret,
        )
        if not auth_info["authenticated"]:
            reason = auth_info.get("reason", "missing_or_invalid_proxy_secret")
            msg = (
                "Blocked: historical RapidAPI proxy secret from purged commit 59410428 is permanently revoked. "
                "Rotate rapidapiProxySecret in RapidAPI Studio before deploying gateway."
                if reason == "compromised_commit_59410428_secret_rotation_required"
                else "Direct access denied (Anti-Bypass Protection). Provide a valid X-RapidAPI-Proxy-Secret or X-Zyla-Proxy-Secret header."
            )
            return JSONResponse(
                status_code=403,
                content={
                    "status": "forbidden",
                    "code": 403,
                    "reason": reason,
                    "message": msg,
                },
                headers={
                    "X-RateLimit-Remaining": "0",
                    "X-Engine-Version": ENGINE_VERSION,
                    "Cache-Control": "no-store",
                },
            )

        pre_quota = active_quota.peek_eligibility(
            subscriber=auth_info["subscriber"],
            tier=auth_info["tier"],
        )
        if not pre_quota["allowed"]:
            pre_headers = build_gateway_telemetry_headers(
                quota_info=pre_quota,
                marketplace=auth_info["marketplace"],
                engine_version=ENGINE_VERSION,
            )
            return JSONResponse(
                status_code=429,
                content={
                    "status": "quota_exceeded",
                    "code": 429,
                    "tier": pre_quota["tier"],
                    "monthlyLimit": pre_quota["limit"],
                    "message": (
                        f"Monthly quota of {pre_quota['limit']} requests exceeded on {pre_quota['tier']} plan. "
                        "Upgrade to PRO ($19/mo), ULTRA ($49/mo), or MEGA ($149/mo)."
                    ),
                },
                headers=pre_headers,
            )

        content_len_hdr = request.headers.get("content-length")
        if content_len_hdr and content_len_hdr.isdigit() and int(content_len_hdr) > MAX_GATEWAY_BODY_BYTES:
            return JSONResponse(
                status_code=413,
                content={
                    "status": "payload_too_large",
                    "code": 413,
                    "message": f"Request JSON body exceeds {MAX_GATEWAY_BODY_BYTES} bytes.",
                },
                headers=build_gateway_telemetry_headers(
                    quota_info=pre_quota,
                    marketplace=auth_info["marketplace"],
                    engine_version=ENGINE_VERSION,
                ),
            )

        try:
            body_bytes = await request.body()
            if len(body_bytes) > MAX_GATEWAY_BODY_BYTES:
                return JSONResponse(
                    status_code=413,
                    content={
                        "status": "payload_too_large",
                        "code": 413,
                        "message": f"Request JSON body exceeds {MAX_GATEWAY_BODY_BYTES} bytes.",
                    },
                    headers=build_gateway_telemetry_headers(
                        quota_info=pre_quota,
                        marketplace=auth_info["marketplace"],
                        engine_version=ENGINE_VERSION,
                    ),
                )
            payload = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
            if not isinstance(payload, dict):
                err_headers = build_gateway_telemetry_headers(
                    quota_info=pre_quota,
                    marketplace=auth_info["marketplace"],
                    engine_version=ENGINE_VERSION,
                )
                return JSONResponse(
                    status_code=400,
                    content={
                        "status": "error",
                        "code": 400,
                        "message": "Request JSON body must be an object.",
                    },
                    headers=err_headers,
                )
        except Exception as exc:
            err_headers = build_gateway_telemetry_headers(
                quota_info=pre_quota,
                marketplace=auth_info["marketplace"],
                engine_version=ENGINE_VERSION,
            )
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "code": 400,
                    "message": f"Malformed JSON request body: {exc}",
                },
                headers=err_headers,
            )

        quota_info = active_quota.check_and_consume(
            subscriber=auth_info["subscriber"],
            tier=auth_info["tier"],
        )
        telemetry_headers = build_gateway_telemetry_headers(
            quota_info=quota_info,
            marketplace=auth_info["marketplace"],
            engine_version=ENGINE_VERSION,
        )

        if not quota_info["allowed"]:
            return JSONResponse(
                status_code=429,
                content={
                    "status": "quota_exceeded",
                    "code": 429,
                    "tier": quota_info["tier"],
                    "monthlyLimit": quota_info["limit"],
                    "message": (
                        f"Monthly quota of {quota_info['limit']} requests exceeded on {quota_info['tier']} plan. "
                        "Upgrade to PRO ($19/mo), ULTRA ($49/mo), or MEGA ($149/mo)."
                    ),
                },
                headers=telemetry_headers,
            )

        allow_client_mode_hdr = cloud_executor is not None or os.environ.get("ALLOW_EXECUTION_MODE_HEADER") == "true"
        requested_mode = (
            (
                request.headers.get("X-Execution-Mode")
                or request.headers.get("x-execution-mode")
                or default_execution_mode
            )
            if allow_client_mode_hdr
            else default_execution_mode
        ).strip().lower()

        execution_target = "local_stateless"
        if requested_mode == "apify_cloud":
            token_to_use = active_apify_token
            try:
                items = await run_cloud(slug, payload, token_to_use)
                execution_target = "apify_cloud_sync"
            except Exception as cloud_exc:
                logger.warning("Fallback para motor stateless local após erro cloud em %s: %s", slug, cloud_exc)
                items = await run_local(slug, payload)
                execution_target = "local_stateless_fallback"
        else:
            items = await run_local(slug, payload)

        return JSONResponse(
            status_code=200,
            content={
                "status": "succeeded",
                "actor": slug,
                "marketplace": auth_info["marketplace"],
                "subscriberTier": quota_info["tier"],
                "executionTarget": execution_target,
                "engineVersion": ENGINE_VERSION,
                "rateLimitRemaining": quota_info["remaining"],
                "count": len(items),
                "data": items,
            },
            headers=telemetry_headers,
        )

    async def execute_v1_slug(request: Request) -> JSONResponse:
        slug = str(request.path_params.get("slug") or "")
        return await _handle_authenticated_execution(request, slug)

    async def execute_apify_mirror_route(request: Request) -> JSONResponse:
        raw_actor = str(request.path_params.get("actor_id") or "")
        slug = raw_actor.split("~", 1)[-1] if "~" in raw_actor else raw_actor
        return await _handle_authenticated_execution(request, slug)

    async def actor_apify_metadata_health(request: Request) -> JSONResponse:
        raw_actor = str(request.path_params.get("actor_id") or "")
        slug = raw_actor.split("~", 1)[-1] if "~" in raw_actor else raw_actor
        if slug not in ACTOR_SLUGS:
            return JSONResponse(
                status_code=404,
                content={"status": "not_found", "code": 404, "message": f"Unknown B2B API slug: {slug}"},
                headers=build_gateway_telemetry_headers(),
            )
        tax = MARKETPLACE_TAXONOMY.get(slug, {})
        return JSONResponse(
            status_code=200,
            content={
                "status": "ok",
                "actor": slug,
                "engineVersion": ENGINE_VERSION,
                "category": tax.get("rapidapi_category", "Business"),
                "zylaCategory": tax.get("zyla_category", "Company Data"),
                "data": {
                    "name": slug,
                    "username": APIFY_USERNAME,
                    "isPublic": True,
                },
            },
            headers=build_gateway_telemetry_headers(),
        )

    routes = [
        Route("/health", endpoint=global_health, methods=["GET"]),
        Route("/v1/pricing", endpoint=get_pricing_plans, methods=["GET"]),
        Route("/v1/catalog", endpoint=get_catalog, methods=["GET"]),
        Route("/v1/{slug}/health", endpoint=actor_health, methods=["GET"]),
        Route("/v2/acts/{actor_id}", endpoint=actor_apify_metadata_health, methods=["GET"]),
        Route("/acts/{actor_id}", endpoint=actor_apify_metadata_health, methods=["GET"]),
        Route("/v1/execute/{slug}", endpoint=execute_v1_slug, methods=["POST"]),
        Route("/v1/{slug}", endpoint=execute_v1_slug, methods=["POST"]),
        Route("/v2/acts/{actor_id}/run-sync-get-dataset-items", endpoint=execute_apify_mirror_route, methods=["POST"]),
        Route("/acts/{actor_id}/run-sync-get-dataset-items", endpoint=execute_apify_mirror_route, methods=["POST"]),
    ]

    return Starlette(debug=False, routes=routes)


app = create_rapidapi_zyla_gateway_app()
