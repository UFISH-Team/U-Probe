from __future__ import annotations

from pathlib import Path
import sys
import traceback
import yaml

def run_uprobe_workflow(*, protocol_yaml: str, username: str, task_id: str, output_dir: str, threads: int, raw_csv: bool, continue_invalid_targets: bool, log_path: str) -> dict:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    log_file = Path(log_path)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    f = open(log_file, "a", encoding="utf-8", buffering=1)
    old_out = sys.stdout
    old_err = sys.stderr
    sys.stdout = f
    sys.stderr = f
    try:
        print("UPROBE_TASK_START")
        print(f"task_id={task_id} user={username} threads={threads} output_dir={output_dir}")
        protocol_dict = yaml.safe_load(protocol_yaml) or {}
        from uprobe.http.utils.paths import get_genomes_yaml, get_user_genomes_yaml
        merged_genomes = {}
        public_yaml = get_genomes_yaml()
        if public_yaml.exists():
            try:
                merged_genomes.update(yaml.safe_load(public_yaml.read_text(encoding="utf-8")) or {})
            except Exception:
                pass
        user_yaml = get_user_genomes_yaml(username)
        if user_yaml.exists():
            try:
                merged_genomes.update(yaml.safe_load(user_yaml.read_text(encoding="utf-8")) or {})
            except Exception:
                pass
        (out_dir / "protocol.yaml").write_text(protocol_yaml, encoding="utf-8")
        (out_dir / "merged_genomes.yaml").write_text(yaml.dump(merged_genomes, default_flow_style=False, sort_keys=False, allow_unicode=True), encoding="utf-8")
        from uprobe.core.api import UProbeAPI
        api = UProbeAPI(protocol_config=protocol_dict, genomes_config=merged_genomes, output_dir=out_dir)
        api.run_workflow(raw_csv=raw_csv, continue_on_invalid_targets=continue_invalid_targets, threads=threads)
        csv_files = [p.name for p in out_dir.glob("*.csv")]
        html_files = [p.name for p in out_dir.glob("*.html")]
        zip_name = f"{task_id}_results.zip"
        zip_path = out_dir / zip_name
        import zipfile
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for p in out_dir.iterdir():
                if p.is_file() and p.suffix in (".csv", ".html", ".yaml", ".log"):
                    zf.write(p, p.name)
        return {"ok": True, "zip_name": zip_name, "csv_files": csv_files, "html_files": html_files}
    except Exception:
        tb = traceback.format_exc()
        try:
            print(tb, file=sys.stderr)
        except Exception:
            pass
        return {"ok": False, "error": tb}
    finally:
        sys.stdout = old_out
        sys.stderr = old_err
        try:
            f.close()
        except Exception:
            pass

