#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gerador Automatizado de 31 Especificações Individuais OpenAPI 3.0.3 (`specs_openapi_31/`).

Gera 1 arquivo JSON OpenAPI 3.0.3 individual e 100% compatível com o importador 1-Clique
do RapidAPI Studio (Nokia Rapid) e do Zyla API Hub para cada uma das 31 APIs B2B
(`b2b-gov-procurement-pncp-radar` até `b2b-quant-mcp-server`).

Cada especificação inclui:
- Descrição comercial em inglês voltada a compradores corporativos B2B;
- Categoria exata do RapidAPI Hub e do Zyla API Hub;
- Tags de busca SEO de alta intenção comercial;
- Schemas rigorosos de Request e Response em formato OpenAPI 3.0.3 puro;
- Exemplos reais de payload (`example`) para Request e Response;
- Snippets de código prontos para produção em `cURL`, `Python` e `Node.js`.
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any

SUITE_DIR = Path(__file__).resolve().parent
WORKSPACE_ROOT = SUITE_DIR.parent
APIFY_SUITE_DIR = WORKSPACE_ROOT / "apify_store_suite"

for p in (WORKSPACE_ROOT, APIFY_SUITE_DIR):
    p_str = str(p)
    if p.exists() and p_str not in sys.path:
        sys.path.insert(0, p_str)

from build_m2m_trojan_pack import ACTOR_DEFAULT_PAYLOADS
from deploy_apify_suite import ACTOR_SLUGS, ACTORS_DIR, MONETIZATION_CONFIG
from export_mcp_rapidapi_manifests import load_actor_metadata

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("generate_rapidapi_zyla_specs")

SPECS_OUTPUT_DIR = SUITE_DIR / "specs_openapi_31"
APIS_JSON_OUTPUT_PATH = SUITE_DIR / "apis.json"
POSTMAN_COLLECTION_OUTPUT_PATH = SUITE_DIR / "postman_public_network_collection.json"
APIFY_USERNAME = "b2b-quant-apis"
WISE_ACCOUNT_NUMBER = "890361113"
ENGINE_VERSION = "3.0.0"
GITHUB_RELEASE_TAG = "v2.2.0"
DEFAULT_GATEWAY_BASE_URL = "https://b2b-quant-rapidapi-gateway.jesleytassili.workers.dev"
PUBLIC_GITHUB_PAGES_ORIGIN = "https://jesleytassili-glitch.github.io"
PUBLIC_SPECS_BASE_URL = f"{PUBLIC_GITHUB_PAGES_ORIGIN}/specs_openapi_31"
PUBLIC_SUITE_SPECS_BASE_URL = f"{PUBLIC_GITHUB_PAGES_ORIGIN}/b2b-quant-mcp-n8n-suite/specs_openapi_31"
PUBLIC_APIS_JSON_URL = f"{PUBLIC_GITHUB_PAGES_ORIGIN}/apis.json"
PUBLIC_WELL_KNOWN_APIS_JSON_URL = f"{PUBLIC_GITHUB_PAGES_ORIGIN}/.well-known/apis.json"

# Mapeamento comercial exato de Categorias e Tags SEO por API para RapidAPI Hub e Zyla API Hub
MARKETPLACE_TAXONOMY: dict[str, dict[str, Any]] = {
    "b2b-gov-procurement-pncp-radar": {
        "rapidapi_category": "Business",
        "zyla_category": "Government & Legal",
        "seo_tags": ["brazil-procurement", "pncp", "public-tenders", "b2g-leads", "government-contracts", "lei-14133", "bidding-radar"],
        "buyer_persona": "GovCon Capture Teams, B2B Sales Intelligence Platforms, and ERP Tender Modules",
    },
    "brazil-tax-reform-ncm-classtrib-auditor": {
        "rapidapi_category": "Finance",
        "zyla_category": "Taxes & Compliance",
        "seo_tags": ["brazil-tax-reform", "ncm-auditor", "ibs-cbs", "classtrib", "nfe-compliance", "lc-214-2025", "erp-tax-engine"],
        "buyer_persona": "Tax Automation ERPs, Accounting SaaS, eCommerce Checkout Engines, and Big4 Tax Auditors",
    },
    "healthcare-tiss-xml-validator": {
        "rapidapi_category": "Medical",
        "zyla_category": "Healthcare",
        "seo_tags": ["healthcare-billing", "ans-tiss-xml", "medical-claims", "glosa-prevention", "tuss-validator", "epilogo-hash", "hospital-rcm"],
        "buyer_persona": "Hospital Revenue Cycle Management (RCM) Systems, HealthTech Insurers, and Medical Billing Platforms",
    },
    "brazil-antt-freight-cte-auditor": {
        "rapidapi_category": "Logistics",
        "zyla_category": "Logistics & Shipping",
        "seo_tags": ["freight-audit", "antt-minimum-floor", "cte-xml", "logistics-compliance", "road-transport", "tms-integration", "shipping-cost"],
        "buyer_persona": "Transportation Management Systems (TMS), 3PL Logistics Operators, and Supply Chain Controllers",
    },
    "us-healthcare-npi-provider-lead-enricher": {
        "rapidapi_category": "Medical",
        "zyla_category": "Healthcare",
        "seo_tags": ["npi-registry", "nppes-cms", "healthcare-leads", "medical-providers", "doctor-lookup", "hipaa-kyb", "pharma-crm"],
        "buyer_persona": "MedTech Sales Teams, Healthcare CRMs, Credentialing Platforms, and Digital Health Directories",
    },
    "us-fda-recalls-safety-monitor": {
        "rapidapi_category": "Medical",
        "zyla_category": "Healthcare",
        "seo_tags": ["fda-recalls", "openfda", "drug-safety", "medical-device-recalls", "food-safety", "supply-chain-risk", "pharmacovigilance"],
        "buyer_persona": "Pharmaceutical Compliance Teams, Hospital Pharmacies, Retail Supply Chains, and InsurTech Underwriters",
    },
    "global-b2b-email-domain-security-auditor": {
        "rapidapi_category": "Cybersecurity",
        "zyla_category": "Security",
        "seo_tags": ["email-verification", "dmarc-spf-mx", "domain-security", "disposable-email", "kyb-fraud-prevention", "b2b-lead-hygiene", "secops"],
        "buyer_persona": "B2B Outbound Platforms, FinTech Onboarding Anti-Fraud Engines, and SOC Security Teams",
    },
    "us-clinical-trials-biotech-radar": {
        "rapidapi_category": "Medical",
        "zyla_category": "Healthcare",
        "seo_tags": ["clinical-trials", "biotech-intelligence", "nih-clinicaltrials", "pharma-pipeline", "cro-leads", "phase2-phase3", "life-sciences"],
        "buyer_persona": "Contract Research Organizations (CROs), Biotech Venture Capitalists, and Pharma BD&L Teams",
    },
    "us-nhtsa-vehicle-vin-recall-auditor": {
        "rapidapi_category": "Logistics",
        "zyla_category": "Logistics & Shipping",
        "seo_tags": ["vin-decoder", "nhtsa-recalls", "vehicle-safety", "fleet-management", "auto-insurance", "automotive-kyb", "vpic-api"],
        "buyer_persona": "Auto InsurTechs, Commercial Fleet Managers, Automotive Marketplaces, and Lending Underwriters",
    },
    "brazil-b2b-cnpj-qsa-lead-enricher": {
        "rapidapi_category": "Business",
        "zyla_category": "Company Data",
        "seo_tags": ["cnpj-lookup", "receita-federal", "qsa-ubo-partners", "brazil-kyb", "company-enrichment", "cnae-lookup", "b2b-credit-risk"],
        "buyer_persona": "FinTech KYB Onboarding Flows, B2B Credit Bureaus, and Enterprise CRM Enrichment Pipelines",
    },
    "us-sec-edgar-filings-insider-radar": {
        "rapidapi_category": "Finance",
        "zyla_category": "Finance",
        "seo_tags": ["sec-edgar", "10k-10q-8k", "form-4-insider", "quantitative-finance", "corporate-governance", "cik-lookup", "equity-research"],
        "buyer_persona": "Quantitative Hedge Funds, Equity Research Platforms, WealthTech Apps, and M&A Advisory Teams",
    },
    "eu-vies-vat-tax-compliance-auditor": {
        "rapidapi_category": "Finance",
        "zyla_category": "Taxes & Compliance",
        "seo_tags": ["eu-vat-validation", "vies-api", "reverse-charge", "cross-border-tax", "european-kyb", "vat-compliance", "b2b-invoicing"],
        "buyer_persona": "European B2B SaaS Billing Engines, Cross-Border Marketplaces, and ERP Tax Compliance Modules",
    },
    "us-epa-echo-environmental-compliance-auditor": {
        "rapidapi_category": "Data",
        "zyla_category": "Government & Legal",
        "seo_tags": ["epa-echo", "esg-compliance", "environmental-risk", "clean-air-water-act", "rcra-hazmat", "industrial-due-diligence", "supply-chain-esg"],
        "buyer_persona": "ESG Rating Agencies, Institutional Investors, Environmental Law Firms, and Supply Chain Risk Teams",
    },
    "us-fdic-bankfind-institution-financial-auditor": {
        "rapidapi_category": "Finance",
        "zyla_category": "Finance",
        "seo_tags": ["fdic-bankfind", "bank-solvency", "treasury-risk", "tier1-capital", "banking-kyb", "counterparty-risk", "us-banks"],
        "buyer_persona": "Corporate Treasurers, CFOs, Institutional Counterparty Risk Teams, and FinTech Payment Routers",
    },
    "us-sam-gov-federal-procurement-auditor": {
        "rapidapi_category": "Business",
        "zyla_category": "Government & Legal",
        "seo_tags": ["sam-gov", "usaspending", "federal-contracts", "govcon-intelligence", "naics-psc", "b2g-procurement", "defense-contracts"],
        "buyer_persona": "U.S. Federal Defense Contractors, GovCon BD Teams, and Public Sector Market Intelligence Platforms",
    },
    "multi-ats-tech-job-board-hiring-radar": {
        "rapidapi_category": "Business",
        "zyla_category": "Company Data",
        "seo_tags": ["hiring-signals", "greenhouse-ats", "tech-jobs-api", "b2b-buying-intent", "recruiting-intelligence", "sales-triggers", "revops"],
        "buyer_persona": "B2B Outbound Sales Teams, Executive Search Firms, Venture Capitalists, and RevOps Data Pipelines",
    },
    "global-gleif-lei-corporate-ownership-kyb": {
        "rapidapi_category": "Finance",
        "zyla_category": "Company Data",
        "seo_tags": ["gleif-lei", "legal-entity-identifier", "global-kyb", "corporate-ownership", "mifid-ii-emir", "parent-subsidiary", "aml-onboarding"],
        "buyer_persona": "Global Investment Banks, RegTech KYB Platforms, Crypto Institutional Desks, and Trade Finance Systems",
    },
    "us-census-fcc-real-estate-geo-enricher": {
        "rapidapi_category": "Data",
        "zyla_category": "Company Data",
        "seo_tags": ["us-census-fips", "fcc-area-api", "real-estate-analytics", "geospatial-enrichment", "census-tract", "proptech", "mortgage-hmda"],
        "buyer_persona": "PropTech Platforms, Mortgage Lenders (HMDA/CRA Compliance), Real Estate REITs, and Site Selection Teams",
    },
    "icann-rdap-domain-whois-brand-recon": {
        "rapidapi_category": "Cybersecurity",
        "zyla_category": "Security",
        "seo_tags": ["icann-rdap", "whois-lookup", "domain-age", "brand-protection", "dnssec-audit", "anti-phishing", "threat-intelligence"],
        "buyer_persona": "Brand Protection Agencies, SOC Threat Hunters, Fraud Prevention Engines, and Domain Registrars",
    },
    "cisa-kev-ransomware-vulnerability-auditor": {
        "rapidapi_category": "Cybersecurity",
        "zyla_category": "Security",
        "seo_tags": ["cisa-kev", "cve-vulnerability", "ransomware-audit", "patch-management", "bod-22-01", "secops-threat-intel", "exploit-catalog"],
        "buyer_persona": "CISOs, Vulnerability Management Platforms, MSSPs, and Cyber Insurance Underwriters",
    },
    "brazil-bcb-ptax-sgs-financial-contract-indexer": {
        "rapidapi_category": "Finance",
        "zyla_category": "Finance",
        "seo_tags": ["banco-central-brasil", "ptax-usd-brl", "selic-cdi-ipca", "igpm-indexer", "contract-readjustment", "brazil-macro-api", "fintech-rates"],
        "buyer_persona": "Real Estate ERPs, LegalTech Contract Management Systems, FX Desks, and Brazilian FinTechs",
    },
    "brazil-pix-ispb-cvm-financial-kyb-auditor": {
        "rapidapi_category": "Finance",
        "zyla_category": "Finance",
        "seo_tags": ["brazil-pix-ispb", "str-spi-participants", "bank-routing-kyb", "bacen-institutions", "payment-clearing", "fintech-compliance", "compe-ispb"],
        "buyer_persona": "Payment Service Providers (PSPs), Banking-as-a-Service (BaaS) Platforms, and Treasury Reconciliation Systems",
    },
    "brazil-ibge-cnae-municipal-b2b-expansion-enricher": {
        "rapidapi_category": "Business",
        "zyla_category": "Company Data",
        "seo_tags": ["ibge-cnae", "concla-subclass", "brazil-tax-activities", "municipal-expansion", "b2b-market-sizing", "company-classification", "simples-nacional"],
        "buyer_persona": "Accounting Automation Platforms, B2B Lead Scoring Engines, and Franchise Expansion Analysts",
    },
    "brazil-cep-geocoordinates-logistics-auditor": {
        "rapidapi_category": "Logistics",
        "zyla_category": "Logistics & Shipping",
        "seo_tags": ["brazil-cep-lookup", "postal-geocoding", "ibge-municipality-code", "nfe-address-validator", "last-mile-logistics", "ddd-lookup", "ecommerce-checkout"],
        "buyer_persona": "eCommerce Checkout Flows, Last-Mile Delivery Routers, NF-e Issuers, and Retail Omni-Channel ERPs",
    },
    "brazil-camara-legislative-regulatory-risk-radar": {
        "rapidapi_category": "Data",
        "zyla_category": "Government & Legal",
        "seo_tags": ["brazil-congress-api", "camara-deputados", "legislative-radar", "regulatory-risk", "public-policy-tracker", "gov-relations", "pec-pl-plp"],
        "buyer_persona": "Government Relations (RIG) Teams, Corporate Legal Departments, Institutional Funds, and Law Firms",
    },
    "us-osha-workplace-safety-violation-auditor": {
        "rapidapi_category": "Business",
        "zyla_category": "Government & Legal",
        "seo_tags": ["osha-violations", "workplace-safety", "ehs-compliance", "industrial-inspections", "workers-comp-underwriting", "supply-chain-audit", "dol-osha"],
        "buyer_persona": "Commercial Insurance Underwriters (Workers' Comp), EHS Compliance Platforms, and M&A Due Diligence Teams",
    },
    "eu-ted-public-tenders-procurement-radar": {
        "rapidapi_category": "Business",
        "zyla_category": "Government & Legal",
        "seo_tags": ["eu-ted-tenders", "european-procurement", "cpv-codes", "public-sector-bids", "b2g-europe", "official-journal-ojs", "government-rfp"],
        "buyer_persona": "European B2G Bid Teams, Multinational IT Integrators, and Global Public Procurement Aggregators",
    },
    "uk-fca-companies-house-kyb-compliance-auditor": {
        "rapidapi_category": "Finance",
        "zyla_category": "Company Data",
        "seo_tags": ["uk-companies-house", "crn-lookup", "uk-kyb-verification", "fca-compliance", "british-corporate-registry", "gleif-uk", "aml-due-diligence"],
        "buyer_persona": "UK/EU FinTechs, Commercial Banks, Legal Conveyancing Platforms, and Vendor Onboarding Systems",
    },
    "global-sanctions-pep-interpol-watchlist-screener": {
        "rapidapi_category": "Cybersecurity",
        "zyla_category": "Security",
        "seo_tags": ["ofac-sdn-sanctions", "aml-kyc-screening", "pep-watchlist", "eu-un-sanctions", "financial-crime-compliance", "entity-screening", "regtech-aml"],
        "buyer_persona": "Crypto Exchanges, Cross-Border Payment Gateways, Neobanks, and AML/KYC Compliance Officers",
    },
    "b2b-ssl-tls-ct-log-subdomain-attack-surface-auditor": {
        "rapidapi_category": "Cybersecurity",
        "zyla_category": "Security",
        "seo_tags": ["certificate-transparency", "subdomain-discovery", "attack-surface-management", "easm-recon", "shadow-it-audit", "ssl-tls-monitor", "secops-api"],
        "buyer_persona": "External Attack Surface Management (EASM) Platforms, Penetration Testers, Bug Bounty Automation, and SOCs",
    },
    "b2b-quant-mcp-server": {
        "rapidapi_category": "Artificial Intelligence/Machine Learning",
        "zyla_category": "AI & Machine Learning",
        "seo_tags": ["mcp-server", "model-context-protocol", "ai-agent-tools", "b2b-compliance-suite", "claude-cursor-tools", "langchain-b2b", "autonomous-agents"],
        "buyer_persona": "AI Agent Builders, Enterprise LLM Orchestration Teams, and Multi-Agent FinTech/SecOps Platforms",
    },
}

STANDARD_PRICING_TIERS = {
    "BASIC": {
        "tier": "BASIC",
        "label": "Freemium Developer Trial",
        "monthlyPriceUsd": 0.00,
        "monthlyQuotaRequests": 15,
        "overagePricePerRequestUsd": 0.00,
        "hardLimit": True,
    },
    "PRO": {
        "tier": "PRO",
        "label": "Startup & RevOps Pipeline",
        "monthlyPriceUsd": 19.00,
        "monthlyQuotaRequests": 1000,
        "overagePricePerRequestUsd": 0.02,
        "hardLimit": False,
    },
    "ULTRA": {
        "tier": "ULTRA",
        "label": "Mid-Market Automation Cluster",
        "monthlyPriceUsd": 49.00,
        "monthlyQuotaRequests": 5000,
        "overagePricePerRequestUsd": 0.015,
        "hardLimit": False,
    },
    "MEGA": {
        "tier": "MEGA",
        "label": "Enterprise High-Throughput SLA",
        "monthlyPriceUsd": 149.00,
        "monthlyQuotaRequests": 25000,
        "overagePricePerRequestUsd": 0.010,
        "hardLimit": False,
    },
}


def _build_canonical_request_example(slug: str, in_props_raw: dict[str, Any]) -> dict[str, Any]:
    """
    Constrói o payload de exemplo canônico (`example`) contendo estritamente chaves declaradas
    em `input_schema.json`, priorizando `prefill`, `ACTOR_DEFAULT_PAYLOADS` (quando a chave
    existe no schema) e `default`.
    """
    legacy_defaults = ACTOR_DEFAULT_PAYLOADS.get(slug, {})
    canonical: dict[str, Any] = {}

    for prop_k, prop_v in in_props_raw.items():
        if not isinstance(prop_v, dict):
            continue
        prefill_val = prop_v.get("prefill")
        default_val = prop_v.get("default")
        legacy_val = legacy_defaults.get(prop_k)

        if prefill_val not in (None, [], ""):
            canonical[prop_k] = prefill_val
        elif legacy_val not in (None, [], ""):
            canonical[prop_k] = legacy_val
        elif default_val is not None:
            canonical[prop_k] = default_val
        elif prefill_val is not None:
            canonical[prop_k] = prefill_val
        elif legacy_val is not None:
            canonical[prop_k] = legacy_val

    return canonical


def _clean_openapi_303_property(prop_key: str, prop_meta: dict[str, Any], default_payload: dict[str, Any]) -> dict[str, Any]:
    """
    Converte uma propriedade de `input_schema.json` Apify v1 para JSON Schema estrito do OpenAPI 3.0.3.
    Remove chaves proprietárias (`editor`, `prefill`, `enumTitles`, `isSecret`) incompatíveis com o importador.
    """
    raw_type = prop_meta.get("type", "string")
    if isinstance(raw_type, list):
        raw_type = next((t for t in raw_type if t != "null"), "string")
    if raw_type not in ("string", "number", "integer", "boolean", "array", "object"):
        raw_type = "string"

    cleaned: dict[str, Any] = {
        "type": raw_type,
        "title": str(prop_meta.get("title") or prop_key),
        "description": str(prop_meta.get("description") or f"Parameter {prop_key}"),
    }

    if raw_type == "array":
        items_meta = prop_meta.get("items")
        if isinstance(items_meta, dict) and "type" in items_meta:
            item_type = str(items_meta["type"])
            cleaned["items"] = (
                {"type": "object", "additionalProperties": True}
                if item_type == "object"
                else {"type": item_type}
            )
        else:
            sample_list = None
            for candidate in (default_payload.get(prop_key), prop_meta.get("prefill"), prop_meta.get("default")):
                if isinstance(candidate, list) and len(candidate) > 0:
                    sample_list = candidate
                    break
            if sample_list:
                first_item = sample_list[0]
                if isinstance(first_item, dict):
                    cleaned["items"] = {"type": "object", "additionalProperties": True}
                elif isinstance(first_item, bool):
                    cleaned["items"] = {"type": "boolean"}
                elif isinstance(first_item, int):
                    cleaned["items"] = {"type": "integer"}
                elif isinstance(first_item, float):
                    cleaned["items"] = {"type": "number"}
                else:
                    cleaned["items"] = {"type": "string"}
            else:
                cleaned["items"] = {"type": "string"}
    elif raw_type == "object":
        cleaned["additionalProperties"] = True

    if "default" in prop_meta:
        cleaned["default"] = prop_meta["default"]
    if "enum" in prop_meta and isinstance(prop_meta["enum"], list) and prop_meta["enum"]:
        cleaned["enum"] = prop_meta["enum"]
    if "minimum" in prop_meta and isinstance(prop_meta["minimum"], (int, float)):
        cleaned["minimum"] = prop_meta["minimum"]
    if "maximum" in prop_meta and isinstance(prop_meta["maximum"], (int, float)):
        cleaned["maximum"] = prop_meta["maximum"]

    if prop_key in default_payload:
        cleaned["example"] = default_payload[prop_key]
    elif "prefill" in prop_meta and prop_meta["prefill"] is not None:
        cleaned["example"] = prop_meta["prefill"]
    elif "default" in prop_meta and prop_meta["default"] is not None:
        cleaned["example"] = prop_meta["default"]
    else:
        cleaned["example"] = (
            ""
            if raw_type == "string"
            else ([] if raw_type == "array" else ({} if raw_type == "object" else (False if raw_type == "boolean" else 0)))
        )

    return cleaned


def _extract_output_properties_and_example(
    slug: str,
    ds_schema: dict[str, Any],
    title: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """
    Extrai os campos de saída tanto de `fields.properties` quanto de `views.overview.display.properties`,
    garantindo que 100% das 31 especificações possuam schema de resposta rico e determinístico.
    """
    raw_fields = ds_schema.get("fields", {}).get("properties", {})
    view_props = (
        ds_schema.get("views", {})
        .get("overview", {})
        .get("display", {})
        .get("properties", {})
    )

    out_props: dict[str, Any] = {}
    sample_item: dict[str, Any] = {}

    if isinstance(raw_fields, dict) and raw_fields:
        for f_key, f_meta in raw_fields.items():
            if not isinstance(f_meta, dict):
                continue
            f_type = str(f_meta.get("type") or "string")
            if f_type not in ("string", "number", "integer", "boolean", "array", "object"):
                f_type = "string"
            f_title = str(f_meta.get("title") or f_key)
            f_desc = str(f_meta.get("description") or f_title)
            prop_spec: dict[str, Any] = {
                "type": f_type,
                "title": f_title,
                "description": f_desc,
            }
            if f_type == "array":
                prop_spec["items"] = {"type": "string"}
            elif f_type == "object":
                prop_spec["additionalProperties"] = True

            if f_type == "integer":
                ex_val: Any = 88
            elif f_type == "number":
                ex_val = 94.5
            elif f_type == "boolean":
                ex_val = True
            elif f_type == "array":
                ex_val = ["VERIFIED_PRIMARY_SOURCE"]
            elif f_type == "object":
                ex_val = {"source": "official_registry", "verified": True}
            else:
                ex_val = f"Verified {f_title} ({slug})"

            prop_spec["example"] = ex_val
            out_props[f_key] = prop_spec
            sample_item[f_key] = ex_val

    if not out_props and isinstance(view_props, dict) and view_props:
        for f_key, v_meta in view_props.items():
            v_dict = v_meta if isinstance(v_meta, dict) else {}
            fmt = str(v_dict.get("format") or "text")
            label = str(v_dict.get("label") or f_key)
            if fmt == "integer":
                f_type = "integer"
                ex_val = 10
            elif fmt == "number":
                f_type = "number"
                key_low = f_key.lower()
                ex_val = 92.0 if any(t in key_low for t in ("score", "pct", "percent", "rate", "confidence")) else 1250.00
            elif fmt == "boolean":
                f_type = "boolean"
                ex_val = True
            else:
                f_type = "string"
                ex_val = f"https://registry.gov.br/{slug}" if fmt == "link" else f"Verified {label}"

            out_props[f_key] = {
                "type": f_type,
                "title": label,
                "description": f"{label} extracted and validated by {title}.",
                "example": ex_val,
            }
            sample_item[f_key] = ex_val

    if "quantRiskScore" not in out_props and "viabilityScore" not in out_props:
        out_props["quantScore"] = {
            "type": "number",
            "title": "Quantitative Compliance & Opportunity Score (0-100)",
            "description": "Normalized deterministic score from 0 to 100 generated by the quantitative engine.",
            "example": 91.5,
        }
        sample_item["quantScore"] = 91.5

    if "ragMarkdownBrief" not in out_props:
        out_props["ragMarkdownBrief"] = {
            "type": "string",
            "title": "Executive RAG Markdown Brief",
            "description": "LLM-ready executive summary formatted in Markdown for RAG pipelines and compliance dossiers.",
            "example": f"### Executive Audit Brief — {title}\n- **Status:** VERIFIED\n- **Quantitative Score:** 91.5/100",
        }
        sample_item["ragMarkdownBrief"] = (
            f"### Executive Audit Brief — {title}\n- **Status:** VERIFIED\n- **Quantitative Score:** 91.5/100"
        )

    return out_props, sample_item


def build_code_snippets(slug: str, sample_input: dict[str, Any], gateway_url: str = DEFAULT_GATEWAY_BASE_URL) -> dict[str, str]:
    """
    Gera os 3 snippets prontos de integração comercial (`cURL`, `Python`, `Node.js`) para
    consumidores do RapidAPI Hub e do Zyla API Hub.
    """
    endpoint_url = f"{gateway_url.rstrip('/')}/v1/{slug}"
    rapidapi_host = f"{slug}.p.rapidapi.com"
    payload_compact = json.dumps(sample_input, ensure_ascii=False)
    payload_pretty = json.dumps(sample_input, indent=4, ensure_ascii=False)

    curl_snippet = (
        f'curl --request POST \\\n'
        f'  --url "{endpoint_url}" \\\n'
        f'  --header "Content-Type: application/json" \\\n'
        f'  --header "X-RapidAPI-Host: {rapidapi_host}" \\\n'
        f'  --header "X-RapidAPI-Key: <YOUR_RAPIDAPI_OR_ZYLA_KEY>" \\\n'
        f"  --data '{payload_compact}'"
    )

    python_snippet = (
        "import httpx\n\n"
        f'url = "{endpoint_url}"\n'
        f"payload = {payload_pretty}\n"
        "headers = {\n"
        '    "Content-Type": "application/json",\n'
        f'    "X-RapidAPI-Host": "{rapidapi_host}",\n'
        '    "X-RapidAPI-Key": "<YOUR_RAPIDAPI_OR_ZYLA_KEY>",\n'
        "}\n\n"
        "with httpx.Client(timeout=30.0) as client:\n"
        "    response = client.post(url, json=payload, headers=headers)\n"
        "    response.raise_for_status()\n"
        "    print(response.json())\n"
    )

    nodejs_snippet = (
        f'const url = "{endpoint_url}";\n'
        "const options = {\n"
        '  method: "POST",\n'
        "  headers: {\n"
        '    "Content-Type": "application/json",\n'
        f'    "X-RapidAPI-Host": "{rapidapi_host}",\n'
        '    "X-RapidAPI-Key": "<YOUR_RAPIDAPI_OR_ZYLA_KEY>"\n'
        "  },\n"
        f"  body: JSON.stringify({payload_compact})\n"
        "};\n\n"
        "const response = await fetch(url, options);\n"
        "const data = await response.json();\n"
        "console.log(data);\n"
    )

    return {
        "cURL": curl_snippet,
        "Python": python_snippet,
        "Node.js": nodejs_snippet,
    }


def build_Commercial_b2b_description(
    slug: str,
    title: str,
    base_description: str,
    taxonomy: dict[str, Any],
    monetization: dict[str, Any],
) -> str:
    """Constrói a descrição comercial em inglês otimizada para conversão B2B no RapidAPI e Zyla Hub."""
    buyer_persona = taxonomy.get("buyer_persona", "Enterprise Compliance, FinTech, SecOps, and RevOps Teams")
    rapid_cat = taxonomy.get("rapidapi_category", "Business")
    zyla_cat = taxonomy.get("zyla_category", "Company Data")
    seo_tags_str = ", ".join(taxonomy.get("seo_tags", [slug]))
    event_title = monetization.get("event_title", "Validated B2B Record")

    return (
        f"{base_description}\n\n"
        f"### Enterprise B2B Value Proposition ({title})\n"
        f"- **Target B2B Buyers:** {buyer_persona}.\n"
        f"- **Zero External API Keys Required:** Connects directly to authoritative government, regulatory, "
        f"and financial primary registries with built-in retry/backoff and deterministic schema normalization.\n"
        f"- **Quantitative Scoring & RAG Briefs:** Every record is enriched with a quantitative 0-100 risk/viability "
        f"score and an LLM-ready Markdown executive brief (`{event_title}`).\n"
        f"- **Marketplace Categories:** RapidAPI `{rapid_cat}` | Zyla API Hub `{zyla_cat}`.\n"
        f"- **Subscription Tiers (USD):** `BASIC` ($0.00/mo, 15 req/mo hard cap), `PRO` ($19.00/mo, 1,000 req/mo + $0.02/extra), "
        f"`ULTRA` ($49.00/mo, 5,000 req/mo + $0.015/extra), `MEGA` ($149.00/mo, 25,000 req/mo + $0.010/extra).\n"
        f"- **SEO Keywords:** {seo_tags_str}."
    )


def build_single_openapi_303_spec(
    slug: str,
    actors_dir: Path = ACTORS_DIR,
    gateway_url: str = DEFAULT_GATEWAY_BASE_URL,
) -> dict[str, Any]:
    """
    Constrói a especificação OpenAPI 3.0.3 individual para um único motor B2B, 100% compatível
    com o importador 1-Clique do RapidAPI Studio e do Zyla API Hub.
    """
    if slug not in ACTOR_SLUGS:
        raise KeyError(f"Slug B2B desconhecido: {slug}")

    meta = load_actor_metadata(slug, actors_dir=actors_dir)
    actor_info = meta["actor"]
    in_schema = meta["input_schema"]
    ds_schema = meta["dataset_schema"]
    mon = MONETIZATION_CONFIG.get(slug, {})
    taxonomy = MARKETPLACE_TAXONOMY.get(
        slug,
        {
            "rapidapi_category": "Business",
            "zyla_category": "Company Data",
            "seo_tags": [slug, "b2b-api", "compliance", "automation"],
            "buyer_persona": "Enterprise B2B Engineering & Compliance Teams",
        },
    )

    title = str(actor_info.get("title") or slug)
    base_desc = str(actor_info.get("description") or title)
    commercial_desc = build_Commercial_b2b_description(slug, title, base_desc, taxonomy, mon)

    in_props_raw = in_schema.get("properties", {})
    default_payload: dict[str, Any] = _build_canonical_request_example(slug, in_props_raw)
    cleaned_in_props: dict[str, Any] = {}
    for prop_k, prop_v in in_props_raw.items():
        if isinstance(prop_v, dict):
            cleaned_in_props[prop_k] = _clean_openapi_303_property(prop_k, prop_v, default_payload)

    required_in = [str(r) for r in in_schema.get("required", []) if r in cleaned_in_props]
    out_props, sample_output_item = _extract_output_properties_and_example(slug, ds_schema, title)
    snippets = build_code_snippets(slug, default_payload, gateway_url=gateway_url)

    model_prefix = "".join(part.capitalize() for part in slug.split("-"))
    input_schema_name = f"{model_prefix}Request"
    output_item_schema_name = f"{model_prefix}Record"
    response_envelope_name = f"{model_prefix}ResponseEnvelope"

    response_example = {
        "status": "succeeded",
        "actor": slug,
        "marketplace": "rapidapi_zyla_hub",
        "engineVersion": ENGINE_VERSION,
        "count": 1,
        "data": [sample_output_item],
    }

    seo_tags: list[str] = list(taxonomy.get("seo_tags", []))
    rapid_category = str(taxonomy.get("rapidapi_category", "Business"))
    zyla_category = str(taxonomy.get("zyla_category", "Company Data"))

    code_samples_list = [
        {"lang": "cURL", "label": "cURL", "source": snippets["cURL"]},
        {"lang": "Python", "label": "Python (httpx)", "source": snippets["Python"]},
        {"lang": "Node.js", "label": "Node.js (fetch)", "source": snippets["Node.js"]},
    ]

    spec: dict[str, Any] = {
        "openapi": "3.0.3",
        "info": {
            "title": title,
            "version": ENGINE_VERSION,
            "description": commercial_desc,
            "termsOfService": "https://jesleytassili-glitch.github.io/b2b-quant-mcp-n8n-suite/",
            "contact": {
                "name": "B2B Quant APIs (@b2b-quant-apis)",
                "email": "jesleytassili@gmail.com",
                "url": f"https://apify.com/{APIFY_USERNAME}/{slug}",
            },
            "license": {
                "name": "Commercial B2B API Subscription (RapidAPI & Zyla Hub)",
                "url": f"https://apify.com/{APIFY_USERNAME}/{slug}",
            },
            "x-category": rapid_category,
            "x-rapidapi-category": rapid_category,
            "x-zyla-category": zyla_category,
            "x-seo-tags": seo_tags,
            "x-payout-destination": f"Wise #{WISE_ACCOUNT_NUMBER}",
            "x-pricing-plans": STANDARD_PRICING_TIERS,
            "x-code-snippets": snippets,
            "x-openapi-spec-url": f"{PUBLIC_SPECS_BASE_URL}/{slug}.json",
            "x-openapi-suite-spec-url": f"{PUBLIC_SUITE_SPECS_BASE_URL}/{slug}.json",
            "x-apis-json-url": PUBLIC_APIS_JSON_URL,
            "x-github-release-tag": GITHUB_RELEASE_TAG,
        },
        "externalDocs": {
            "description": f"Official B2B Documentation & Schema Reference for {title}",
            "url": f"https://jesleytassili-glitch.github.io/b2b-quant-mcp-n8n-suite/actors/{slug}.html",
        },
        "servers": [
            {
                "url": gateway_url.rstrip("/"),
                "description": "Primary Anti-Bypass Stateless B2B Gateway (RapidAPI & Zyla Hub Proxy)",
            },
            {
                "url": "https://api.apify.com/v2",
                "description": "Direct Apify Cloud Synchronous Execution Cluster",
            },
        ],
        "tags": [
            {
                "name": rapid_category,
                "description": f"RapidAPI Hub primary category: {rapid_category} (Zyla Hub: {zyla_category})",
            },
            *[
                {"name": tag_str, "description": f"B2B SEO Search Tag: {tag_str}"}
                for tag_str in seo_tags
            ],
        ],
        "security": [
            {"RapidAPIProxySecret": []},
            {"ZylaProxySecret": []},
            {"RapidAPISubscriberKey": []},
        ],
        "paths": {
            f"/v1/{slug}": {
                "post": {
                    "operationId": f"execute_{slug.replace('-', '_')}",
                    "summary": f"Execute {title}",
                    "description": (
                        f"Synchronous stateless execution of **{title}**. "
                        f"Validates `X-RapidAPI-Proxy-Secret` / `X-Zyla-Proxy-Secret` in constant time (`hmac.compare_digest`), "
                        f"injects quota headers (`X-RateLimit-Remaining`, `X-Engine-Version`), and returns deterministic JSON records."
                    ),
                    "tags": [rapid_category, *seo_tags[:5]],
                    "x-codeSamples": code_samples_list,
                    "x-snippets": snippets,
                    "requestBody": {
                        "required": True,
                        "description": f"Structured JSON parameters for `{slug}`.",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": f"#/components/schemas/{input_schema_name}",
                                },
                                "example": default_payload,
                            }
                        },
                    },
                    "responses": {
                        "200": {
                            "description": f"Successful synchronous execution of `{slug}` returning enriched B2B JSON records.",
                            "headers": {
                                "X-RateLimit-Remaining": {
                                    "description": "Remaining requests in the subscriber's monthly plan quota (BASIC=15, PRO=1000, ULTRA=5000, MEGA=25000).",
                                    "schema": {"type": "integer", "example": 999},
                                },
                                "X-Engine-Version": {
                                    "description": "Deterministic B2B engine release version.",
                                    "schema": {"type": "string", "example": ENGINE_VERSION},
                                },
                            },
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": f"#/components/schemas/{response_envelope_name}",
                                    },
                                    "example": response_example,
                                }
                            },
                        },
                        "400": {
                            "description": "Bad Request — Invalid JSON payload or schema validation error.",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                                    "example": {
                                        "status": "error",
                                        "code": 400,
                                        "message": "Invalid JSON request body.",
                                    },
                                }
                            },
                        },
                        "403": {
                            "description": "Forbidden — Missing or invalid `X-RapidAPI-Proxy-Secret` / `X-Zyla-Proxy-Secret` header (Anti-Bypass Protection).",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                                    "example": {
                                        "status": "forbidden",
                                        "code": 403,
                                        "message": "Direct access denied. Requests must originate from RapidAPI Hub or Zyla API Hub with a valid Proxy-Secret.",
                                    },
                                }
                            },
                        },
                        "429": {
                            "description": "Too Many Requests — Monthly plan quota exceeded (e.g., BASIC Freemium 15 req/month hard limit).",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                                    "example": {
                                        "status": "quota_exceeded",
                                        "code": 429,
                                        "message": "Monthly request quota exceeded for BASIC plan (15 req/month hard limit). Upgrade to PRO ($19/mo), ULTRA ($49/mo), or MEGA ($149/mo).",
                                    },
                                }
                            },
                        },
                    },
                }
            },
            f"/v1/{slug}/health": {
                "get": {
                    "operationId": f"health_{slug.replace('-', '_')}",
                    "summary": f"Health & SLA Check for {title}",
                    "description": f"Lightweight health and schema readiness check for `{slug}` on RapidAPI Hub and Zyla API Hub.",
                    "tags": [rapid_category],
                    "responses": {
                        "200": {
                            "description": "Engine online and ready.",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "status": {"type": "string", "example": "ok"},
                                            "actor": {"type": "string", "example": slug},
                                            "engineVersion": {"type": "string", "example": ENGINE_VERSION},
                                            "category": {"type": "string", "example": rapid_category},
                                        },
                                    },
                                    "example": {
                                        "status": "ok",
                                        "actor": slug,
                                        "engineVersion": ENGINE_VERSION,
                                        "category": rapid_category,
                                    },
                                }
                            },
                        }
                    },
                }
            },
        },
        "components": {
            "securitySchemes": {
                "RapidAPIProxySecret": {
                    "type": "apiKey",
                    "in": "header",
                    "name": "X-RapidAPI-Proxy-Secret",
                    "description": "RapidAPI Hub shared proxy secret verified in constant time via hmac.compare_digest.",
                },
                "ZylaProxySecret": {
                    "type": "apiKey",
                    "in": "header",
                    "name": "X-Zyla-Proxy-Secret",
                    "description": "Zyla API Hub shared proxy secret verified in constant time via hmac.compare_digest.",
                },
                "RapidAPISubscriberKey": {
                    "type": "apiKey",
                    "in": "header",
                    "name": "X-RapidAPI-Key",
                    "description": "Subscriber API Key injected by RapidAPI Hub or Zyla API Hub.",
                },
            },
            "schemas": {
                input_schema_name: {
                    "type": "object",
                    "title": f"{title} Request Schema",
                    "description": str(in_schema.get("description") or f"Input parameters for {title}."),
                    "properties": cleaned_in_props,
                    **({"required": required_in} if required_in else {}),
                    "example": default_payload,
                },
                output_item_schema_name: {
                    "type": "object",
                    "title": f"{title} Output Record",
                    "description": f"Enriched B2B dataset item returned by `{slug}`.",
                    "properties": out_props,
                    "example": sample_output_item,
                },
                response_envelope_name: {
                    "type": "object",
                    "title": f"{title} Synchronous Response Envelope",
                    "required": ["status", "actor", "count", "data"],
                    "properties": {
                        "status": {"type": "string", "example": "succeeded"},
                        "actor": {"type": "string", "example": slug},
                        "marketplace": {"type": "string", "example": "rapidapi_zyla_hub"},
                        "engineVersion": {"type": "string", "example": ENGINE_VERSION},
                        "count": {"type": "integer", "example": 1},
                        "data": {
                            "type": "array",
                            "items": {"$ref": f"#/components/schemas/{output_item_schema_name}"},
                        },
                    },
                    "example": response_example,
                },
                "ErrorResponse": {
                    "type": "object",
                    "required": ["status", "code", "message"],
                    "properties": {
                        "status": {"type": "string", "example": "error"},
                        "code": {"type": "integer", "example": 403},
                        "message": {"type": "string", "example": "Direct access denied."},
                    },
                },
            },
        },
    }
    return spec


def build_apis_json_catalog(
    actors_dir: Path = ACTORS_DIR,
    origin_url: str = PUBLIC_GITHUB_PAGES_ORIGIN,
    gateway_url: str = DEFAULT_GATEWAY_BASE_URL,
) -> dict[str, Any]:
    """
    Constrói o catálogo padrão `apis.json` (`API Commons / APIs.guru specification`, `specificationVersion: "0.16"`)
    contendo todas as 31 APIs B2B com suas URLs públicas `OpenAPI 3.0.3` (`https://jesleytassili-glitch.github.io/specs_openapi_31/<slug>.json`).
    """
    clean_origin = origin_url.rstrip("/")
    clean_gw = gateway_url.rstrip("/")
    apis_entries: list[dict[str, Any]] = []

    for slug in ACTOR_SLUGS:
        meta = load_actor_metadata(slug, actors_dir=actors_dir)
        actor_info = meta["actor"]
        mon = MONETIZATION_CONFIG.get(slug, {})
        tax = MARKETPLACE_TAXONOMY.get(slug, {})
        title = str(actor_info.get("title") or slug)
        base_desc = str(actor_info.get("description") or title)
        seo_tags = list(tax.get("seo_tags", [slug, "b2b-api", "openapi"]))
        spec_public_url = f"{clean_origin}/specs_openapi_31/{slug}.json"
        spec_suite_url = f"{clean_origin}/b2b-quant-mcp-n8n-suite/specs_openapi_31/{slug}.json"
        human_doc_url = f"{clean_origin}/b2b-quant-mcp-n8n-suite/actors/{slug}.html"

        apis_entries.append(
            {
                "name": title,
                "slug": slug,
                "description": build_Commercial_b2b_description(slug, title, base_desc, tax, mon),
                "image": f"{clean_origin}/favicon.ico",
                "humanURL": human_doc_url,
                "baseURL": f"{clean_gw}/v1/{slug}",
                "version": ENGINE_VERSION,
                "tags": seo_tags,
                "properties": [
                    {"type": "OpenAPI", "url": spec_public_url},
                    {"type": "Swagger", "url": spec_public_url},
                    {"type": "OpenAPI-Mirror", "url": spec_suite_url},
                    {"type": "Documentation", "url": human_doc_url},
                    {"type": "Pricing", "url": f"{clean_origin}/pricing_plans_manifest.json"},
                    {"type": "X-RapidAPI-Category", "url": f"https://rapidapi.com/search/{slug}"},
                    {"type": "X-Zyla-Category", "url": f"https://zylalabs.com/api-marketplace/{slug}"},
                    {"type": "X-Apify-Actor", "url": f"https://apify.com/{APIFY_USERNAME}/{slug}"},
                    {"type": "X-MCP-Server", "url": f"https://mcp.apify.com/?actors={APIFY_USERNAME}/{slug}"},
                ],
                "contact": [
                    {
                        "FN": "B2B Quant APIs (@b2b-quant-apis)",
                        "email": "jesleytassili@gmail.com",
                        "url": f"https://apify.com/{APIFY_USERNAME}/{slug}",
                    }
                ],
            }
        )

    return {
        "name": "B2B Quant, Regulatory Compliance, FinTech & SecOps API Suite (@b2b-quant-apis)",
        "description": (
            "Production suite of 31 Stateless B2B Regulatory Compliance, KYB, Sanctions AML, GovCon "
            "(SAM.gov / EU TED / Brazil PNCP), SEC EDGAR, UK Companies House/FCA, US OSHA, SSL/TLS CT Attack Surface, "
            "Healthcare (ClinicalTrials.gov / OpenFDA / NPI / TISS), and Brazil Central Bank (BCB / PIX / CNPJ / IBGE / Tax Reform) "
            "OpenAPI 3.0.3 Engines settled in USD via RapidAPI Hub, Zyla API Hub, Postman Public API Network, and Wise #890361113."
        ),
        "url": f"{clean_origin}/apis.json",
        "image": f"{clean_origin}/favicon.ico",
        "specificationVersion": "0.16",
        "created": "2026-01-15",
        "modified": "2026-11-01",
        "tags": [
            "b2b-api",
            "openapi",
            "openapi3",
            "rapidapi",
            "zyla-hub",
            "postman",
            "apis-guru",
            "kyb",
            "compliance",
            "fintech",
            "secops",
            "healthcare",
            "govcon",
            "mcp",
            "x402",
        ],
        "maintainers": [
            {
                "FN": "Jesley Aguileira (@b2b-quant-apis)",
                "email": "jesleytassili@gmail.com",
                "url": f"https://apify.com/{APIFY_USERNAME}",
                "github": "https://github.com/jesleytassili-glitch/b2b-quant-mcp-n8n-suite",
                "payoutDestination": f"Wise #{WISE_ACCOUNT_NUMBER}",
            }
        ],
        "totalApis": len(apis_entries),
        "apis": apis_entries,
        "include": [],
    }


def generate_apis_json_catalog(
    output_path: Path = APIS_JSON_OUTPUT_PATH,
    actors_dir: Path = ACTORS_DIR,
    origin_url: str = PUBLIC_GITHUB_PAGES_ORIGIN,
    gateway_url: str = DEFAULT_GATEWAY_BASE_URL,
) -> Path:
    """Gera e salva o catálogo `apis.json` (`API Commons / APIs.guru`) em disco."""
    catalog = build_apis_json_catalog(
        actors_dir=actors_dir,
        origin_url=origin_url,
        gateway_url=gateway_url,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(catalog, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")
    return output_path


def build_postman_public_collection(
    actors_dir: Path = ACTORS_DIR,
    origin_url: str = PUBLIC_GITHUB_PAGES_ORIGIN,
    gateway_url: str = DEFAULT_GATEWAY_BASE_URL,
) -> dict[str, Any]:
    """
    Constrói a coleção Postman v2.1.0 (`postman_public_network_collection.json`) contendo as 31 APIs B2B
    prontas para importação 1-Clique na Postman Public API Network (`postman.com/explore`).
    """
    clean_origin = origin_url.rstrip("/")
    clean_gw = gateway_url.rstrip("/")
    folders: list[dict[str, Any]] = []

    for idx, slug in enumerate(ACTOR_SLUGS, start=1):
        meta = load_actor_metadata(slug, actors_dir=actors_dir)
        actor_info = meta["actor"]
        in_props_raw = meta["input_schema"].get("properties", {})
        sample_payload = _build_canonical_request_example(slug, in_props_raw)
        title = str(actor_info.get("title") or slug)
        tax = MARKETPLACE_TAXONOMY.get(slug, {})
        spec_url = f"{clean_origin}/specs_openapi_31/{slug}.json"

        folders.append(
            {
                "name": f"{idx:02d}. {title} ({slug})",
                "description": (
                    f"{actor_info.get('description', title)}\n\n"
                    f"- **Canonical OpenAPI 3.0.3 Spec URL:** `{spec_url}`\n"
                    f"- **RapidAPI Category:** `{tax.get('rapidapi_category', 'Business')}`\n"
                    f"- **Zyla Hub Category:** `{tax.get('zyla_category', 'Company Data')}`"
                ),
                "item": [
                    {
                        "name": f"POST /v1/{slug} — Execute {title}",
                        "request": {
                            "method": "POST",
                            "header": [
                                {"key": "Content-Type", "value": "application/json"},
                                {"key": "X-RapidAPI-Host", "value": f"{slug}.p.rapidapi.com"},
                                {"key": "X-RapidAPI-Key", "value": "{{RAPIDAPI_OR_ZYLA_KEY}}"},
                            ],
                            "body": {
                                "mode": "raw",
                                "raw": json.dumps(sample_payload, indent=2, ensure_ascii=False),
                                "options": {"raw": {"language": "json"}},
                            },
                            "url": {
                                "raw": f"{clean_gw}/v1/{slug}",
                                "protocol": "https",
                                "host": clean_gw.replace("https://", "").replace("http://", "").split("/")[0].split("."),
                                "path": ["v1", slug],
                            },
                            "description": f"Synchronous execution of `{slug}` (OpenAPI 3.0.3: {spec_url}).",
                        },
                    },
                    {
                        "name": f"GET /v1/{slug}/health — SLA Health Check",
                        "request": {
                            "method": "GET",
                            "header": [],
                            "url": {
                                "raw": f"{clean_gw}/v1/{slug}/health",
                                "protocol": "https",
                                "host": clean_gw.replace("https://", "").replace("http://", "").split("/")[0].split("."),
                                "path": ["v1", slug, "health"],
                            },
                            "description": f"Health and readiness probe for `{slug}`.",
                        },
                    },
                ],
            }
        )

    return {
        "info": {
            "_postman_id": "b2b-quant-31-openapi-303-suite-v3",
            "name": "B2B Quant, Regulatory Compliance & FinTech Suite (31 OpenAPI 3.0.3 APIs)",
            "version": ENGINE_VERSION,
            "description": (
                "Official Postman Public API Network Collection for 31 Stateless B2B Regulatory Compliance, "
                "KYB, FinTech, SecOps, GovCon, and Healthcare APIs (@b2b-quant-apis). "
                f"All 31 individual OpenAPI 3.0.3 specifications are hosted at `{clean_origin}/specs_openapi_31/<slug>.json` "
                f"and indexed in `{clean_origin}/apis.json`."
            ),
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        },
        "variable": [
            {"key": "GATEWAY_BASE_URL", "value": clean_gw, "type": "string"},
            {"key": "RAPIDAPI_OR_ZYLA_KEY", "value": "<YOUR_RAPIDAPI_OR_ZYLA_SUBSCRIBER_KEY>", "type": "string"},
            {"key": "OPENAPI_SPECS_ORIGIN", "value": f"{clean_origin}/specs_openapi_31", "type": "string"},
        ],
        "item": folders,
    }


def generate_postman_public_collection(
    output_path: Path = POSTMAN_COLLECTION_OUTPUT_PATH,
    actors_dir: Path = ACTORS_DIR,
    origin_url: str = PUBLIC_GITHUB_PAGES_ORIGIN,
    gateway_url: str = DEFAULT_GATEWAY_BASE_URL,
) -> Path:
    """Gera e salva a coleção `postman_public_network_collection.json` em disco."""
    col = build_postman_public_collection(
        actors_dir=actors_dir,
        origin_url=origin_url,
        gateway_url=gateway_url,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(col, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")
    return output_path


def generate_all_31_openapi_specs(
    output_dir: Path = SPECS_OUTPUT_DIR,
    actors_dir: Path = ACTORS_DIR,
    gateway_url: str = DEFAULT_GATEWAY_BASE_URL,
) -> list[Path]:
    """
    Gera e salva os 31 arquivos JSON OpenAPI 3.0.3 individuais em `specs_openapi_31/<slug>.json`,
    além de atualizar `apis.json` (`API Commons / APIs.guru`) e `postman_public_network_collection.json`.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    generated_files: list[Path] = []

    for slug in ACTOR_SLUGS:
        spec = build_single_openapi_303_spec(slug, actors_dir=actors_dir, gateway_url=gateway_url)
        spec_file = output_dir / f"{slug}.json"
        spec_file.write_text(json.dumps(spec, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")
        generated_files.append(spec_file)

    generate_apis_json_catalog(
        output_path=APIS_JSON_OUTPUT_PATH,
        actors_dir=actors_dir,
        gateway_url=gateway_url,
    )
    generate_postman_public_collection(
        output_path=POSTMAN_COLLECTION_OUTPUT_PATH,
        actors_dir=actors_dir,
        gateway_url=gateway_url,
    )

    logger.info(
        "31/31 especificações OpenAPI 3.0.3 individuais + apis.json + Postman Collection geradas em: %s",
        output_dir,
    )
    return generated_files


if __name__ == "__main__":
    generate_all_31_openapi_specs()

