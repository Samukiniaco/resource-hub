# Web Resource Hub (protótipo CSS/JS)

Lê o **MESMO** `data/catalog.json` — o `tools/catalog_editor.py` continua funcionando sem conversão.

## Rodar local (2 opções)
```bash
# da raiz do repo:
python -m http.server 8000
# abrir http://localhost:8000/web/
```
Ou abra `web/index.html` direto (usa fallback raw.githubusercontent se `../data` bloqueado por file://).

## Por que web?
- CSS resolve janelas de tamanho errado (responsivo, sem botão escondido)
- Scroll nativo do navegador (sem mirar na barra)
- `<details>` para changelog (expandir logo abaixo, sem bug de closure)
- Imagens com `onerror="this.remove()"` (sem "banner indisponível")

## Catalog editor
Inalterado — edite e `☁️ Publicar`, a web puxa o mesmo raw. Backup em `backups/catalog-2026-09-08/`.
