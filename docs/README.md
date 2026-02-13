# Backend - Storage e processamento

## Fluxo recomendado (frontend -> storage -> backend)
1. Frontend autentica via Supabase e obtem o JWT do usuario.
2. Frontend faz upload direto no bucket `videos` com path `auth.uid()/...`.
   Exemplo de path: `{user_id}/{video_id}.mp4`.
3. Frontend cria o registro no backend:
   `POST /api/videos/` com `title`, `storage_path` (path relativo ao bucket), `project_id` opcional e `status` inicial (`queued` ou `uploaded`).
4. O backend persiste o registro e devolve **sempre**:
   ```json
   {
     "video_id": "<uuid>",
     "project_id": "<uuid|null>",
     "storage_path": "<path>",
     "status": "<queued|uploaded|processing|error>"
   }
   ```
5. O backend enfileira o pipeline automaticamente apos a persistencia (sem chamada extra do frontend).

## Endpoint de upload legado (deprecated)
`POST /files/upload` continua funcionando, mas esta marcado como deprecated.
Ele valida o JWT do usuario, envia o arquivo para o Storage com Service Role, persiste o registro e retorna o mesmo contrato de `POST /api/videos/`.
Evite usar em producao.

## Delete transacional (logico)
`DELETE /api/videos/{video_id}`
- Remove primeiro o arquivo do Storage e somente depois remove o registro e dependencias.
- Se a remocao do Storage falhar, o registro nao e deletado.

## Storage health (dev only)
`GET /api/storage/health`
- Disponivel apenas em ambiente dev.
- Use `APP_ENV=dev` ou `DEBUG=1` para habilitar.

## Variaveis de ambiente
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY` (necessaria para signed URL e download server-side)
- `SUPABASE_STORAGE_BUCKET` (opcional, default: `videos`)
- `UPLOAD_MAX_SIZE_MB` (opcional, default: 200)

## Endpoint de status
`GET /api/videos/{video_id}`
- Retorna status atualizado do processamento com `error_detail` quando houver falha.
