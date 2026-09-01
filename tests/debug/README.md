# Debug Catalog

Pasta para testar o catálogo remoto **sem precisar de nuvem**.

- `catalog.json` — cópia editável do catálogo (`schema_version: 1`). Use para simular updates.
  - Altere `app.catalog_version` (ex: `1.0.0` → `1.0.1-debug`) e `app.changelog` para disparar o aviso de atualização no app.
  - Altere `libraries.warning` para testar aviso de reinstalação de bibliotecas.
  - Adicione/remove entradas em `minecraft.versions`, `java`, `other` — a UI gera cards dinamicamente.

## Como usar localmente

1. **Editar fácil:** rode o editor visual:
   ```bash
   python tools/catalog_editor.py
   # ou para abrir direto o debug:
   python tools/catalog_editor.py tests/debug/catalog.json
   ```

2. **Testar sem internet / offline:**
   ```bash
   # Copia o debug para o cache local do app
   copy tests\debug\catalog.json data\catalog.json
   python -m app.main
   ```

3. **Simular catálogo remoto local (sem nuvem):**
   - Opção A — arquivo local via `data/catalog_url.txt`:
     ```bash
     echo file:///C:/caminho/para/tests/debug/catalog.json > data/catalog_url.txt
     ```
   - Opção B — servidor HTTP simples:
     ```bash
     python -m http.server 8000 --directory tests/debug
     # e em outro terminal:
     echo http://localhost:8000/catalog.json > data/catalog_url.txt
     python -m app.main
     ```

4. **Hospedar em nuvem (produção externa):**
   - Faça upload do `catalog.json` final para um host estático (GitHub Raw, S3, R2, etc).
   - Defina a URL no cliente via `RESOURCE_HUB_CATALOG_URL` ou `data/catalog_url.txt`.
   - O app mantém o catálogo remoto como **única fonte da verdade** — nunca hard-code recursos no Python.

## Validação
O editor e o app validam estritamente o schema antes de salvar/carregar. JSON malformado, `schema_version != 1`, ou URLs inválidas (`javascript:` etc) são rejeitados e o cache válido é preservado.
