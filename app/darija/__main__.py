"""CLI du générateur : python3 -m app.darija biberon --ar "رضاعة" --level 3"""
from .engine import (C, KINDS, LEVELS, REGISTERS, generate, keyword_pools,  # noqa: F401
                     preview, stats, to_arabic, to_arabizi)

import argparse
import json

ap = argparse.ArgumentParser(description="Générateur de patterns darija")
ap.add_argument("keyword", nargs="?", help="mot-clé latin, ex. biberon")
ap.add_argument("--ar", default="", help="mot-clé arabe, ex. رضاعة")
ap.add_argument("--kinds", default="", help=f"familles séparées par des virgules ({','.join(KINDS)})")
ap.add_argument("--registers", default=",".join(REGISTERS))
ap.add_argument("--level", type=int, default=3, choices=(1, 2, 3))
ap.add_argument("--limit", type=int, default=0, help="plafond de patterns")
ap.add_argument("--out", default="", help="fichier de sortie (.yaml / .json / .txt)")
ap.add_argument("--stats", action="store_true", help="afficher la taille du corpus")
a = ap.parse_args()

if a.stats or not a.keyword:
    s = stats()
    print(f"{s['gabarits_total']} gabarits · {s['familles_intentions']} familles "
          f"· registres : {', '.join(s['registres'])}")
    for kind, regs in s["detail"].items():
        print(f"  {kind:14} " + "  ".join(f"{r}:{n:>3}" for r, n in regs.items()))
    if not a.keyword:
        raise SystemExit(0)

kinds = tuple(x.strip() for x in a.kinds.split(",") if x.strip()) or KINDS
regs = tuple(x.strip() for x in a.registers.split(",") if x.strip())
pats = generate(a.keyword, a.ar, kinds=kinds, registers=regs,
                level=a.level, cap=a.limit or None)
print(f"{len(pats)} patterns pour « {a.keyword} »"
      + (f" / « {a.ar} »" if a.ar else "") + f" (niveau {a.level})")
for p in pats[:60]:
    print("  •", p)
if len(pats) > 60:
    print(f"  … {len(pats) - 60} autres")

if a.out:
    from pathlib import Path
    f = Path(a.out)
    if f.suffix == ".json":
        f.write_text(json.dumps(pats, ensure_ascii=False, indent=1), encoding="utf-8")
    elif f.suffix in (".yaml", ".yml"):
        import yaml
        f.write_text(yaml.safe_dump({f"produit_{a.keyword}": {"patterns": pats}},
                                    allow_unicode=True, sort_keys=False, width=4096),
                     encoding="utf-8")
    else:
        f.write_text("\n".join(pats), encoding="utf-8")
    print(f"→ écrit dans {f}")
