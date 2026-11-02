"""Deploy Dig Out to AWS: backend package, infrastructure (Terraform), platform password, frontend.

    uv run --project backend python scripts/deploy.py              # build + deploy everything
    uv run --project backend python scripts/deploy.py --plan       # only show what Terraform would change
    uv run --project backend python scripts/deploy.py --set-password
    uv run --project backend python scripts/deploy.py --destroy    # remove the environment

Needs: AWS credentials (aws configure / SSO), terraform >= 1.10, uv, node/npm.
"""

import argparse
import getpass
import hashlib
import json
import mimetypes
import shutil
import subprocess
import sys
import time
import zipfile
from pathlib import Path

import boto3

ROOT = Path(__file__).resolve().parents[1]
BACKEND, FRONTEND, INFRA = ROOT / "backend", ROOT / "frontend", ROOT / "infra"
BUILD = ROOT / "build"
FIXED_ZIP_TIME = (2020, 1, 1, 0, 0, 0)  # reproducible zip -> Terraform only redeploys on real changes
NO_CACHE = "no-cache, no-store, must-revalidate"
IMMUTABLE = "public, max-age=31536000, immutable"
ONE_DAY = "public, max-age=86400"

mimetypes.add_type("image/webp", ".webp")
mimetypes.add_type("application/manifest+json", ".webmanifest")


def step(title: str) -> None:
    print(f"\n\033[1;33m▶ {title}\033[0m", flush=True)


def run(cmd: list[str], cwd: Path = ROOT, capture: bool = False) -> str:
    print("  $ " + " ".join(cmd), flush=True)
    result = subprocess.run(cmd, cwd=cwd, check=True, text=True, capture_output=capture)
    return result.stdout if capture else ""


# ------------------------------------------------------------------ checks ---

def check_tools() -> None:
    missing = [tool for tool in ("terraform", "uv", "npm") if shutil.which(tool) is None]
    if missing:
        sys.exit(f"Fehlende Werkzeuge: {', '.join(missing)}")


def confirm_account(session: boto3.Session, env: str, assume_yes: bool) -> str:
    identity = session.client("sts").get_caller_identity()
    print(f"  AWS-Konto {identity['Account']} · {identity['Arn']} · Region {session.region_name} · Umgebung {env}")
    if not assume_yes and input("  In dieses Konto deployen? [j/N] ").strip().lower() not in ("j", "ja", "y", "yes"):
        sys.exit("Abgebrochen.")
    return str(identity["Account"])


# ------------------------------------------------------------- lambda build ---

def build_lambda() -> Path:
    """Backend + runtime dependencies (Linux arm64, Python 3.13) + game data -> build/lambda.zip."""
    pkg = BUILD / "lambda"
    shutil.rmtree(pkg, ignore_errors=True)
    pkg.mkdir(parents=True)
    requirements = BUILD / "requirements.txt"
    run(["uv", "export", "--project", str(BACKEND), "--no-dev", "--no-emit-project", "--no-hashes",
         "--frozen", "-o", str(requirements)])
    run(["uv", "pip", "install", "-r", str(requirements), "--target", str(pkg), "--python-platform",
         "aarch64-manylinux2014", "--python-version", "3.13", "--only-binary", ":all:", "--quiet"])
    shutil.copytree(BACKEND / "src" / "digout", pkg / "digout",
                    ignore=shutil.ignore_patterns("__pycache__", "devserver.py", "sim"))
    shutil.copytree(ROOT / "game-data", pkg / "game-data")
    archive = BUILD / "lambda.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(p for p in pkg.rglob("*") if p.is_file() and "__pycache__" not in p.parts):
            info = zipfile.ZipInfo(str(path.relative_to(pkg)), date_time=FIXED_ZIP_TIME)
            info.external_attr = 0o644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(info, path.read_bytes())
    print(f"  {archive.relative_to(ROOT)}: {archive.stat().st_size // 1024} KB")
    return archive


# ---------------------------------------------------------------- terraform ---

def terraform_init(env: str) -> None:
    # Backend changes require an explicit migration; never silently abandon the previous state.
    run(["terraform", "init", "-input=false"], cwd=INFRA)
    # Production uses the exact configured key; other environments have separate states.
    workspace = "default" if env == "prod" else env
    run(["terraform", "workspace", "select", "-or-create", workspace], cwd=INFRA)


def terraform_vars(args: argparse.Namespace, archive: Path) -> list[str]:
    tf_vars = [f"-var=env={args.env}", f"-var=region={args.region}", f"-var=lambda_zip={archive}"]
    if args.alert_email:
        tf_vars.append(f"-var=alert_email={args.alert_email}")
    return tf_vars


def terraform_outputs() -> dict[str, str]:
    raw = json.loads(run(["terraform", "output", "-json"], cwd=INFRA, capture=True))
    return {key: value["value"] for key, value in raw.items()}


# ----------------------------------------------------------- gate password ---

def ensure_gate_password(session: boto3.Session, param: str, force: bool) -> None:
    sys.path.insert(0, str(BACKEND / "src"))
    from digout.aws.security import hash_password

    ssm = session.client("ssm")
    if not force:
        try:
            ssm.get_parameter(Name=param)
            print("  Plattform-Passwort ist gesetzt (ändern mit --set-password)")
            return
        except ssm.exceptions.ParameterNotFound:
            print("  Noch kein Plattform-Passwort gesetzt.")
    while True:
        first = getpass.getpass("  Neues Plattform-Passwort (mind. 12 Zeichen): ")
        if len(first) < 12:
            print("  Zu kurz.")
            continue
        if getpass.getpass("  Wiederholen: ") == first:
            break
        print("  Stimmt nicht überein.")
    ssm.put_parameter(Name=param, Value=hash_password(first), Type="SecureString", Overwrite=True)
    print("  gespeichert (nur der scrypt-Hash, in SSM Parameter Store)")


# ------------------------------------------------------------------ frontend ---

def cache_control(key: str) -> str:
    if key in ("index.html", "config.json") or key.startswith("gate/"):
        return NO_CACHE
    if key.startswith("assets/") and key.count("/") == 1:
        return IMMUTABLE  # Vite output with content hash in the file name
    return ONE_DAY        # rendered art (stable names)


def deploy_frontend(session: boto3.Session, outputs: dict[str, str]) -> None:
    if not (FRONTEND / "node_modules").exists():
        run(["npm", "ci"], cwd=FRONTEND)
    run(["npm", "run", "build"], cwd=FRONTEND)
    dist = FRONTEND / "dist"
    (dist / "config.json").write_text(json.dumps({
        "mode": "aws",
        "region": outputs["region"],
        "clientId": outputs["user_pool_client_id"],
        "wsUrl": outputs["ws_url"],
    }))

    s3 = session.client("s3")
    bucket = outputs["site_bucket"]
    existing = {o["Key"]: o["ETag"].strip('"') for page in s3.get_paginator("list_objects_v2").paginate(Bucket=bucket)
                for o in page.get("Contents", [])}
    files = {p.relative_to(dist).as_posix(): p for p in dist.rglob("*") if p.is_file()}
    uploaded = 0
    for key, path in sorted(files.items()):
        data = path.read_bytes()
        if existing.get(key) == hashlib.md5(data).hexdigest() and cache_control(key) != NO_CACHE:
            continue
        content_type = mimetypes.guess_type(key)[0] or "application/octet-stream"
        s3.put_object(Bucket=bucket, Key=key, Body=data, ContentType=content_type, CacheControl=cache_control(key))
        uploaded += 1
    stale = [k for k in existing if k not in files]
    for i in range(0, len(stale), 1000):
        s3.delete_objects(Bucket=bucket, Delete={"Objects": [{"Key": k} for k in stale[i:i + 1000]]})
    print(f"  {uploaded} Dateien hochgeladen, {len(stale)} veraltete gelöscht")

    session.client("cloudfront").create_invalidation(
        DistributionId=outputs["distribution_id"],
        InvalidationBatch={"Paths": {"Quantity": 4, "Items": ["/", "/index.html", "/config.json", "/gate/*"]},
                           "CallerReference": str(time.time())},
    )


# ---------------------------------------------------------------------- main ---

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--env", default="prod")
    parser.add_argument("--region", default="eu-central-1")
    parser.add_argument("--profile", help="AWS-Profil (sonst Standard-Credentials)")
    parser.add_argument("--alert-email", help="E-Mail für Fehler-Alarme und Budget-Warnung")
    parser.add_argument("--plan", action="store_true", help="nur terraform plan, nichts ändern")
    parser.add_argument("--set-password", action="store_true", help="Plattform-Passwort (neu) setzen")
    parser.add_argument("--skip-frontend", action="store_true")
    parser.add_argument("--destroy", action="store_true", help="Umgebung komplett löschen")
    parser.add_argument("--yes", action="store_true", help="keine Rückfragen")
    args = parser.parse_args()

    check_tools()
    session = boto3.Session(profile_name=args.profile, region_name=args.region)
    step("AWS-Konto")
    confirm_account(session, args.env, args.yes)

    step("Backend-Paket bauen")
    archive = build_lambda()

    step("Infrastruktur (Terraform)")
    terraform_init(args.env)
    tf_vars = terraform_vars(args, archive)
    if args.destroy:
        run(["terraform", "destroy", "-input=false", *tf_vars, *(["-auto-approve"] if args.yes else [])], cwd=INFRA)
        print("\nUmgebung gelöscht. (Der State-Bucket bleibt bestehen.)")
        return
    if args.plan:
        run(["terraform", "plan", "-input=false", *tf_vars], cwd=INFRA)
        return
    run(["terraform", "apply", "-input=false", *tf_vars, *(["-auto-approve"] if args.yes else [])], cwd=INFRA)
    outputs = terraform_outputs()

    step("Plattform-Passwort")
    ensure_gate_password(session, outputs["gate_hash_param"], args.set_password)

    if not args.skip_frontend:
        step("Frontend")
        deploy_frontend(session, outputs)

    print(f"\n\033[1;32m✔ Fertig: {outputs['site_url']}\033[0m")
    print("  CloudFront braucht beim ersten Mal bis zu ~10 Minuten, bis die Seite überall erreichbar ist.")


if __name__ == "__main__":
    main()
