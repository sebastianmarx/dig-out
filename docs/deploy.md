# Deployment auf AWS

Ein Befehl baut und deployt alles: Backend-Paket, Infrastruktur (Terraform), Plattform-Passwort, Frontend.

Die Produktionswebsite ist unter **https://dig-out.marxai.de** erreichbar. Terraform verwaltet
das ACM-Zertifikat in `us-east-1`, dessen DNS-Validierung sowie die A-/AAAA-Alias-Einträge
in der bestehenden Route-53-Zone `marxai.de`. Die Anwendungsressourcen bleiben in `eu-central-1`.
CloudFront verwendet für die eigene Domain mindestens TLS 1.2.

```bash
uv run --project backend python scripts/deploy.py --alert-email du@example.com
```

## Voraussetzungen

| Was | Prüfen mit |
|---|---|
| AWS-Zugang mit Admin-Rechten im Zielkonto | `aws sts get-caller-identity` |
| Terraform ≥ 1.10 | `terraform version` |
| uv, Node/npm | `uv --version`, `npm --version` |

Der vorhandene S3-Bucket `marx-aws-tfstates` in `eu-central-1` dient als Terraform-Backend.
Die Produktionsumgebung verwendet den Key `dig-out` im Workspace `default`.
Verschlüsselung und natives S3-State-Locking sind aktiviert. Der AWS-Zugang benötigt
Zugriff auf den State und die Lockdatei `dig-out.tflock` sowie das Auflisten des Buckets.
Das Deployment-Skript verwendet diese Konfiguration aus `infra/versions.tf` und legt keinen State-Bucket an.
Weitere Umgebungen (`--env dev`) verwenden eigene Terraform-Workspaces
(z. B. Key `env:/dev/dig-out`). `--region` steuert die Region der Anwendungsressourcen;
die Backend-Region bleibt `eu-central-1`.

Bei einem späteren Backend-Wechsel den vorhandenen State mit `terraform init -migrate-state`
übertragen. `-reconfigure` übernimmt nur die Backend-Konfiguration und kopiert keinen State
([Terraform-Dokumentation](https://developer.hashicorp.com/terraform/cli/commands/init#backend-initialization)).
Das Deployment-Skript verwendet deshalb normales `terraform init` und bricht bei einem
noch nicht migrierten Backend-Wechsel ab.

### State-Wiederherstellung vom 02.11.2026

Der vollständige Produktions-State aus
`s3://digout-tfstate-473197088636-eu-central-1/prod/terraform.tfstate`
wurde nach `s3://marx-aws-tfstates/dig-out` übertragen und anschließend verglichen
(68 verwaltete Ressourcen, 10 Datenabfragen). Der alte State bleibt als Sicherung bestehen;
weitere Deployments verwenden ausschließlich das neue Backend.

Der unvollständige State des fehlgeschlagenen Deployments wurde vor der Übertragung unter
`s3://marx-aws-tfstates/dig-out.recovery-20261102/partial-before.tfstate` gesichert.
Lokale Sicherungen liegen im ignorierten Verzeichnis `build/state-recovery-20261102/`.
State-Dateien enthalten Geheimnisse und gehören nicht ins Repository.

Das fehlgeschlagene Deployment hat außerdem zwei zusätzliche API Gateways mit eigenen
Stages erzeugt: HTTP `wlhlcnsucf` und WebSocket `0vqtx6blm7`. Diese wurden bei der
State-Übertragung nicht gelöscht. Die ursprünglichen, weiterhin vom Produktions-State
verwalteten APIs sind HTTP `v7885w4hsi` und WebSocket `8egqr0ogfh`.

Der anschließende Plan mit den Deployment-Parametern war erfolgreich:
`0 to add, 1 to change, 0 to destroy`. Die einzige Änderung betrifft die
CloudFront-Gate-Function für die neuen Icon-Pfade. Es wurde kein Apply ausgeführt.

Empfehlung: ein eigenes AWS-Konto (oder zumindest Profil) nur für Dig Out, Root-Konto mit MFA, Zugang über IAM Identity Center (`aws sso login --profile digout`, dann `--profile digout` an das Skript hängen).

## Ablauf

1. **Erst ansehen, was passiert** (erstellt den lokalen Build und initialisiert das Backend, ohne Infrastruktur anzulegen):
   ```bash
   uv run --project backend python scripts/deploy.py --plan
   ```
2. **Deployen**:
   ```bash
   uv run --project backend python scripts/deploy.py --alert-email du@example.com
   ```
   Das Skript
   1. zeigt Konto/Region und fragt nach Bestätigung,
   2. verwendet den bestehenden Terraform-State-Bucket `marx-aws-tfstates` mit Key `dig-out`,
   3. baut `build/lambda.zip` (Python 3.13, arm64, inkl. `game-data/`),
   4. führt `terraform apply` aus (Terraform zeigt den Plan und fragt `yes`),
   5. fragt beim ersten Mal das **Plattform-Passwort** ab und speichert nur dessen scrypt-Hash im SSM Parameter Store (nie im Terraform-State),
   6. baut das Frontend, schreibt `config.json` (Cognito-Client, WebSocket-URL), lädt alles nach S3 und invalidiert CloudFront.
3. Am Ende steht die URL (`https://dig-out.marxai.de`). Zertifikatsvalidierung, DNS und CloudFront können beim ersten Mal mehrere Minuten benötigen. Entwicklungsumgebungen verwenden weiterhin ihre eigene CloudFront-URL.
4. Bei `--alert-email` kommt eine Mail von AWS SNS: **Abo bestätigen**, sonst gibt es keine Alarme.

## Erste Schritte auf der Seite

1. URL öffnen → Passwortseite → Plattform-Passwort.
2. „Registrieren“: Name, eigenes Passwort (mind. 10 Zeichen, Groß-/Kleinbuchstaben, Ziffer) und noch einmal das Plattform-Passwort.
3. Freunden URL + Plattform-Passwort geben.

## Später

| Aufgabe | Befehl |
|---|---|
| Neue Version deployen | dasselbe Kommando wie oben (nur Geändertes wird hochgeladen) |
| Plattform-Passwort ändern | `… scripts/deploy.py --set-password` (alte Gate-Cookies bleiben bis zu 30 Tage gültig; sofort sperren: Gate-Key in `infra/gate.tf` per `terraform apply -replace=random_password.gate_key` erneuern) |
| Nur Backend/Infra, kein Frontend | `… scripts/deploy.py --skip-frontend` |
| Zweite Umgebung (z. B. Test) | `… scripts/deploy.py --env dev` |
| Alles löschen | `… scripts/deploy.py --destroy` (State-Bucket bleibt) |
| Konto zurücksetzen (Passwort vergessen) | `aws cognito-idp admin-set-user-password --user-pool-id <id> --username <name> --password <neu> --permanent` |

## Was in AWS entsteht

CloudFront (+ Function als Passwort-Gate, Security-Header, CSP) → S3 (privat) für die Seite und API Gateway HTTP für `/api/*`; API Gateway WebSocket für das Spiel; 6 Python-Lambdas (arm64); DynamoDB (on-demand, TTL); Cognito (Lite); EventBridge Scheduler (nur bei Zeitlimit); SSM Parameter; CloudWatch Logs (14 Tage), optional Alarme + Budget (5 $).

Kosten bei privater Nutzung: im Bereich weniger Cent pro Monat (siehe `project.md` Kap. 6).

## Bekannte Einschränkungen

- Login nutzt Cognito `USER_PASSWORD_AUTH` (Passwort per TLS an Cognito) statt SRP; Tokens liegen im `localStorage`, abgesichert durch die strikte CSP.
- Keine E-Mail-Adresse bei der Registrierung → Passwort-Reset nur durch den Admin (Befehl oben).
