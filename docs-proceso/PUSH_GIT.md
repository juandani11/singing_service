# PUSH_GIT — publicación de `App-SyncDance` (v0.4.0)

> Fecha: 2026-11-16 · Repo remoto: `https://github.com/juandani11/singing_service.git`
> Rama publicada: `sprint2` · Tag de release: `v0.4.0` (`ddfe6ef`).
> El commit de este reporte es posterior y avanza `sprint2`; el tag `v0.4.0`
> sigue apuntando a `ddfe6ef`.

## 1. Estado local inicial

```text
$ git remote -v
# (sin salida: no había remote configurado)

$ git branch -a
  master
  sprint1
* sprint2

$ git tag -l
v0.2.2
v0.2.3
v0.3.0
v0.4.0

$ git status --short
# (limpio)

$ git log --oneline -5
b562277 chore: reorganizar root en docs-proceso/ (auditorías, cierres, handoffs, histórico)
1acec2a docs: MENSAJE_CORE actualizado a v0.4.0 (aditivos Sprint 2)
22b79a9 docs: cierre v0.4.0 (Sprint 2 completo)
ddfe6ef chore(singing-service): release v0.4.0 — Sprint 2 (production-ready)
8d10789 chore(singing-service): HU-S1-08 migrar TestClient a httpx2 (v0.4.0-dev)

$ git rev-parse v0.4.0^{commit}
ddfe6ef8d0285823d7ff60704eb7a17a993bcc57
```

## 2. Auditoría de secretos

```text
--- SENSITIVE FILES ---
singing-service/.env.example
--- GITIGNORE ---
# Python
__pycache__/
*.py[cod]
*.egg-info/
.venv/
venv/
.pytest_cache/
.coverage
htmlcov/
.ruff_cache/

# Entornos
.env
.env.local
*.log

# Fixtures generadas (no commitear audios)
singing-service/integration/fixtures/
singing-service/integration/fixtures/**/*.wav
singing-service/integration/fixtures/**/*.m4a
singing-service/integration/fixtures/**/*.mp3
singing-service/integration/fixtures/**/*.aac
singing-service/integration/fixtures/**/*.ogg

# OS
.DS_Store
Thumbs.db

# IDE
.idea/
.vscode/
*.swp

# Docker
*.pid

# Secretos
*.pem
*.key

# Obsidian (workspace personal / binario Enterprise Architect)
Docs/Obsidian/.obsidian/
Docs/Obsidian/.trash/
Docs/Obsidian/**/*.eap
--- LARGE FILES (>5MB) ---
# (ninguno)
```

**Falso positivo:** `singing-service/.env.example` es una plantilla con
placeholders (`SINGING_SERVICE_URL`, límites, `FFMPEG_BINARY=`), **sin
credenciales**. No hay `.env` real trackeado ni archivos >5 MB. El `.gitignore`
cubre `.env`, `.venv/`, caches, fixtures, `.obsidian/` y `**/*.eap`.

## 3. Remote configurado

```text
origin  https://x-access-token@github.com/juandani11/singing_service.git (fetch)
origin  https://x-access-token@github.com/juandani11/singing_service.git (push)
```

> El token PAT se usó solo en memoria (askpass temporal) y **no** se guardó en
> `.git/config`, en este documento ni en el historial. La URL pública es
> `https://github.com/juandani11/singing_service.git`.

`git ls-remote --heads --tags origin` antes del push: **vacío** (repo nuevo, sin
refs). No había branches/tags que difirieran.

## 4. Push de branches

```text
$ git push -u origin master
To https://github.com/juandani11/singing_service.git
 * [new branch]      master -> master
branch 'master' set up to track 'origin/master'.

$ git push -u origin sprint1
To https://github.com/juandani11/singing_service.git
 * [new branch]      sprint1 -> sprint1
branch 'sprint1' set up to track 'origin/sprint1'.

$ git push -u origin sprint2
To https://github.com/juandani11/singing_service.git
 * [new branch]      sprint2 -> sprint2
branch 'sprint2' set up to track 'origin/sprint2'.
```

## 5. Push de tags

```text
$ git push origin --tags
To https://github.com/juandani11/singing_service.git
 * [new tag]         v0.2.2 -> v0.2.2
 * [new tag]         v0.2.3 -> v0.2.3
 * [new tag]         v0.3.0 -> v0.3.0
 * [new tag]         v0.4.0 -> v0.4.0
```

## 6. Verificación remota (`ls-remote`)

> Snapshot del push de release. El commit de este reporte avanza `sprint2`
> después; el tag `v0.4.0` no se mueve.

```text
$ git ls-remote --heads origin
d056e9409ba59d5904feec84af9e3240210cebd6    refs/heads/master
5c1366dcecf5e47a6fa46d3f1a2ad1dc00fdfe7f    refs/heads/sprint1
b5622774878b5a6427166cea2675909d0b66bdc6    refs/heads/sprint2

$ git ls-remote --tags origin
404ed935ec2b5f959887bdb5a192185b4b9519e4    refs/tags/v0.2.2
c83615424958f90cacd3885eb59109e547ee4dc9    refs/tags/v0.2.2^{}
495bbaaec2d8980bbe7e41f2c4408a96fb61f1cf    refs/tags/v0.2.3
f744a8e18e7dac14bb0e6b7d5dbf36258efab7be    refs/tags/v0.2.3^{}
985511bac63cc50c23a61a2a9df534467fa06393    refs/tags/v0.3.0
0016e2e65266ea6086e8c50253932497668e5e8d    refs/tags/v0.3.0^{}
5ab0513500b52e832b0cdfa6421ae4304d5b8a04    refs/tags/v0.4.0
ddfe6ef8d0285823d7ff60704eb7a17a993bcc57    refs/tags/v0.4.0^{}
```

## 7. Simulación de clonado (Core)

```text
$ git clone https://github.com/juandani11/singing_service.git test-clone
Cloning into 'test-clone'...

$ cd test-clone && git tag -l
v0.2.2
v0.2.3
v0.3.0
v0.4.0

$ git checkout v0.4.0
Note: switching to 'v0.4.0'.
HEAD is now at ddfe6ef chore(singing-service): release v0.4.0 — Sprint 2 (production-ready)

$ git log --oneline -1
ddfe6ef chore(singing-service): release v0.4.0 — Sprint 2 (production-ready)

$ ls singing-service/
app  docs  integration  scripts  tests  .dockerignore  .env.example  .gitignore

$ grep -r "0.4.0" singing-service/app/main.py singing-service/app/core/config.py
singing-service/app/main.py:325: "version": "0.4.0",
singing-service/app/main.py:347: "version": "0.4.0",
singing-service/app/main.py:477: "version": "0.4.0",
singing-service/app/core/config.py:16: version: str = "0.4.0"

$ ls singing-service/integration/verify_handoff.sh
singing-service/integration/verify_handoff.sh
```

Clon y checkout **OK**. La carpeta temporal se eliminó después.

## 8. URL final

```text
https://github.com/juandani11/singing_service.git
```

## 9. Cómo Core clona

```bash
git clone https://github.com/juandani11/singing_service.git
cd singing_service
git checkout v0.4.0
cd singing-service
docker compose up -d
bash integration/verify_handoff.sh
```

## 10. Confirmación

- Working tree local **limpio**.
- Tags intactos: `v0.2.2`, `v0.2.3`, `v0.3.0`, `v0.4.0` (mismos commits).
- `Docs/` y `singing-service/` **sin cambios** en el push.
- El tag `v0.4.0` apunta a `ddfe6ef` (release), no a `b562277` (reorg posterior).
