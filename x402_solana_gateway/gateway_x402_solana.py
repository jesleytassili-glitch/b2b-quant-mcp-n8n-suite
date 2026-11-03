#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gateway x402 (HTTP 402 Payment Required) — Liquidação Nativa em USDC na Rede Solana (SPL).

Permite que Agentes de IA autônomos (OpenClaw, Claude, Cursor, LangChain, CrewAI, AgentCash e x402 Bazaar)
consumam qualquer um dos 25 Motores B2B Determinísticos (@b2b-quant-apis) realizando micropagamentos
on-chain em USDC (Solana Mainnet) diretamente para a carteira oficial:
    DuaKjymBXrmawGgg5gK8D1zT2w1NCqjmb7B1XKHRYc5T

Inclui:
1. Desafio HTTP 402 compatível com especificação x402 Version 1 (CAIP-2 Solana Mainnet + Mint USDC SPL);
2. Verificador criptográfico de transações Solana via RPC (`getTransaction`) com Trava Anti-Replay (`Double-Spend`);
3. Manifesto OpenAPI 3.1.0 enriquecido com `x-guidance`, `x-payment-info` (`AgentCash.dev`) e `x-bazaar` (`x402 Bazaar`);
4. Endpoint de Descoberta `/.well-known/x402.json` para indexadores M2M.
"""

from __future__ import annotations

import asyncio
import base64
import importlib.util
import json
import logging
import os
import re
import sys
import tempfile
import time
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Callable

import httpx
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

SUITE_DIR = Path(__file__).resolve().parent.parent
if str(SUITE_DIR) not in sys.path:
    sys.path.insert(0, str(SUITE_DIR))

from deploy_apify_suite import ACTOR_SLUGS, ACTORS_DIR, MONETIZATION_CONFIG
from export_mcp_rapidapi_manifests import load_actor_metadata

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("x402_solana_gateway")

# Constantes Oficiais On-Chain (Solana Mainnet + USDC SPL)
SOLANA_USDC_WALLET = "DuaKjymBXrmawGgg5gK8D1zT2w1NCqjmb7B1XKHRYc5T"
SOLANA_USDC_PAY_TO_ATA = "A2t3qcFiKAjVYZ2KHDAieLAVXYmTPhGv659QAMZjNbP9"
SOLANA_CAIP2_NETWORK = "solana:5eykt4UsFv8P8NJdTREpY1vzqKqZKvdp"
SOLANA_NETWORK_SHORTHAND = "solana-mainnet"
SOLANA_USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
SOLANA_USDC_DECIMALS = 6
SOLANA_RPC_URL = "https://api.mainnet-beta.solana.com"
PUBLIC_BASE_URL = "https://jesleytassili-glitch.github.io/b2b-quant-mcp-n8n-suite"
APIFY_USERNAME = "b2b-quant-apis"
DEFAULT_REPLAY_STORE_PATH = Path(__file__).resolve().parent / ".x402_used_signatures.json"
MAX_X402_BODY_BYTES = 65_536
MAX_X402_BATCH_ITEMS = 50
_ACTOR_FN_CACHE: dict[str, tuple[Callable[..., Any], dict[str, Any]]] = {}

BASE58_SIGNATURE_REGEX = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{43,90}$")


def usd_to_usdc_atomic_units(price_usd: float | str | Decimal) -> str:
    """
    Converte valor em USD (ex: 0.025) para unidades atômicas inteiras de USDC (6 casas decimais -> '25000').
    """
    dec_val = Decimal(str(price_usd))
    if dec_val <= Decimal("0"):
        raise ValueError(f"Preço USD deve ser positivo: {price_usd}")
    atomic = int((dec_val * Decimal(10**SOLANA_USDC_DECIMALS)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    return str(atomic)


def format_usd_amount(price_usd: float | str | Decimal) -> str:
    """Formata o preço USD em string limpa compatível com AgentCash (ex: '0.025' ou '0.02')."""
    dec_val = Decimal(str(price_usd)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    formatted = f"{dec_val:f}".rstrip("0").rstrip(".")
    return formatted if formatted else "0.01"


def build_x402_challenge(slug: str, base_url: str = PUBLIC_BASE_URL) -> dict[str, Any]:
    """
    Constrói o payload oficial HTTP 402 Payment Required segundo o protocolo x402 (Version 1)
    para liquidação em USDC na rede Solana Mainnet.
    """
    if slug not in ACTOR_SLUGS:
        raise KeyError(f"Ator desconhecido: {slug}")

    meta = load_actor_metadata(slug)
    title = meta["actor"].get("title", slug)
    description = meta["actor"].get("description", "")
    mon = MONETIZATION_CONFIG.get(slug, {})
    price_usd = mon.get("price_usd", 0.02)
    event_name = mon.get("event_name", "item")
    atomic_amount = usd_to_usdc_atomic_units(price_usd)
    resource_url = f"{base_url.rstrip('/')}/v1/x402/{slug}"

    return {
        "x402Version": 1,
        "error": "Payment Required: Submit a valid Solana USDC transfer proof in the X-PAYMENT header.",
        "accepts": [
            {
                "scheme": "exact",
                "network": SOLANA_CAIP2_NETWORK,
                "maxAmountRequired": atomic_amount,
                "asset": "USDC",
                "payTo": SOLANA_USDC_WALLET,
                "resource": resource_url,
                "description": f"{title} — {description}",
                "mimeType": "application/json",
                "maxTimeoutSeconds": 120,
                "extra": {
                    "networkShorthand": SOLANA_NETWORK_SHORTHAND,
                    "mint": SOLANA_USDC_MINT,
                    "payToAta": SOLANA_USDC_PAY_TO_ATA,
                    "decimals": SOLANA_USDC_DECIMALS,
                    "priceUsd": format_usd_amount(price_usd),
                    "actorSlug": slug,
                    "eventName": event_name,
                    "mcpStreamableHttpUrl": f"https://mcp.apify.com/?actors={APIFY_USERNAME}/{slug}",
                },
            }
        ],
    }


def parse_x402_payment_header(header_value: str) -> dict[str, Any]:
    """
    Decodifica o cabeçalho `X-PAYMENT` ou `PAYMENT-SIGNATURE`.
    Suporta:
    1. JSON direto: `{"txSignature": "...", "network": "solana-mainnet"}`
    2. Base64 de JSON (padrão x402 SDK): `eyJ0eFNpZ25hdHVyZSI6...`
    3. Assinatura Base58 direta da transação Solana (43 a 90 caracteres).
    """
    if not header_value or not isinstance(header_value, str):
        raise ValueError("Cabeçalho X-PAYMENT vazio ou ausente.")

    raw = header_value.strip()
    if not raw:
        raise ValueError("Cabeçalho X-PAYMENT contém apenas espaços.")

    # Caso 1: JSON direto
    if raw.startswith("{") and raw.endswith("}"):
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                return _normalize_parsed_payment_dict(parsed)
        except json.JSONDecodeError as exc:
            raise ValueError(f"JSON malformado no cabeçalho X-PAYMENT: {exc}") from exc

    # Caso 2: Tenta decodificar Base64 -> JSON
    try:
        padded = raw + "=" * (-len(raw) % 4)
        decoded_bytes = base64.b64decode(padded, validate=False)
        decoded_str = decoded_bytes.decode("utf-8").strip()
        if decoded_str.startswith("{") and decoded_str.endswith("}"):
            parsed = json.loads(decoded_str)
            if isinstance(parsed, dict):
                return _normalize_parsed_payment_dict(parsed)
    except Exception:
        pass

    # Caso 3: Assinatura Base58 pura da Solana
    if BASE58_SIGNATURE_REGEX.match(raw):
        return {
            "txSignature": raw,
            "network": SOLANA_CAIP2_NETWORK,
            "scheme": "exact",
        }

    raise ValueError("Formato de prova X-PAYMENT inválido. Envie Base64 JSON, JSON ou assinatura Base58 Solana.")


def _normalize_parsed_payment_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Extrai e valida `txSignature` de diferentes formatos de payload x402."""
    payload_obj = data.get("payload") if isinstance(data.get("payload"), dict) else data
    tx_sig = (
        payload_obj.get("txSignature")
        or payload_obj.get("signature")
        or payload_obj.get("txHash")
        or payload_obj.get("transactionSignature")
        or data.get("txSignature")
        or data.get("signature")
    )
    if not tx_sig or not isinstance(tx_sig, str) or not BASE58_SIGNATURE_REGEX.match(tx_sig.strip()):
        raise ValueError("Campo txSignature/signature ausente ou em formato Base58 inválido no payload X-PAYMENT.")

    return {
        "txSignature": tx_sig.strip(),
        "network": str(data.get("network") or payload_obj.get("network") or SOLANA_CAIP2_NETWORK),
        "scheme": str(data.get("scheme") or payload_obj.get("scheme") or "exact"),
        "payer": str(payload_obj.get("payer") or data.get("payer") or ""),
    }


class SolanaX402Verifier:
    """
    Verificador On-Chain de Pagamentos USDC na Solana com Proteção Anti-Replay (Double-Spend).
    """

    def __init__(
        self,
        rpc_url: str = SOLANA_RPC_URL,
        recipient_wallet: str = SOLANA_USDC_WALLET,
        usdc_mint: str = SOLANA_USDC_MINT,
        replay_store_path: Path | None = None,
        max_age_seconds: int | None = None,
        commitment: str = "confirmed",
    ) -> None:
        self.rpc_url = rpc_url
        self.recipient_wallet = recipient_wallet
        self.usdc_mint = usdc_mint
        self.replay_store_path = replay_store_path
        self.max_age_seconds = max_age_seconds
        self.commitment = commitment
        self._used_signatures: set[str] = set()
        self._in_flight_signatures: set[str] = set()
        self._lock = asyncio.Lock()
        if self.replay_store_path and self.replay_store_path.exists():
            try:
                loaded = json.loads(self.replay_store_path.read_text(encoding="utf-8"))
                if isinstance(loaded, list):
                    self._used_signatures.update(str(s) for s in loaded)
            except Exception as exc:
                logger.warning("Não foi possível carregar cache anti-replay: %s", exc)

    def is_signature_used(self, tx_signature: str) -> bool:
        """Retorna True se a transação já foi utilizada anteriormente (Replay Attack)."""
        return tx_signature in self._used_signatures

    def mark_signature_used(self, tx_signature: str) -> None:
        """Registra a assinatura como consumida e persiste atomicamente em disco se configurado."""
        self._used_signatures.add(tx_signature)
        if self.replay_store_path:
            tmp_path: Path | None = None
            try:
                self.replay_store_path.parent.mkdir(parents=True, exist_ok=True)
                fd, tmp_name = tempfile.mkstemp(
                    dir=str(self.replay_store_path.parent),
                    prefix=".x402_replay_",
                    suffix=".tmp",
                )
                tmp_path = Path(tmp_name)
                with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
                    json.dump(sorted(self._used_signatures), fh, indent=2)
                    fh.write("\n")
                os.replace(tmp_path, self.replay_store_path)
            except Exception as exc:
                logger.error("Erro ao persistir cache anti-replay: %s", exc)
                if tmp_path and tmp_path.exists():
                    tmp_path.unlink(missing_ok=True)

    async def fetch_solana_transaction(self, tx_signature: str) -> dict[str, Any] | None:
        """Consulta `getTransaction` no RPC da Solana Mainnet com timeout seguro."""
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getTransaction",
            "params": [
                tx_signature,
                {
                    "encoding": "jsonParsed",
                    "commitment": self.commitment,
                    "maxSupportedTransactionVersion": 0,
                },
            ],
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(self.rpc_url, json=payload)
            resp.raise_for_status()
            body = resp.json()
            return body.get("result")

    def verify_parsed_transaction_result(
        self,
        tx_result: dict[str, Any] | None,
        required_atomic_amount: int,
    ) -> tuple[bool, str, int]:
        """
        Inspeciona o retorno do RPC `getTransaction` para confirmar que:
        1. A transação existe e não falhou (`meta.err is None`);
        2. Opcionalmente respeita `max_age_seconds` via `blockTime`;
        3. Houve crédito líquido de `>= required_atomic_amount` do Mint USDC SPL (6 decimais)
           para `self.recipient_wallet`.
        """
        if not tx_result or not isinstance(tx_result, dict):
            return False, "transaction_not_found_on_chain", 0

        meta = tx_result.get("meta")
        if not isinstance(meta, dict):
            return False, "missing_transaction_meta", 0

        if meta.get("err") is not None:
            return False, "transaction_failed_on_chain", 0

        if self.max_age_seconds is not None and "blockTime" in tx_result and tx_result["blockTime"] is not None:
            tx_age = int(time.time()) - int(tx_result["blockTime"])
            if tx_age > self.max_age_seconds:
                return False, f"stale_transaction_blocktime: age={tx_age}s max={self.max_age_seconds}s", 0

        # Calcula delta de saldo USDC (postTokenBalances - preTokenBalances) para a carteira recebedora
        pre_balances = meta.get("preTokenBalances") or []
        post_balances = meta.get("postTokenBalances") or []

        pre_amount = 0
        for item in pre_balances:
            if (
                isinstance(item, dict)
                and item.get("mint") == self.usdc_mint
                and item.get("owner") == self.recipient_wallet
            ):
                ui_token = item.get("uiTokenAmount") or {}
                if int(ui_token.get("decimals", SOLANA_USDC_DECIMALS)) != SOLANA_USDC_DECIMALS:
                    return False, "unexpected_token_decimals", 0
                pre_amount += int(ui_token.get("amount") or 0)

        post_amount = 0
        for item in post_balances:
            if (
                isinstance(item, dict)
                and item.get("mint") == self.usdc_mint
                and item.get("owner") == self.recipient_wallet
            ):
                ui_token = item.get("uiTokenAmount") or {}
                if int(ui_token.get("decimals", SOLANA_USDC_DECIMALS)) != SOLANA_USDC_DECIMALS:
                    return False, "unexpected_token_decimals", 0
                post_amount += int(ui_token.get("amount") or 0)

        received_atomic = post_amount - pre_amount
        if received_atomic < required_atomic_amount:
            return (
                False,
                f"insufficient_usdc_transfer: received={received_atomic} required={required_atomic_amount}",
                max(received_atomic, 0),
            )

        return True, "verified_on_chain", received_atomic

    async def verify_payment(
        self,
        header_value: str,
        required_atomic_amount: int,
    ) -> dict[str, Any]:
        """
        Fluxo completo de validação do cabeçalho `X-PAYMENT` com trava assíncrona anti-TOCTOU:
        1. Parseia o cabeçalho;
        2. Reserva a assinatura em `_in_flight_signatures` sob `asyncio.Lock` (evitando Double-Spend concorrente);
        3. Consulta a transação na Solana Mainnet e valida destinatário, Mint USDC e valor;
        4. Marca a assinatura como consumida se aprovada, liberando a trava em `finally`.
        """
        parsed = parse_x402_payment_header(header_value)
        tx_sig = parsed["txSignature"]

        async with self._lock:
            if self.is_signature_used(tx_sig) or tx_sig in self._in_flight_signatures:
                return {
                    "valid": False,
                    "reason": "replay_attack_detected",
                    "txSignature": tx_sig,
                    "receivedAtomic": 0,
                }
            self._in_flight_signatures.add(tx_sig)

        try:
            try:
                tx_result = await self.fetch_solana_transaction(tx_sig)
            except Exception as exc:
                logger.error("Falha de rede ao consultar Solana RPC para %s: %s", tx_sig, exc)
                return {
                    "valid": False,
                    "reason": f"rpc_verification_error: {exc}",
                    "txSignature": tx_sig,
                    "receivedAtomic": 0,
                }

            is_ok, reason, received_atomic = self.verify_parsed_transaction_result(
                tx_result=tx_result,
                required_atomic_amount=required_atomic_amount,
            )
            if not is_ok:
                return {
                    "valid": False,
                    "reason": reason,
                    "txSignature": tx_sig,
                    "receivedAtomic": received_atomic,
                }

            async with self._lock:
                if self.is_signature_used(tx_sig):
                    return {
                        "valid": False,
                        "reason": "replay_attack_detected",
                        "txSignature": tx_sig,
                        "receivedAtomic": 0,
                    }
                self.mark_signature_used(tx_sig)

            return {
                "valid": True,
                "reason": "verified_on_chain",
                "txSignature": tx_sig,
                "receivedAtomic": received_atomic,
                "recipientWallet": self.recipient_wallet,
                "asset": "USDC",
                "network": SOLANA_CAIP2_NETWORK,
                "verifiedAt": int(time.time()),
            }
        finally:
            async with self._lock:
                self._in_flight_signatures.discard(tx_sig)


def _load_cached_x402_actor_fn(slug: str) -> tuple[Callable[..., Any], dict[str, Any]]:
    """Carrega e armazena em cache a função assíncrona e o input default de um Ator."""
    cached = _ACTOR_FN_CACHE.get(slug)
    if cached is not None:
        return cached

    main_py = ACTORS_DIR / slug / "src" / "main.py"
    if not main_py.exists():
        raise FileNotFoundError(f"Motor do ator {slug} não encontrado em {main_py}")

    module_name = f"actor_x402_{slug.replace('-', '_')}"
    spec = importlib.util.spec_from_file_location(module_name, main_py)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Falha ao carregar especificação do módulo para {slug}")

    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    candidate_names = (
        "process_input",
        "run_pipeline",
        "run_tax_audit",
        "run_pncp_radar",
        "run_tiss_validation",
        "run_cte_audit",
        "run_npi_enrichment",
    )
    process_fn = None
    for fn_name in candidate_names:
        fn = getattr(mod, fn_name, None)
        if callable(fn):
            process_fn = fn
            break

    if process_fn is None:
        raise RuntimeError(f"Função de execução ausente em {slug}")

    default_input = getattr(mod, "DEFAULT_ACTOR_INPUT", {})
    default_dict = dict(default_input) if isinstance(default_input, dict) else {}
    _ACTOR_FN_CACHE[slug] = (process_fn, default_dict)
    return process_fn, default_dict


def _estimate_batch_units(payload: dict[str, Any]) -> int:
    """Estima o número de unidades faturáveis no payload para evitar arbitragem de lote."""
    max_units = 1
    for val in payload.values():
        if isinstance(val, list):
            max_units = max(max_units, len(val))
    return max_units


async def execute_local_actor_engine(slug: str, payload: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Executa localmente o motor determinístico `process_input` do Ator solicitado (com cache em memória).
    Garante resposta em milissegundos sem custo de servidor intermediário.
    """
    process_fn, default_dict = _load_cached_x402_actor_fn(slug)
    effective_payload = payload if payload else default_dict
    result = await process_fn(effective_payload)
    if isinstance(result, tuple) and len(result) >= 1:
        items = result[0]
        return items if isinstance(items, list) else [items]
    if isinstance(result, list):
        return result
    if isinstance(result, dict):
        return [result]
    return []


def build_free_catalog_status_payload(base_url: str = PUBLIC_BASE_URL) -> dict[str, Any]:
    """
    Constrói o payload Freemium ($0.00 USD) de descoberta e status (`GET /v1/free-catalog-status`)
    para que crawlers x402, diretórios MCP e agentes autônomos consultem a suíte gratuitamente.
    """
    clean_base = base_url.rstrip("/")
    return {
        "status": "online",
        "service": "b2b-quant-mcp-n8n-suite",
        "version": "2.1.0",
        "freeTier": True,
        "priceUsd": 0.0,
        "protocol": "x402",
        "x402Version": 1,
        "network": SOLANA_CAIP2_NETWORK,
        "asset": "USDC",
        "mint": SOLANA_USDC_MINT,
        "payTo": SOLANA_USDC_WALLET,
        "masterMcpActor": f"{APIFY_USERNAME}/b2b-quant-mcp-server",
        "totalActors": len(ACTOR_SLUGS),
        "totalTools": len(ACTOR_SLUGS),
        "discoveryManifests": {
            "openapi": f"{clean_base}/openapi.json",
            "llmsTxt": f"{clean_base}/llms.txt",
            "llmsFullTxt": f"{clean_base}/llms-full.txt",
            "wellKnownMcp": f"{clean_base}/.well-known/mcp.json",
            "wellKnownX402": f"{clean_base}/.well-known/x402.json",
            "wellKnownAgent": f"{clean_base}/.well-known/agent.json",
        },
        "actors": list(ACTOR_SLUGS),
    }


def build_agentcash_openapi_spec(base_url: str = PUBLIC_BASE_URL) -> dict[str, Any]:
    """
    Gera a especificação OpenAPI 3.1.0 completa para os 31 Motores B2B + 1 rota Freemium ($0.00):
    - `GET /v1/free-catalog-status` com `x-price-usd: 0.0` e `x-402-free-tier: true`;
    - `info.x-guidance` exigido pelo indexador `AgentCash.dev` (`@agentcash/discovery`);
    - `x-payment-info` em cada operação `POST /v1/x402/{slug}` declarando `x402` (USDC Solana) e preço em USD;
    - `x-bazaar` (`extensions.bazaar`) para indexação automática no `x402 Bazaar`.
    """
    paths: dict[str, Any] = {}
    clean_base = base_url.rstrip("/")

    paths["/v1/free-catalog-status"] = {
        "get": {
            "summary": "Freemium $0.00 B2B MCP & x402 Catalog Discovery & Health Status",
            "description": (
                "Free ($0.00 USD) instant discovery and health endpoint for autonomous AI agents, "
                "MCP clients, and x402 crawlers. Returns the full catalog of 31 B2B tools, schemas, "
                "and Solana USDC payment coordinates without requiring an X-PAYMENT header."
            ),
            "operationId": "get_free_catalog_status",
            "tags": ["FREE_DISCOVERY", "AI", "DEVELOPER_TOOLS"],
            "x-price-usd": 0.0,
            "x-402-free-tier": True,
            "x-payment-info": {
                "protocols": [],
                "price": {
                    "mode": "free",
                    "currency": "USD",
                    "amount": "0",
                },
            },
            "x-bazaar": {
                "discoverable": True,
                "freeTier": True,
                "category": "b2b-compliance-and-quant-intelligence",
            },
            "responses": {
                "200": {
                    "description": "Free catalog status and 31-tool index ($0.00 USD).",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "status": {"type": "string", "example": "online"},
                                    "freeTier": {"type": "boolean", "example": True},
                                    "priceUsd": {"type": "number", "example": 0.0},
                                    "totalActors": {"type": "integer", "example": 31},
                                    "payTo": {"type": "string", "example": SOLANA_USDC_WALLET},
                                    "actors": {"type": "array", "items": {"type": "string"}},
                                },
                            }
                        }
                    },
                }
            },
        }
    }

    for slug in ACTOR_SLUGS:
        meta = load_actor_metadata(slug)
        actor_info = meta["actor"]
        in_schema = meta["input_schema"]
        ds_schema = meta["dataset_schema"]
        mon = MONETIZATION_CONFIG.get(slug, {})

        title = actor_info.get("title", slug)
        description = actor_info.get("description", "")
        price_usd = mon.get("price_usd", 0.02)
        price_str = format_usd_amount(price_usd)
        atomic_str = usd_to_usdc_atomic_units(price_usd)
        op_id = "run_" + slug.replace("-", "_")

        req_props = in_schema.get("properties", {})
        req_fields = in_schema.get("required", [])
        out_props = ds_schema.get("fields", {}).get("properties", {})

        paths[f"/v1/x402/{slug}"] = {
            "post": {
                "summary": title,
                "description": (
                    f"{description} | Settled natively on Solana Mainnet in USDC ({price_str} USDC per call) "
                    f"to wallet `{SOLANA_USDC_WALLET}` via the x402 protocol."
                ),
                "operationId": op_id,
                "tags": [str(c) for c in mon.get("categories", ["AI", "BUSINESS"])],
                "x-price-usd": float(price_usd),
                "x-402-free-tier": False,
                "parameters": [
                    {
                        "name": "X-PAYMENT",
                        "in": "header",
                        "required": False,
                        "description": "Signed Solana USDC transaction signature or Base64 x402 payment payload.",
                        "schema": {"type": "string"},
                    }
                ],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": req_props,
                                **({"required": req_fields} if req_fields else {}),
                            }
                        }
                    },
                },
                "responses": {
                    "200": {
                        "description": f"Deterministic JSON output from {title}.",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "status": {"type": "string", "example": "succeeded"},
                                        "actor": {"type": "string", "example": slug},
                                        "payment": {"type": "object"},
                                        "data": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": out_props,
                                            },
                                        },
                                    },
                                }
                            }
                        },
                    },
                    "402": {
                        "description": "Payment Required — Returns x402Version 1 challenge for Solana USDC.",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "x402Version": {"type": "integer", "example": 1},
                                        "accepts": {"type": "array", "items": {"type": "object"}},
                                    },
                                }
                            }
                        },
                    },
                },
                "x-payment-info": {
                    "protocols": [
                        {
                            "x402": {
                                "scheme": "exact",
                                "network": SOLANA_CAIP2_NETWORK,
                                "asset": "USDC",
                                "mint": SOLANA_USDC_MINT,
                                "payTo": SOLANA_USDC_WALLET,
                                "maxAmountRequired": atomic_str,
                            }
                        }
                    ],
                    "price": {
                        "mode": "fixed",
                        "currency": "USD",
                        "amount": price_str,
                    },
                },
                "x-bazaar": {
                    "discoverable": True,
                    "category": "b2b-compliance-and-quant-intelligence",
                    "network": SOLANA_CAIP2_NETWORK,
                    "asset": "USDC",
                    "payTo": SOLANA_USDC_WALLET,
                    "maxAmountRequired": atomic_str,
                },
            }
        }

    return {
        "openapi": "3.1.0",
        "info": {
            "title": "B2B Quant, Regulatory Compliance & KYB Suite (x402 Solana USDC Edition)",
            "version": "2.1.0",
            "description": (
                "31 Deterministic B2B Regulatory Compliance, Master MCP Server, SEC EDGAR, SAM.gov, EU TED, "
                "UK Companies House/FCA, Sanctions AML, OSHA, SSL CT, GLEIF LEI, Brazil BCB/PIX/CNPJ, "
                "CISA KEV, and Lead Intelligence APIs powered by native x402 Solana USDC micropayments."
            ),
            "x-guidance": (
                "Ping GET /v1/free-catalog-status for free ($0.00) discovery. To invoke any paid tool, send a POST "
                "request to /v1/x402/{actor_slug} with a JSON body matching its input schema. "
                "If no X-PAYMENT header is provided, the gateway responds with HTTP 402 containing x402Version 1 "
                f"payment instructions for USDC on Solana Mainnet ({SOLANA_CAIP2_NETWORK}) payable to "
                f"{SOLANA_USDC_WALLET}. Settle the transfer and retry with the X-PAYMENT header."
            ),
            "contact": {
                "name": "B2B Quant APIs (@b2b-quant-apis)",
                "url": "https://github.com/jesleytassili-glitch/b2b-quant-mcp-n8n-suite",
            },
        },
        "servers": [
            {
                "url": clean_base,
                "description": "Primary x402 Discovery & Documentation Host",
            },
            {
                "url": "https://mcp.apify.com",
                "description": "Managed Streamable HTTP MCP Execution Cluster",
            },
        ],
        "paths": paths,
    }


def build_well_known_x402_manifest(base_url: str = PUBLIC_BASE_URL) -> dict[str, Any]:
    """
    Gera o manifesto de descoberta `/.well-known/x402.json` para indexadores `x402 Bazaar`,
    `AgentCash.dev` e `SkillMarket.space`.
    """
    clean_base = base_url.rstrip("/")
    resources: list[dict[str, Any]] = []
    for slug in ACTOR_SLUGS:
        challenge = build_x402_challenge(slug, base_url=clean_base)
        meta = load_actor_metadata(slug)
        resources.append(
            {
                "slug": slug,
                "title": meta["actor"].get("title", slug),
                "description": meta["actor"].get("description", ""),
                "endpoint": f"{clean_base}/v1/x402/{slug}",
                "method": "POST",
                "mcpEndpoint": f"https://mcp.apify.com/?actors={APIFY_USERNAME}/{slug}",
                "openapiUrl": f"{clean_base}/openapi.json",
                "x402Version": 1,
                "accepts": challenge["accepts"],
                "inputSchema": meta["input_schema"],
            }
        )

    return {
        "x402Version": 1,
        "provider": {
            "name": "B2B Quant & Regulatory Compliance Suite (@b2b-quant-apis)",
            "publisher": "jesleytassili-glitch",
            "wallet": SOLANA_USDC_WALLET,
            "network": SOLANA_CAIP2_NETWORK,
            "asset": "USDC",
            "mint": SOLANA_USDC_MINT,
            "freeTierStatusEndpoint": f"{clean_base}/v1/free-catalog-status",
            "openapi": f"{clean_base}/openapi.json",
            "llmsTxt": f"{clean_base}/llms.txt",
            "wellKnownMcp": f"{clean_base}/.well-known/mcp.json",
            "wellKnownAgent": f"{clean_base}/.well-known/agent.json",
            "repository": "https://github.com/jesleytassili-glitch/b2b-quant-mcp-n8n-suite",
        },
        "totalResources": len(resources),
        "freeTierDiscoveryEndpoint": f"{clean_base}/v1/free-catalog-status",
        "resources": resources,
    }


def create_x402_app(verifier: SolanaX402Verifier | None = None) -> Starlette:
    """Cria a instância ASGI (Starlette) de alta performance do Gateway x402 Solana USDC."""
    if verifier is not None:
        active_verifier = verifier
    else:
        default_store = None if os.environ.get("PYTEST_CURRENT_TEST") else DEFAULT_REPLAY_STORE_PATH
        active_verifier = SolanaX402Verifier(replay_store_path=default_store)

    async def health_check(request: Request) -> JSONResponse:
        return JSONResponse(
            content={
                "status": "ok",
                "protocol": "x402",
                "x402Version": 1,
                "network": SOLANA_CAIP2_NETWORK,
                "asset": "USDC",
                "payTo": SOLANA_USDC_WALLET,
                "payToAta": SOLANA_USDC_PAY_TO_ATA,
                "totalActors": len(ACTOR_SLUGS),
            }
        )

    async def get_free_catalog_status(request: Request) -> JSONResponse:
        return JSONResponse(content=build_free_catalog_status_payload())

    async def get_openapi_spec(request: Request) -> JSONResponse:
        return JSONResponse(content=build_agentcash_openapi_spec())

    async def get_well_known_x402(request: Request) -> JSONResponse:
        return JSONResponse(content=build_well_known_x402_manifest())

    async def get_catalog(request: Request) -> JSONResponse:
        manifest = build_well_known_x402_manifest()
        return JSONResponse(content=manifest)

    async def invoke_x402_actor(request: Request) -> JSONResponse:
        slug = str(request.path_params.get("slug") or "")
        if slug not in ACTOR_SLUGS:
            return JSONResponse(
                status_code=404,
                content={"error": f"Actor '{slug}' not found."},
            )

        body_bytes = await request.body()
        if len(body_bytes) > MAX_X402_BODY_BYTES:
            return JSONResponse(
                status_code=413,
                content={"error": f"Request body exceeds limit ({MAX_X402_BODY_BYTES} bytes)."},
            )

        payment_header = request.headers.get("X-PAYMENT") or request.headers.get("PAYMENT-SIGNATURE")
        challenge = build_x402_challenge(slug)
        unit_atomic = int(challenge["accepts"][0]["maxAmountRequired"])

        parsed_payload: dict[str, Any] = {}
        if body_bytes:
            try:
                raw_json = json.loads(body_bytes.decode("utf-8"))
                if isinstance(raw_json, dict):
                    parsed_payload = raw_json
            except Exception as exc:
                if payment_header:
                    return JSONResponse(
                        status_code=400,
                        content={"error": f"Invalid JSON request body: {exc}"},
                    )

        batch_units = _estimate_batch_units(parsed_payload)
        if batch_units > MAX_X402_BATCH_ITEMS:
            return JSONResponse(
                status_code=400,
                content={"error": f"Batch size {batch_units} exceeds max_items_per_request ({MAX_X402_BATCH_ITEMS})."},
            )
        required_atomic = unit_atomic * max(1, batch_units)
        challenge["accepts"][0]["maxAmountRequired"] = str(required_atomic)

        if not payment_header:
            return JSONResponse(
                status_code=402,
                content=challenge,
                headers={
                    "X-Payment-Required": (
                        f'x402; version="1"; network="{SOLANA_CAIP2_NETWORK}"; '
                        f'asset="USDC"; amount="{required_atomic}"; payTo="{SOLANA_USDC_WALLET}"'
                    ),
                    "Cache-Control": "no-store",
                },
            )

        try:
            verification = await active_verifier.verify_payment(
                header_value=payment_header,
                required_atomic_amount=required_atomic,
            )
        except ValueError as exc:
            return JSONResponse(
                status_code=400,
                content={
                    "error": "Invalid X-PAYMENT header format",
                    "detail": str(exc),
                    "x402Challenge": challenge,
                },
            )

        if not verification.get("valid"):
            status_code = 409 if verification.get("reason") == "replay_attack_detected" else 402
            return JSONResponse(
                status_code=status_code,
                content={
                    "error": "Payment verification failed",
                    "reason": verification.get("reason"),
                    "txSignature": verification.get("txSignature"),
                    "x402Challenge": challenge,
                },
            )

        items = await execute_local_actor_engine(slug, parsed_payload)
        return JSONResponse(
            status_code=200,
            content={
                "status": "succeeded",
                "actor": slug,
                "payment": verification,
                "count": len(items),
                "data": items,
            },
        )

    routes = [
        Route("/health", endpoint=health_check, methods=["GET"]),
        Route("/health.json", endpoint=health_check, methods=["GET"]),
        Route("/v1/free-catalog-status", endpoint=get_free_catalog_status, methods=["GET"]),
        Route("/v1/free-catalog-status.json", endpoint=get_free_catalog_status, methods=["GET"]),
        Route("/openapi.json", endpoint=get_openapi_spec, methods=["GET"]),
        Route("/.well-known/x402.json", endpoint=get_well_known_x402, methods=["GET"]),
        Route("/v1/x402/catalog", endpoint=get_catalog, methods=["GET"]),
        Route("/v1/x402/{slug}", endpoint=invoke_x402_actor, methods=["POST"]),
    ]

    return Starlette(debug=False, routes=routes)


app = create_x402_app()

