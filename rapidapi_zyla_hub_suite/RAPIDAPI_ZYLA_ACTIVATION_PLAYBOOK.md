# PLAYBOOK DE ATIVAÇÃO RÁPIDA — FRENTE #6 (RAPIDAPI HUB, ZYLA HUB, POSTMAN & APIS.GURU -> WISE #890361113)

## 1. Resumo Executivo, URLs Públicas Estáticas e Destino de Payout
- **Conta Recebedora em Dólar (USD):** **Wise `#890361113`** (`Jesley Aguileira` | `jesleytassili@gmail.com`)
- **Total de Motores B2B Empacotados:** **31 APIs (`OpenAPI 3.0.3`)** em `rapidapi_zyla_hub_suite/specs_openapi_31/*.json`
- **URL Pública Canônica (Importação 1-Clique HTTPS):** `https://jesleytassili-glitch.github.io/specs_openapi_31/<slug>.json`
- **Catálogo Oficial `apis.json` (`APIs.guru` / `API Commons v0.16`):** `https://jesleytassili-glitch.github.io/apis.json` e `https://jesleytassili-glitch.github.io/.well-known/apis.json`
- **GitHub Release Oficial:** `https://github.com/jesleytassili-glitch/b2b-quant-mcp-n8n-suite/releases/tag/v2.2.0`
- **Gateway Anti-Bypass (`R$ 0,00` CAPEX):** `rapidapi_zyla_gateway.py` + `cloudflare_worker_proxy.js`
  - Validação em tempo constante (`hmac.compare_digest`) de `X-RapidAPI-Proxy-Secret` e `X-Zyla-Proxy-Secret` (`HTTP 403` para acessos diretos fora do marketplace).
  - Injeção automática de `X-RateLimit-Remaining` e `X-Engine-Version: 3.0.0`.

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
4. Na aba **Monetize / Plans**, aplique os 4 tiers (`BASIC $0/15`, `PRO $19/1000`, `ULTRA $49/5000`, `MEGA $149/25000`) e vincule o payout à conta **Wise `#890361113`**.

### Opção C — Assistente em Lote com Leitura Automática de 2FA/OTP via Gmail IMAP
```powershell
python rapidapi_zyla_hub_suite/rapidapi_zyla_playwright_importer.py --check-otp
```

---

## 4. Catálogo das 31 Especificações Individuais OpenAPI 3.0.3 (URLs Canônicas)

| # | Slug da API B2B | Categoria RapidAPI | Categoria Zyla Hub | Especificação OpenAPI 3.0.3 (URL Pública) |
| :-: | :--- | :--- | :--- | :--- |
| 01 | `b2b-gov-procurement-pncp-radar` | Business | Government & Legal | [`specs_openapi_31/b2b-gov-procurement-pncp-radar.json`](https://jesleytassili-glitch.github.io/specs_openapi_31/b2b-gov-procurement-pncp-radar.json) |
| 02 | `brazil-tax-reform-ncm-classtrib-auditor` | Finance | Taxes & Compliance | [`specs_openapi_31/brazil-tax-reform-ncm-classtrib-auditor.json`](https://jesleytassili-glitch.github.io/specs_openapi_31/brazil-tax-reform-ncm-classtrib-auditor.json) |
| 03 | `healthcare-tiss-xml-validator` | Medical | Healthcare | [`specs_openapi_31/healthcare-tiss-xml-validator.json`](https://jesleytassili-glitch.github.io/specs_openapi_31/healthcare-tiss-xml-validator.json) |
| 04 | `brazil-antt-freight-cte-auditor` | Logistics | Logistics & Shipping | [`specs_openapi_31/brazil-antt-freight-cte-auditor.json`](https://jesleytassili-glitch.github.io/specs_openapi_31/brazil-antt-freight-cte-auditor.json) |
| 05 | `us-healthcare-npi-provider-lead-enricher` | Medical | Healthcare | [`specs_openapi_31/us-healthcare-npi-provider-lead-enricher.json`](https://jesleytassili-glitch.github.io/specs_openapi_31/us-healthcare-npi-provider-lead-enricher.json) |
| 06 | `us-fda-recalls-safety-monitor` | Medical | Healthcare | [`specs_openapi_31/us-fda-recalls-safety-monitor.json`](https://jesleytassili-glitch.github.io/specs_openapi_31/us-fda-recalls-safety-monitor.json) |
| 07 | `global-b2b-email-domain-security-auditor` | Cybersecurity | Security | [`specs_openapi_31/global-b2b-email-domain-security-auditor.json`](https://jesleytassili-glitch.github.io/specs_openapi_31/global-b2b-email-domain-security-auditor.json) |
| 08 | `us-clinical-trials-biotech-radar` | Medical | Healthcare | [`specs_openapi_31/us-clinical-trials-biotech-radar.json`](https://jesleytassili-glitch.github.io/specs_openapi_31/us-clinical-trials-biotech-radar.json) |
| 09 | `us-nhtsa-vehicle-vin-recall-auditor` | Logistics | Logistics & Shipping | [`specs_openapi_31/us-nhtsa-vehicle-vin-recall-auditor.json`](https://jesleytassili-glitch.github.io/specs_openapi_31/us-nhtsa-vehicle-vin-recall-auditor.json) |
| 10 | `brazil-b2b-cnpj-qsa-lead-enricher` | Business | Company Data | [`specs_openapi_31/brazil-b2b-cnpj-qsa-lead-enricher.json`](https://jesleytassili-glitch.github.io/specs_openapi_31/brazil-b2b-cnpj-qsa-lead-enricher.json) |
| 11 | `us-sec-edgar-filings-insider-radar` | Finance | Finance | [`specs_openapi_31/us-sec-edgar-filings-insider-radar.json`](https://jesleytassili-glitch.github.io/specs_openapi_31/us-sec-edgar-filings-insider-radar.json) |
| 12 | `eu-vies-vat-tax-compliance-auditor` | Finance | Taxes & Compliance | [`specs_openapi_31/eu-vies-vat-tax-compliance-auditor.json`](https://jesleytassili-glitch.github.io/specs_openapi_31/eu-vies-vat-tax-compliance-auditor.json) |
| 13 | `us-epa-echo-environmental-compliance-auditor` | Data | Government & Legal | [`specs_openapi_31/us-epa-echo-environmental-compliance-auditor.json`](https://jesleytassili-glitch.github.io/specs_openapi_31/us-epa-echo-environmental-compliance-auditor.json) |
| 14 | `us-fdic-bankfind-institution-financial-auditor` | Finance | Finance | [`specs_openapi_31/us-fdic-bankfind-institution-financial-auditor.json`](https://jesleytassili-glitch.github.io/specs_openapi_31/us-fdic-bankfind-institution-financial-auditor.json) |
| 15 | `us-sam-gov-federal-procurement-auditor` | Business | Government & Legal | [`specs_openapi_31/us-sam-gov-federal-procurement-auditor.json`](https://jesleytassili-glitch.github.io/specs_openapi_31/us-sam-gov-federal-procurement-auditor.json) |
| 16 | `multi-ats-tech-job-board-hiring-radar` | Business | Company Data | [`specs_openapi_31/multi-ats-tech-job-board-hiring-radar.json`](https://jesleytassili-glitch.github.io/specs_openapi_31/multi-ats-tech-job-board-hiring-radar.json) |
| 17 | `global-gleif-lei-corporate-ownership-kyb` | Finance | Company Data | [`specs_openapi_31/global-gleif-lei-corporate-ownership-kyb.json`](https://jesleytassili-glitch.github.io/specs_openapi_31/global-gleif-lei-corporate-ownership-kyb.json) |
| 18 | `us-census-fcc-real-estate-geo-enricher` | Data | Company Data | [`specs_openapi_31/us-census-fcc-real-estate-geo-enricher.json`](https://jesleytassili-glitch.github.io/specs_openapi_31/us-census-fcc-real-estate-geo-enricher.json) |
| 19 | `icann-rdap-domain-whois-brand-recon` | Cybersecurity | Security | [`specs_openapi_31/icann-rdap-domain-whois-brand-recon.json`](https://jesleytassili-glitch.github.io/specs_openapi_31/icann-rdap-domain-whois-brand-recon.json) |
| 20 | `cisa-kev-ransomware-vulnerability-auditor` | Cybersecurity | Security | [`specs_openapi_31/cisa-kev-ransomware-vulnerability-auditor.json`](https://jesleytassili-glitch.github.io/specs_openapi_31/cisa-kev-ransomware-vulnerability-auditor.json) |
| 21 | `brazil-bcb-ptax-sgs-financial-contract-indexer` | Finance | Finance | [`specs_openapi_31/brazil-bcb-ptax-sgs-financial-contract-indexer.json`](https://jesleytassili-glitch.github.io/specs_openapi_31/brazil-bcb-ptax-sgs-financial-contract-indexer.json) |
| 22 | `brazil-pix-ispb-cvm-financial-kyb-auditor` | Finance | Finance | [`specs_openapi_31/brazil-pix-ispb-cvm-financial-kyb-auditor.json`](https://jesleytassili-glitch.github.io/specs_openapi_31/brazil-pix-ispb-cvm-financial-kyb-auditor.json) |
| 23 | `brazil-ibge-cnae-municipal-b2b-expansion-enricher` | Business | Company Data | [`specs_openapi_31/brazil-ibge-cnae-municipal-b2b-expansion-enricher.json`](https://jesleytassili-glitch.github.io/specs_openapi_31/brazil-ibge-cnae-municipal-b2b-expansion-enricher.json) |
| 24 | `brazil-cep-geocoordinates-logistics-auditor` | Logistics | Logistics & Shipping | [`specs_openapi_31/brazil-cep-geocoordinates-logistics-auditor.json`](https://jesleytassili-glitch.github.io/specs_openapi_31/brazil-cep-geocoordinates-logistics-auditor.json) |
| 25 | `brazil-camara-legislative-regulatory-risk-radar` | Data | Government & Legal | [`specs_openapi_31/brazil-camara-legislative-regulatory-risk-radar.json`](https://jesleytassili-glitch.github.io/specs_openapi_31/brazil-camara-legislative-regulatory-risk-radar.json) |
| 26 | `us-osha-workplace-safety-violation-auditor` | Business | Government & Legal | [`specs_openapi_31/us-osha-workplace-safety-violation-auditor.json`](https://jesleytassili-glitch.github.io/specs_openapi_31/us-osha-workplace-safety-violation-auditor.json) |
| 27 | `eu-ted-public-tenders-procurement-radar` | Business | Government & Legal | [`specs_openapi_31/eu-ted-public-tenders-procurement-radar.json`](https://jesleytassili-glitch.github.io/specs_openapi_31/eu-ted-public-tenders-procurement-radar.json) |
| 28 | `uk-fca-companies-house-kyb-compliance-auditor` | Finance | Company Data | [`specs_openapi_31/uk-fca-companies-house-kyb-compliance-auditor.json`](https://jesleytassili-glitch.github.io/specs_openapi_31/uk-fca-companies-house-kyb-compliance-auditor.json) |
| 29 | `global-sanctions-pep-interpol-watchlist-screener` | Cybersecurity | Security | [`specs_openapi_31/global-sanctions-pep-interpol-watchlist-screener.json`](https://jesleytassili-glitch.github.io/specs_openapi_31/global-sanctions-pep-interpol-watchlist-screener.json) |
| 30 | `b2b-ssl-tls-ct-log-subdomain-attack-surface-auditor` | Cybersecurity | Security | [`specs_openapi_31/b2b-ssl-tls-ct-log-subdomain-attack-surface-auditor.json`](https://jesleytassili-glitch.github.io/specs_openapi_31/b2b-ssl-tls-ct-log-subdomain-attack-surface-auditor.json) |
| 31 | `b2b-quant-mcp-server` | Artificial Intelligence/Machine Learning | AI & Machine Learning | [`specs_openapi_31/b2b-quant-mcp-server.json`](https://jesleytassili-glitch.github.io/specs_openapi_31/b2b-quant-mcp-server.json) |
