# Colocando o catálogo na nuvem ☁️

O `catalog.json` é a **única fonte da verdade** do app. Você edita local com `tools/catalog_editor.py` e hospeda o JSON em qualquer host estático. O app baixa, valida e usa; se falhar, mantém o cache local.

---

## Opção 1 — GitHub (recomendada, grátis, já deste projeto)

### 1. Editar e publicar pelo editor (com autenticação)

1. `python tools/catalog_editor.py` (ou `data/catalog.json` / `tests/debug/catalog.json`)
2. Altere `catalog_version` (ex: `1.0.0` → `1.0.1`) e `changelog` — isso dispara a notificação no app.
3. `Salvar` (Ctrl+S) → valida com `schema_version: 1`.
4. Clique `☁️ Publicar` no topo. O editor pede:
   - **Mensagem do commit** (padrão `chore(catalog): update to vX`)
   - **PAT** (opcional, se o Windows ainda não tem credencial salva). Crie em `github.com/settings/tokens` → *Generate new token (classic)* → scope `repo`. Pode deixar em branco se já fez `git push` antes e salvou no Credential Manager, ou defina `GITHUB_TOKEN` no sistema.
5. O editor faz `git add` + `commit` + `push`. Se der erro de autenticação, ele mantém o commit local e mostra a mensagem para você colar o PAT e tentar de novo.
6. Ao sucesso, ele mostra e copia a **URL Raw**:

```
https://raw.githubusercontent.com/SEU_USER/resource-hub/BRANCH/data/catalog.json
```

### 2. Apontar o app para a URL

No cliente (onde o `Resource Hub` roda), escolha **uma** forma:

- **Arquivo** (mais simples pra testar): crie `data/catalog_url.txt` com a URL na primeira linha:
  ```
  https://raw.githubusercontent.com/Samukiniaco/resource-hub/master/data/catalog.json
  ```
- **Env**: `RESOURCE_HUB_CATALOG_URL` (mesma URL) — útil se distribuir o `.exe` com env.

Pronto. Toda vez que você publicar nova `catalog_version`, o app detecta, mostra changelog e aviso de `libraries.warning` se houver.

> Dica: `raw.githubusercontent.com` tem cache de ~5 min. Se precisar instantâneo, use `cdn.jsdelivr.net/gh/USER/REPO@BRANCH/data/catalog.json`.

### Manual (sem botão)

```bash
git add data/catalog.json
git commit -m "chore(catalog): update to v1.0.1"
git push
```

---

## Opção 2 — Qualquer host estático (S3, R2, Netlify, Drive direto, etc)

1. Edite e `Salvar` no editor.
2. Faça upload do **JSON puro** (não HTML) para o host. Garanta `Content-Type: application/json` e CORS liberado.
3. Copie a URL direta (ex: `https://pub-xxxxx.r2.dev/catalog.json` ou `https://SEU_BUCKET.s3.amazonaws.com/catalog.json`).
4. Aponte `data/catalog_url.txt` ou `RESOURCE_HUB_CATALOG_URL` para ela.

Para testar local sem nuvem:

```bash
# servidor local
python -m http.server 8000 --directory data
echo http://localhost:8000/catalog.json > data/catalog_url.txt
python -m app.main
```

Ou debug dedicado:

```bash
copy tests\debug\catalog.json data\catalog.json
python -m app.main
# depois hospede tests/debug/catalog.json
```

---

## Boas práticas

- **Nunca** hard-code recursos no Python — tudo vem do catalog.
- URLs `link`/`banner` devem ser `https://` (validação rejeita `javascript:`).
- `libraries` é global — não duplique por versão; use `warning` para avisar reinstalação.
- O app nunca baixa/executa arquivos — só `webbrowser.open` + copiar link.
- Mantenha `schema_version: 1`.

---

## Troubleshooting

- **Ctrl+Z não funcionava?** Corrigido: todos os `Text` agora têm `undo=True` e binds `Ctrl+Z`/`Ctrl+Y`/`Ctrl+Shift+Z` + `Ctrl+A`.
- **Push pede senha?** GitHub removeu senha; use PAT (`ghp_...`) ou `gh auth login` (GitHub CLI).
- **404 no app?** Status fica amarelo “Offline — usando cache local” e botão `Abrir URL do catálogo` ajuda a debugar.
- **Raw demora?** Normal (CDN). Aguarde 5 min ou use `cdn.jsdelivr.net`.
