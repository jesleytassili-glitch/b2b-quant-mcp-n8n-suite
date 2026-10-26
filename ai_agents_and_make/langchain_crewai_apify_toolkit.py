"""
Plug-and-Play Python SDK / LangChain / CrewAI Toolkit for @b2b-quant-apis (15 B2B Apify Actors).
Every call executes via the client's APIFY_API_TOKEN and triggers Pay-Per-Event billing on Apify Store.
"""

import os
from typing import Any, Dict, List, Optional
import httpx

APIFY_USERNAME = "b2b-quant-apis"
AVAILABLE_ACTORS: List[str] = [
    "b2b-gov-procurement-pncp-radar",
    "brazil-antt-freight-cte-auditor",
    "brazil-b2b-cnpj-qsa-lead-enricher",
    "brazil-bcb-ptax-sgs-financial-contract-indexer",
    "brazil-camara-legislative-regulatory-risk-radar",
    "brazil-cep-geocoordinates-logistics-auditor",
    "brazil-ibge-cnae-municipal-b2b-expansion-enricher",
    "brazil-pix-ispb-cvm-financial-kyb-auditor",
    "brazil-tax-reform-ncm-classtrib-auditor",
    "cisa-kev-ransomware-vulnerability-auditor",
    "eu-vies-vat-tax-compliance-auditor",
    "global-b2b-email-domain-security-auditor",
    "global-gleif-lei-corporate-ownership-kyb",
    "healthcare-tiss-xml-validator",
    "icann-rdap-domain-whois-brand-recon",
    "multi-ats-tech-job-board-hiring-radar",
    "us-census-fcc-real-estate-geo-enricher",
    "us-clinical-trials-biotech-radar",
    "us-epa-echo-environmental-compliance-auditor",
    "us-fda-recalls-safety-monitor",
    "us-fdic-bankfind-institution-financial-auditor",
    "us-healthcare-npi-provider-lead-enricher",
    "us-nhtsa-vehicle-vin-recall-auditor",
    "us-sam-gov-federal-procurement-auditor",
    "us-sec-edgar-filings-insider-radar"
]


def run_b2b_actor_sync(
    actor_slug: str,
    payload: Dict[str, Any],
    apify_token: Optional[str] = None,
    timeout_seconds: float = 300.0,
) -> List[Dict[str, Any]]:
    """
    Executes a @b2b-quant-apis Actor synchronously and returns the structured JSON dataset items.
    """
    if actor_slug not in AVAILABLE_ACTORS:
        raise ValueError(f"Unknown actor_slug '{actor_slug}'. Valid options: {AVAILABLE_ACTORS}")
    token = apify_token or os.environ.get("APIFY_API_TOKEN", "")
    if not token:
        raise RuntimeError("Missing APIFY_API_TOKEN environment variable or apify_token argument.")

    url = f"https://api.apify.com/v2/acts/{APIFY_USERNAME}~{actor_slug}/run-sync-get-dataset-items"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    with httpx.Client(timeout=timeout_seconds, follow_redirects=True) as client:
        response = client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        return data if isinstance(data, list) else [data]
