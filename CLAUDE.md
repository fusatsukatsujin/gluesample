# CLAUDE.md

## ブランチ運用（git flow）

このリポジトリは git flow に従って運用します。

- `main` — リリース済み・本番相当のコードのみを置く。
- `develop` — 統合ブランチ。GitHub のデフォルトブランチ。
- 新規の機能追加・修正は `develop` から `feature/xxx` ブランチを切って作業し、
  `develop` に向けて PR を作成してマージする（`main` に直接コミット・マージしない）。
- リリース時は `develop` → `main` にマージする。
- release/hotfix ブランチの運用ルールはまだ決めていない。リリースが近づいたら
  都度相談する。

### 作業開始時のコマンド例

```bash
git checkout develop
git pull
git checkout -b feature/xxx
```
