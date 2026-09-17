# JSON — 応答の直列化

| 項目 | 値 |
|---|---|
| 規則ID・版 | JSON-1.0.0 |
| 状態 | 提案（施工判断。Q63 の確定内容にもとづく） |
| 実装 | `mekiki_reader/schema.py` の `to_json` |

- `json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)`。
- 読み取り専用の値（MappingProxyType・tuple）は dict・list に写してから直列化する。
- 配列の順序はツールが全順序で決め、直列化では並べ替えない（limitations だけは外枠で辞書順に並べ、重複を除く）。
- MCP ではこの文字列をそのまま返す（施工段階3）。R01 は、この文字列が別プロセス（PYTHONHASHSEED を変えたもの）でもバイト単位で一致することを確かめる。
- data/bundle_manifest.json の直列化は BUNDLE-1.0.0（字下げ2・末尾 LF）で、この規則とは別。
