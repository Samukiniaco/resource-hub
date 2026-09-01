# Resource Hub

Utilitário desktop Windows para organizar recursos do Vortex Launcher (Minecraft, bibliotecas compartilhadas, Java, patches).

> **Não modifica, embute ou distribui o launcher externo.** Apenas exibe links e copia/abre no navegador padrão.

## Stack
- Python 3.10+, Tkinter, Pillow

## Execução
```bash
pip install -r requirements.txt
python -m app.main
# ou
python app/main.py
```

## Catálogo remoto
- URL configurável via:
  1. `RESOURCE_HUB_CATALOG_URL` (env)
  2. `data/catalog_url.txt` (primeira linha)
  3. fallback `https://example.com/catalog.json` (`app/config.py`)
- Schema `schema_version: 1` validado estritamente; em falha mantém cache local (`data/catalog.json`).
- Banners carregados de forma assíncrona com cache em `data/image_cache/`.

## JavaPath Helper
Aba **Java** → *Selecionar pasta do Java* → busca recursiva por `java.exe` → escolhe destino → atualiza apenas `JavaPath = ...` em `vortex_launcher.conf`, preservando demais linhas/comentários.

## Estrutura
```
app/
  main.py
  config.py
  models/catalog.py
  services/catalog_service.py, image_service.py, java_helper.py
  utils/browser.py, clipboard.py, logger.py
  ui/app.py, styles.py, components/card.py, tabs/*
data/catalog.json  # cache local
assets/
tools/
tests/
```
