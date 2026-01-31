#!/bin/bash

echo 'Instalando dependências do Playwright...'
pip install playwright

echo 'Baixando navegadores...'
playwright install chromium firefox

echo 'Script de exemplo criado e salvo em /home/holloway/ziva/workspace/playwright_example.py'