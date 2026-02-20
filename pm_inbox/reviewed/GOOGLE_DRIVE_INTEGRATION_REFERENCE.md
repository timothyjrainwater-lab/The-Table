# GOOGLE DRIVE INTEGRATION — OPERATIONAL REFERENCE
# Last updated: 2026-02-20
# Purpose: Document Drive API access for Slate and future agents

---

## A) CREDENTIALS

**Google Cloud Project:** Gemini API (gen-lang-client-0512210458)
**OAuth Client Type:** Desktop Application
**Client ID:** 353636649802-uu7u55p7hqphunmgohanqumsd5vrdter.apps.googleusercontent.com
**Credentials JSON:** F:/DnD-3.5/credentials.json (copy of downloaded OAuth client secret)
**Token cache:** C:/Users/Thunder/.config/google-docs-mcp/token.json

**Scopes authorized:**
- https://www.googleapis.com/auth/drive
- https://www.googleapis.com/auth/drive.file
- https://www.googleapis.com/auth/documents

**OAuth consent screen:** External, test mode. Test user: timothy.j.rainwater@gmail.com

---

## B) TOKEN REFRESH

Access tokens expire after 1 hour. Refresh with:

```bash
curl -s -X POST "https://oauth2.googleapis.com/token" \
  -d "client_id=353636649802-uu7u55p7hqphunmgohanqumsd5vrdter.apps.googleusercontent.com" \
  -d "client_secret=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" \
  -d "refresh_token=1//06w2f70kqkzhgCgYIARAAGAYSNwF-L9IrGQEFZw7LCcC8y1x74NOjKmydqN1myXMxn-51aNW4OkyKzFuk0yPVyug7iNQo1GfuJ_c" \
  -d "grant_type=refresh_token"
```

Returns JSON with `access_token`. Use in Authorization header: `Bearer <token>`

Refresh token expires in ~7 days from creation (604800s). If expired, re-auth is required via the OAuth flow.

---

## C) KNOWN DRIVE FILES

| File | Drive ID | Type | Purpose |
|------|----------|------|---------|
| AEGIS_REHYDRATION_PACKET | 1ZICQUDKVuO0oNqFiFl6gq5VizthLp8LxDLYgW41Gfac | Google Doc | Sovereign rehydration for Aegis (GPT). Contains Seven Wisdoms, identity, DR-014. |
| AEGIS_MEMORY_LEDGER | 10fGUlCnKQUFkuNqpUOKpT3PQb_TXXjlqKT7UB4VrUX0 | Google Doc | Append-only backup of Aegis memory items. Operator-controlled. Newest-first entries. |
| SLATE_NOTEBOOK | 1Py1N-dCnl2Azdol2MOREdoQkT_oqvpCXRJzqca9SR3Y | Google Doc | Slate's append-only personal ledger. Decisions, mistakes, patterns. Rehydration-grade memory. |
| ANVIL_NOTEBOOK | 1pdWxIvGEsLpPUBptNVuC9uPP9ytyiwMXZGwsdzvAip0 | Google Doc | Anvil's append-only personal ledger. Creative observations, experiment findings. Rehydration-grade memory. |

**Web links:**
- Rehydration Packet: https://docs.google.com/document/d/1ZICQUDKVuO0oNqFiFl6gq5VizthLp8LxDLYgW41Gfac/edit
- Memory Ledger: https://docs.google.com/document/d/10fGUlCnKQUFkuNqpUOKpT3PQb_TXXjlqKT7UB4VrUX0/edit
- Slate Notebook: https://docs.google.com/document/d/1Py1N-dCnl2Azdol2MOREdoQkT_oqvpCXRJzqca9SR3Y/edit
- Anvil Notebook: https://docs.google.com/document/d/1pdWxIvGEsLpPUBptNVuC9uPP9ytyiwMXZGwsdzvAip0/edit

---

## D) COMMON OPERATIONS

### List files
```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  "https://www.googleapis.com/drive/v3/files?pageSize=10&fields=files(id,name,mimeType)"
```

### Search files
```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  "https://www.googleapis.com/drive/v3/files?q=name+contains+'REHYDRATION'&fields=files(id,name)"
```

### Upload new file (as Google Doc)
```bash
curl -s -X POST "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart&fields=id,name,webViewLink" \
  -H "Authorization: Bearer $TOKEN" \
  -F "metadata={\"name\": \"FILENAME\", \"mimeType\": \"application/vnd.google-apps.document\"};type=application/json" \
  -F "file=@/path/to/file.md;type=text/markdown"
```

### Update existing file
```bash
curl -s -X PATCH "https://www.googleapis.com/upload/drive/v3/files/FILE_ID?uploadType=media&fields=id,name,modifiedTime" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: text/markdown" \
  --data-binary "@/path/to/file.md"
```

### Create folder
```bash
curl -s -X POST "https://www.googleapis.com/drive/v3/files" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "FOLDER_NAME", "mimeType": "application/vnd.google-apps.folder"}'
```

### Upload file to specific folder
Add `"parents": ["FOLDER_ID"]` to the metadata JSON in the upload command.

---

## E) MCP SERVER (OPTIONAL, NOT YET WIRED)

The `google-docs-mcp` npm package can provide Claude Code with native Drive tools. Current session used direct curl calls instead. To wire up MCP in future:

```bash
claude mcp add --transport stdio \
  --env GOOGLE_CLIENT_ID=353636649802-uu7u55p7hqphunmgohanqumsd5vrdter.apps.googleusercontent.com \
  --env GOOGLE_CLIENT_SECRET=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 \
  google-docs -- cmd /c npx -y google-docs-mcp
```

Requires token.json at ~/.config/google-docs-mcp/token.json (already saved).

---

## F) SECURITY NOTES

- Refresh token has a 7-day expiry window. After that, full re-auth required.
- OAuth consent screen is in test mode. Only timothy.j.rainwater@gmail.com is authorized.
- credentials.json is in the repo root (F:/DnD-3.5/). Add to .gitignore if not already there.
- This file contains client secrets. Do not commit to public repos.
