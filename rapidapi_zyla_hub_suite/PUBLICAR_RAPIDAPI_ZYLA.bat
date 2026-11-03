@echo off
chcp 65001 >nul
title PUBLICAR 31 APIs B2B — RAPIDAPI HUB & ZYLA API HUB (WISE #890361113)
cd /d "%~dp0\.."

echo ============================================================================
echo  FRENTE #6 (RE-06): SINDICANCIA EXTERNA & IMPORTACAO EM LOTE (v3.0)
echo  Marketplaces: RapidAPI Hub, Zyla API Hub, Postman Network & APIs.guru
echo  Destino de Payout: Wise #890361113 (Jesley Aguileira)
echo ============================================================================
echo.
echo [1/4] Gerando as 31 Especificacoes OpenAPI 3.0.3, apis.json e Postman Collection...
python -X utf8 rapidapi_zyla_hub_suite/generate_rapidapi_zyla_specs.py
if errorlevel 1 goto :erro

echo.
echo [2/4] Publicando URLs Publicas no GitHub Pages (Release v2.2.0) e Validando HTTP 200...
python -X utf8 rapidapi_zyla_hub_suite/openapi_syndicator_2026.py
if errorlevel 1 goto :erro

echo.
echo [3/4] Executando Automatizador em Lote (URL Import + PAPI + Gmail IMAP OTP -> 4 Tiers USD)...
python -X utf8 rapidapi_zyla_hub_suite/rapidapi_zyla_playwright_importer.py --check-otp
if errorlevel 1 goto :erro

echo.
echo [4/4] Executando Bateria Hard-Gate Pytest da Suite RapidAPI & Zyla Hub...
python -X utf8 -m pytest rapidapi_zyla_hub_suite/tests/test_rapidapi_zyla_suite.py -v
if errorlevel 1 goto :erro

echo.
echo ============================================================================
echo  CONCLUIDO COM SUCESSO! 31 Specs OpenAPI 3.0.3, apis.json e URLs HTTP 200 OK.
echo ============================================================================
goto :fim

:erro
echo.
echo [ERRO] Falha durante a execucao da suite RapidAPI / Zyla Hub.
exit /b 1

:fim

