# B2B Quant, Regulatory Compliance & Lead Intelligence Suite (`MCP Servers` + `n8n Workflows` + `OpenAPI 3.1`)

[![Apify Store Publisher](https://img.shields.io/badge/Apify_Store-%40b2b--quant--apis-00C853?style=for-the-badge&logo=apify)](https://apify.com/b2b-quant-apis)
[![Model Context Protocol](https://img.shields.io/badge/MCP-20_Live_Servers-6366F1?style=for-the-badge)](https://mcp.apify.com/?actors=b2b-quant-apis/b2b-gov-procurement-pncp-radar,b2b-quant-apis/brazil-tax-reform-ncm-classtrib-auditor,b2b-quant-apis/healthcare-tiss-xml-validator,b2b-quant-apis/brazil-antt-freight-cte-auditor,b2b-quant-apis/us-healthcare-npi-provider-lead-enricher,b2b-quant-apis/us-fda-recalls-safety-monitor,b2b-quant-apis/global-b2b-email-domain-security-auditor,b2b-quant-apis/us-clinical-trials-biotech-radar,b2b-quant-apis/us-nhtsa-vehicle-vin-recall-auditor,b2b-quant-apis/brazil-b2b-cnpj-qsa-lead-enricher,b2b-quant-apis/us-sec-edgar-filings-insider-radar,b2b-quant-apis/eu-vies-vat-tax-compliance-auditor,b2b-quant-apis/us-epa-echo-environmental-compliance-auditor,b2b-quant-apis/us-fdic-bankfind-institution-financial-auditor,b2b-quant-apis/us-sam-gov-federal-procurement-auditor,b2b-quant-apis/multi-ats-tech-job-board-hiring-radar,b2b-quant-apis/global-gleif-lei-corporate-ownership-kyb,b2b-quant-apis/us-census-fcc-real-estate-geo-enricher,b2b-quant-apis/icann-rdap-domain-whois-brand-recon,b2b-quant-apis/cisa-kev-ransomware-vulnerability-auditor,b2b-quant-apis/brazil-bcb-ptax-sgs-financial-contract-indexer,b2b-quant-apis/brazil-pix-ispb-cvm-financial-kyb-auditor,b2b-quant-apis/brazil-ibge-cnae-municipal-b2b-expansion-enricher,b2b-quant-apis/brazil-cep-geocoordinates-logistics-auditor,b2b-quant-apis/brazil-camara-legislative-regulatory-risk-radar)
[![n8n Workflows](https://img.shields.io/badge/n8n-24_Ready_Workflows-FF6D5A?style=for-the-badge&logo=n8n)](./n8n_super_pipelines/)
[![OpenAPI 3.1](https://img.shields.io/badge/OpenAPI-3.1.0_Spec-85EA2D?style=for-the-badge&logo=openapiinitiative)](./openapi_rapidapi_3_1.json)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge)](./LICENSE)

Production-grade suite of **20 Stateless B2B Intelligence, KYB Compliance, GovCon, Healthcare, FinTech, Real Estate, Cybersecurity, and Tax Audit Engines** hosted on **[Apify Store (`@b2b-quant-apis`)](https://apify.com/b2b-quant-apis)**.

Designed for **Machine-to-Machine (M2M) scheduled pipelines** and **Autonomous AI Agents**:
- **20 MCP Servers** ready for **Claude Desktop**, **Cursor IDE**, **Windsurf**, **Smithery**, and **Glama.ai**;
- **4 Multi-Actor Enterprise Waterfall Pipelines (`.n8n.json`)** + **20 Daily Scheduled n8n Templates**;
- **OpenAPI 3.1.0 Specification (`openapi_rapidapi_3_1.json`)** for 1-click import into **RapidAPI**, **Custom GPT Actions**, and enterprise API gateways;
- **Python LangChain / CrewAI SDK (`ai_agents_and_make/langchain_crewai_apify_toolkit.py`)** and **Make.com Blueprint**.

---

## Quick Start: 1-Click MCP Server Setup (Claude Desktop / Cursor IDE)

Add the entire 20-tool B2B intelligence suite to **Claude Desktop** (`claude_desktop_config.json`) or **Cursor IDE** (`.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "b2b-quant-apis-full-suite": {
      "command": "npx",
      "args": [
        "-y",
        "@apify/actors-mcp-server",
        "--actors",
        "b2b-quant-apis/b2b-gov-procurement-pncp-radar,b2b-quant-apis/brazil-tax-reform-ncm-classtrib-auditor,b2b-quant-apis/healthcare-tiss-xml-validator,b2b-quant-apis/brazil-antt-freight-cte-auditor,b2b-quant-apis/us-healthcare-npi-provider-lead-enricher,b2b-quant-apis/us-fda-recalls-safety-monitor,b2b-quant-apis/global-b2b-email-domain-security-auditor,b2b-quant-apis/us-clinical-trials-biotech-radar,b2b-quant-apis/us-nhtsa-vehicle-vin-recall-auditor,b2b-quant-apis/brazil-b2b-cnpj-qsa-lead-enricher,b2b-quant-apis/us-sec-edgar-filings-insider-radar,b2b-quant-apis/eu-vies-vat-tax-compliance-auditor,b2b-quant-apis/us-epa-echo-environmental-compliance-auditor,b2b-quant-apis/us-fdic-bankfind-institution-financial-auditor,b2b-quant-apis/us-sam-gov-federal-procurement-auditor,b2b-quant-apis/multi-ats-tech-job-board-hiring-radar,b2b-quant-apis/global-gleif-lei-corporate-ownership-kyb,b2b-quant-apis/us-census-fcc-real-estate-geo-enricher,b2b-quant-apis/icann-rdap-domain-whois-brand-recon,b2b-quant-apis/cisa-kev-ransomware-vulnerability-auditor,b2b-quant-apis/brazil-bcb-ptax-sgs-financial-contract-indexer,b2b-quant-apis/brazil-pix-ispb-cvm-financial-kyb-auditor,b2b-quant-apis/brazil-ibge-cnae-municipal-b2b-expansion-enricher,b2b-quant-apis/brazil-cep-geocoordinates-logistics-auditor,b2b-quant-apis/brazil-camara-legislative-regulatory-risk-radar"
      ],
      "env": {
        "APIFY_TOKEN": "<YOUR_APIFY_TOKEN_HERE>"
      }
    }
  }
}
```

> **Streamable HTTP / SSE MCP Endpoint (Zero Local Install):**
> `https://mcp.apify.com/?actors=b2b-quant-apis/b2b-gov-procurement-pncp-radar,b2b-quant-apis/brazil-tax-reform-ncm-classtrib-auditor,b2b-quant-apis/healthcare-tiss-xml-validator,b2b-quant-apis/brazil-antt-freight-cte-auditor,b2b-quant-apis/us-healthcare-npi-provider-lead-enricher,b2b-quant-apis/us-fda-recalls-safety-monitor,b2b-quant-apis/global-b2b-email-domain-security-auditor,b2b-quant-apis/us-clinical-trials-biotech-radar,b2b-quant-apis/us-nhtsa-vehicle-vin-recall-auditor,b2b-quant-apis/brazil-b2b-cnpj-qsa-lead-enricher,b2b-quant-apis/us-sec-edgar-filings-insider-radar,b2b-quant-apis/eu-vies-vat-tax-compliance-auditor,b2b-quant-apis/us-epa-echo-environmental-compliance-auditor,b2b-quant-apis/us-fdic-bankfind-institution-financial-auditor,b2b-quant-apis/us-sam-gov-federal-procurement-auditor,b2b-quant-apis/multi-ats-tech-job-board-hiring-radar,b2b-quant-apis/global-gleif-lei-corporate-ownership-kyb,b2b-quant-apis/us-census-fcc-real-estate-geo-enricher,b2b-quant-apis/icann-rdap-domain-whois-brand-recon,b2b-quant-apis/cisa-kev-ransomware-vulnerability-auditor,b2b-quant-apis/brazil-bcb-ptax-sgs-financial-contract-indexer,b2b-quant-apis/brazil-pix-ispb-cvm-financial-kyb-auditor,b2b-quant-apis/brazil-ibge-cnae-municipal-b2b-expansion-enricher,b2b-quant-apis/brazil-cep-geocoordinates-logistics-auditor,b2b-quant-apis/brazil-camara-legislative-regulatory-risk-radar`

---

## Enterprise Multi-Actor Waterfall Pipelines (`n8n_super_pipelines/`)

Import these ready-to-run `.n8n.json` workflows directly into your self-hosted or cloud **n8n** instance:

| # | Enterprise Waterfall Pipeline | Cascaded Apify Actors (`@b2b-quant-apis`) | Schedule | Download JSON |
| :-: | :--- | :--- | :---: | :---: |
| **01** | **Global Vendor KYB, SEC EDGAR, FDIC, EU VAT, EPA & Brazil CNPJ Waterfall** | `us-sec-edgar-filings-insider-radar` → `us-epa-echo-environmental-compliance-auditor` → `us-fdic-bankfind-institution-financial-auditor` → `eu-vies-vat-tax-compliance-auditor` → `brazil-b2b-cnpj-qsa-lead-enricher` | `0 6 * * 1-5` | [`01_global_vendor_kyb_compliance_waterfall.n8n.json`](./n8n_super_pipelines/01_global_vendor_kyb_compliance_waterfall.n8n.json) |
| **02** | **US Federal GovCon (SAM.gov) Daily B2B Lead Scraper + SEC & EPA Due Diligence** | `us-sam-gov-federal-procurement-auditor` → `us-sec-edgar-filings-insider-radar` → `us-epa-echo-environmental-compliance-auditor` | `0 7 * * *` | [`02_us_federal_govcon_lead_enrichment_daily.n8n.json`](./n8n_super_pipelines/02_us_federal_govcon_lead_enrichment_daily.n8n.json) |
| **03** | **Pharma & Biotech Clinical Trials, OpenFDA Recalls & NPI Provider Lead Radar** | `us-clinical-trials-biotech-radar` → `us-fda-recalls-safety-monitor` → `us-healthcare-npi-provider-lead-enricher` | `30 7 * * *` | [`03_pharma_biotech_patent_clinical_radar.n8n.json`](./n8n_super_pipelines/03_pharma_biotech_patent_clinical_radar.n8n.json) |
| **04** | **B2B Outbound Hiring Intent, GLEIF Corporate KYB, ICANN RDAP & CISA KEV Cyber Waterfall** | `multi-ats-tech-job-board-hiring-radar` → `global-gleif-lei-corporate-ownership-kyb` → `icann-rdap-domain-whois-brand-recon` → `cisa-kev-ransomware-vulnerability-auditor` | `0 8 * * 1-5` | [`04_b2b_outbound_hiring_intent_gleif_rdap_cyber_waterfall.n8n.json`](./n8n_super_pipelines/04_b2b_outbound_hiring_intent_gleif_rdap_cyber_waterfall.n8n.json) |

---

## Complete Catalog: 20 B2B Apify Actors & MCP Servers

| # | Actor Slug & Title | Pay-Per-Event (USD) | MCP Server URL | n8n Template |
| :-: | :--- | :---: | :---: | :---: |
| 01 | **[`b2b-gov-procurement-pncp-radar`](https://apify.com/b2b-quant-apis/b2b-gov-procurement-pncp-radar)**<br>_Brazil Gov Procurement & Bidding Radar (PNCP API + MCP Server)_ | `tender-analyzed` (`$0.03` USD) | [Streamable MCP](https://mcp.apify.com/?actors=b2b-quant-apis/b2b-gov-procurement-pncp-radar) | [`b2b-gov-procurement-pncp-radar.n8n.json`](n8n_creator_hub_templates/b2b-gov-procurement-pncp-radar.n8n.json) |
| 02 | **[`brazil-tax-reform-ncm-classtrib-auditor`](https://apify.com/b2b-quant-apis/brazil-tax-reform-ncm-classtrib-auditor)**<br>_Brazil Tax Reform 2026: NCM to cClassTrib & NF-e Auditor_ | `tax-item-audited` (`$0.01` USD) | [Streamable MCP](https://mcp.apify.com/?actors=b2b-quant-apis/brazil-tax-reform-ncm-classtrib-auditor) | [`brazil-tax-reform-ncm-classtrib-auditor.n8n.json`](n8n_creator_hub_templates/brazil-tax-reform-ncm-classtrib-auditor.n8n.json) |
| 03 | **[`healthcare-tiss-xml-validator`](https://apify.com/b2b-quant-apis/healthcare-tiss-xml-validator)**<br>_Brazil Healthcare TISS 4.03.00 XML Validator & Hash Fixer_ | `tiss-lot-validated` (`$0.05` USD) | [Streamable MCP](https://mcp.apify.com/?actors=b2b-quant-apis/healthcare-tiss-xml-validator) | [`healthcare-tiss-xml-validator.n8n.json`](n8n_creator_hub_templates/healthcare-tiss-xml-validator.n8n.json) |
| 04 | **[`brazil-antt-freight-cte-auditor`](https://apify.com/b2b-quant-apis/brazil-antt-freight-cte-auditor)**<br>_Brazil ANTT Minimum Freight Calculator & CT-e XML Batch Auditor_ | `freight-audit-completed` (`$0.02` USD) | [Streamable MCP](https://mcp.apify.com/?actors=b2b-quant-apis/brazil-antt-freight-cte-auditor) | [`brazil-antt-freight-cte-auditor.n8n.json`](n8n_creator_hub_templates/brazil-antt-freight-cte-auditor.n8n.json) |
| 05 | **[`us-healthcare-npi-provider-lead-enricher`](https://apify.com/b2b-quant-apis/us-healthcare-npi-provider-lead-enricher)**<br>_US Healthcare NPI Doctor & Clinic Lead Enricher (CMS API)_ | `npi-lead-enriched` (`$0.02` USD) | [Streamable MCP](https://mcp.apify.com/?actors=b2b-quant-apis/us-healthcare-npi-provider-lead-enricher) | [`us-healthcare-npi-provider-lead-enricher.n8n.json`](n8n_creator_hub_templates/us-healthcare-npi-provider-lead-enricher.n8n.json) |
| 06 | **[`us-fda-recalls-safety-monitor`](https://apify.com/b2b-quant-apis/us-fda-recalls-safety-monitor)**<br>_US FDA Recalls & Safety Monitor (Food, Drug & Devices)_ | `fda-recall-extracted` (`$0.03` USD) | [Streamable MCP](https://mcp.apify.com/?actors=b2b-quant-apis/us-fda-recalls-safety-monitor) | [`us-fda-recalls-safety-monitor.n8n.json`](n8n_creator_hub_templates/us-fda-recalls-safety-monitor.n8n.json) |
| 07 | **[`global-b2b-email-domain-security-auditor`](https://apify.com/b2b-quant-apis/global-b2b-email-domain-security-auditor)**<br>_Global B2B Email, MX, SPF & DMARC Deliverability Auditor_ | `domain-email-audited` (`$0.005` USD) | [Streamable MCP](https://mcp.apify.com/?actors=b2b-quant-apis/global-b2b-email-domain-security-auditor) | [`global-b2b-email-domain-security-auditor.n8n.json`](n8n_creator_hub_templates/global-b2b-email-domain-security-auditor.n8n.json) |
| 08 | **[`us-clinical-trials-biotech-radar`](https://apify.com/b2b-quant-apis/us-clinical-trials-biotech-radar)**<br>_US ClinicalTrials.gov Biotech & Pharma Study Radar_ | `clinical-trial-extracted` (`$0.04` USD) | [Streamable MCP](https://mcp.apify.com/?actors=b2b-quant-apis/us-clinical-trials-biotech-radar) | [`us-clinical-trials-biotech-radar.n8n.json`](n8n_creator_hub_templates/us-clinical-trials-biotech-radar.n8n.json) |
| 09 | **[`us-nhtsa-vehicle-vin-recall-auditor`](https://apify.com/b2b-quant-apis/us-nhtsa-vehicle-vin-recall-auditor)**<br>_US NHTSA Vehicle VIN Decoder & Safety Recall Auditor_ | `vin-decoded-audited` (`$0.02` USD) | [Streamable MCP](https://mcp.apify.com/?actors=b2b-quant-apis/us-nhtsa-vehicle-vin-recall-auditor) | [`us-nhtsa-vehicle-vin-recall-auditor.n8n.json`](n8n_creator_hub_templates/us-nhtsa-vehicle-vin-recall-auditor.n8n.json) |
| 10 | **[`brazil-b2b-cnpj-qsa-lead-enricher`](https://apify.com/b2b-quant-apis/brazil-b2b-cnpj-qsa-lead-enricher)**<br>_Brazil B2B CNPJ, Partners (QSA) & CNAE Lead Enricher_ | `cnpj-lead-enriched` (`$0.015` USD) | [Streamable MCP](https://mcp.apify.com/?actors=b2b-quant-apis/brazil-b2b-cnpj-qsa-lead-enricher) | [`brazil-b2b-cnpj-qsa-lead-enricher.n8n.json`](n8n_creator_hub_templates/brazil-b2b-cnpj-qsa-lead-enricher.n8n.json) |
| 11 | **[`us-sec-edgar-filings-insider-radar`](https://apify.com/b2b-quant-apis/us-sec-edgar-filings-insider-radar)**<br>_US SEC EDGAR Filings & Insider Trading Radar (10-K/8-K/Form 4)_ | `sec-filing-analyzed` (`$0.04` USD) | [Streamable MCP](https://mcp.apify.com/?actors=b2b-quant-apis/us-sec-edgar-filings-insider-radar) | [`us-sec-edgar-filings-insider-radar.n8n.json`](n8n_creator_hub_templates/us-sec-edgar-filings-insider-radar.n8n.json) |
| 12 | **[`eu-vies-vat-tax-compliance-auditor`](https://apify.com/b2b-quant-apis/eu-vies-vat-tax-compliance-auditor)**<br>_EU VIES VAT Number Validator & Reverse Charge Tax Auditor_ | `eu-vat-audited` (`$0.015` USD) | [Streamable MCP](https://mcp.apify.com/?actors=b2b-quant-apis/eu-vies-vat-tax-compliance-auditor) | [`eu-vies-vat-tax-compliance-auditor.n8n.json`](n8n_creator_hub_templates/eu-vies-vat-tax-compliance-auditor.n8n.json) |
| 13 | **[`us-epa-echo-environmental-compliance-auditor`](https://apify.com/b2b-quant-apis/us-epa-echo-environmental-compliance-auditor)**<br>_US EPA ECHO Environmental Compliance & ESG Penalty Auditor_ | `epa-facility-audited` (`$0.03` USD) | [Streamable MCP](https://mcp.apify.com/?actors=b2b-quant-apis/us-epa-echo-environmental-compliance-auditor) | [`us-epa-echo-environmental-compliance-auditor.n8n.json`](n8n_creator_hub_templates/us-epa-echo-environmental-compliance-auditor.n8n.json) |
| 14 | **[`us-fdic-bankfind-institution-financial-auditor`](https://apify.com/b2b-quant-apis/us-fdic-bankfind-institution-financial-auditor)**<br>_US FDIC BankFind Institution & Solvency Risk Auditor_ | `fdic-bank-audited` (`$0.025` USD) | [Streamable MCP](https://mcp.apify.com/?actors=b2b-quant-apis/us-fdic-bankfind-institution-financial-auditor) | [`us-fdic-bankfind-institution-financial-auditor.n8n.json`](n8n_creator_hub_templates/us-fdic-bankfind-institution-financial-auditor.n8n.json) |
| 15 | **[`us-sam-gov-federal-procurement-auditor`](https://apify.com/b2b-quant-apis/us-sam-gov-federal-procurement-auditor)**<br>_US Federal Contracts & SAM.gov Procurement B2G Radar_ | `federal-contract-audited` (`$0.035` USD) | [Streamable MCP](https://mcp.apify.com/?actors=b2b-quant-apis/us-sam-gov-federal-procurement-auditor) | [`us-sam-gov-federal-procurement-auditor.n8n.json`](n8n_creator_hub_templates/us-sam-gov-federal-procurement-auditor.n8n.json) |
| 16 | **[`multi-ats-tech-job-board-hiring-radar`](https://apify.com/b2b-quant-apis/multi-ats-tech-job-board-hiring-radar)**<br>_Multi-ATS Tech Job Board & B2B Hiring Intent Signal Radar_ | `job-signal-extracted` (`$0.02` USD) | [Streamable MCP](https://mcp.apify.com/?actors=b2b-quant-apis/multi-ats-tech-job-board-hiring-radar) | [`multi-ats-tech-job-board-hiring-radar.n8n.json`](n8n_creator_hub_templates/multi-ats-tech-job-board-hiring-radar.n8n.json) |
| 17 | **[`global-gleif-lei-corporate-ownership-kyb`](https://apify.com/b2b-quant-apis/global-gleif-lei-corporate-ownership-kyb)**<br>_Global GLEIF LEI Corporate Ownership & KYB Compliance Auditor_ | `corporate-entity-audited` (`$0.025` USD) | [Streamable MCP](https://mcp.apify.com/?actors=b2b-quant-apis/global-gleif-lei-corporate-ownership-kyb) | [`global-gleif-lei-corporate-ownership-kyb.n8n.json`](n8n_creator_hub_templates/global-gleif-lei-corporate-ownership-kyb.n8n.json) |
| 18 | **[`us-census-fcc-real-estate-geo-enricher`](https://apify.com/b2b-quant-apis/us-census-fcc-real-estate-geo-enricher)**<br>_US Real Estate Census Tract, FIPS & PropTech Geo Enricher_ | `property-geo-enriched` (`$0.02` USD) | [Streamable MCP](https://mcp.apify.com/?actors=b2b-quant-apis/us-census-fcc-real-estate-geo-enricher) | [`us-census-fcc-real-estate-geo-enricher.n8n.json`](n8n_creator_hub_templates/us-census-fcc-real-estate-geo-enricher.n8n.json) |
| 19 | **[`icann-rdap-domain-whois-brand-recon`](https://apify.com/b2b-quant-apis/icann-rdap-domain-whois-brand-recon)**<br>_ICANN RDAP Official Domain WHOIS, Brand & Antifraud Auditor_ | `domain-whois-audited` (`$0.015` USD) | [Streamable MCP](https://mcp.apify.com/?actors=b2b-quant-apis/icann-rdap-domain-whois-brand-recon) | [`icann-rdap-domain-whois-brand-recon.n8n.json`](n8n_creator_hub_templates/icann-rdap-domain-whois-brand-recon.n8n.json) |
| 20 | **[`cisa-kev-ransomware-vulnerability-auditor`](https://apify.com/b2b-quant-apis/cisa-kev-ransomware-vulnerability-auditor)**<br>_US CISA KEV Exploited Vulnerabilities & Ransomware Threat Radar_ | `cve-vulnerability-audited` (`$0.02` USD) | [Streamable MCP](https://mcp.apify.com/?actors=b2b-quant-apis/cisa-kev-ransomware-vulnerability-auditor) | [`cisa-kev-ransomware-vulnerability-auditor.n8n.json`](n8n_creator_hub_templates/cisa-kev-ransomware-vulnerability-auditor.n8n.json) |
| 21 | **[`brazil-bcb-ptax-sgs-financial-contract-indexer`](https://apify.com/b2b-quant-apis/brazil-bcb-ptax-sgs-financial-contract-indexer)**<br>_Brazil Central Bank PTAX, Selic, CDI & IPCA Contract Indexer_ | `contract-index-calculated` (`$0.015` USD) | [Streamable MCP](https://mcp.apify.com/?actors=b2b-quant-apis/brazil-bcb-ptax-sgs-financial-contract-indexer) | [`brazil-bcb-ptax-sgs-financial-contract-indexer.n8n.json`](n8n_creator_hub_templates/brazil-bcb-ptax-sgs-financial-contract-indexer.n8n.json) |
| 22 | **[`brazil-pix-ispb-cvm-financial-kyb-auditor`](https://apify.com/b2b-quant-apis/brazil-pix-ispb-cvm-financial-kyb-auditor)**<br>_Brazil Pix ISPB, COMPE & CVM Financial Institution KYB Auditor_ | `financial-institution-audited` (`$0.02` USD) | [Streamable MCP](https://mcp.apify.com/?actors=b2b-quant-apis/brazil-pix-ispb-cvm-financial-kyb-auditor) | [`brazil-pix-ispb-cvm-financial-kyb-auditor.n8n.json`](n8n_creator_hub_templates/brazil-pix-ispb-cvm-financial-kyb-auditor.n8n.json) |
| 23 | **[`brazil-ibge-cnae-municipal-b2b-expansion-enricher`](https://apify.com/b2b-quant-apis/brazil-ibge-cnae-municipal-b2b-expansion-enricher)**<br>_Brazil IBGE CNAE 2.3 & Municipal Code B2B Tax Enricher_ | `cnae-municipality-enriched` (`$0.015` USD) | [Streamable MCP](https://mcp.apify.com/?actors=b2b-quant-apis/brazil-ibge-cnae-municipal-b2b-expansion-enricher) | [`brazil-ibge-cnae-municipal-b2b-expansion-enricher.n8n.json`](n8n_creator_hub_templates/brazil-ibge-cnae-municipal-b2b-expansion-enricher.n8n.json) |
| 24 | **[`brazil-cep-geocoordinates-logistics-auditor`](https://apify.com/b2b-quant-apis/brazil-cep-geocoordinates-logistics-auditor)**<br>_Brazil CEP Geocoordinates, IBGE Code & Logistics Auditor_ | `cep-geo-audited` (`$0.01` USD) | [Streamable MCP](https://mcp.apify.com/?actors=b2b-quant-apis/brazil-cep-geocoordinates-logistics-auditor) | [`brazil-cep-geocoordinates-logistics-auditor.n8n.json`](n8n_creator_hub_templates/brazil-cep-geocoordinates-logistics-auditor.n8n.json) |
| 25 | **[`brazil-camara-legislative-regulatory-risk-radar`](https://apify.com/b2b-quant-apis/brazil-camara-legislative-regulatory-risk-radar)**<br>_Brazil Congress Legislative Bills & Tax Regulatory Risk Radar_ | `legislative-bill-analyzed` (`$0.025` USD) | [Streamable MCP](https://mcp.apify.com/?actors=b2b-quant-apis/brazil-camara-legislative-regulatory-risk-radar) | [`brazil-camara-legislative-regulatory-risk-radar.n8n.json`](n8n_creator_hub_templates/brazil-camara-legislative-regulatory-risk-radar.n8n.json) |

---

## Direct REST API Call (`cURL` Synchronous JSON Dataset Output)

Every Actor can be called synchronously as a stateless HTTP POST endpoint returning clean JSON array records:

```bash
curl -X POST "https://api.apify.com/v2/acts/b2b-quant-apis~multi-ats-tech-job-board-hiring-radar/run-sync-get-dataset-items" \
  -H "Authorization: Bearer <YOUR_APIFY_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "companyBoards": "stripe,cloudflare,anthropic",
    "keyword": "engineer",
    "maxResults": 10
  }'
```

---

## Repository Structure

- [`n8n_super_pipelines/`](./n8n_super_pipelines/) — 4 Multi-Actor enterprise waterfall workflows for n8n.
- [`n8n_creator_hub_templates/`](./n8n_creator_hub_templates/) — 20 Single-Actor scheduled daily n8n workflows.
- [`ai_agents_and_make/`](./ai_agents_and_make/) — 1-Click configs for Claude Desktop, Cursor IDE, Make.com Blueprint, and Python LangChain/CrewAI SDK.
- [`openapi_rapidapi_3_1.json`](./openapi_rapidapi_3_1.json) — Full OpenAPI 3.1.0 specification with 20 POST routes and 40 JSON Schemas.
- [`mcp_directory_manifest.json`](./mcp_directory_manifest.json) — Machine-readable catalog of all 20 MCP Server Cards.
- [`smithery.yaml`](./smithery.yaml) & [`glama.json`](./glama.json) — Official MCP Directory discovery manifests.

---

## License

Released under the [MIT License](./LICENSE).
