# update_ai_log.py
# Version: 1.0.3 | 自動產生 docs/AI-Log.md | 支援 modules + metadata + Prompt 結構

from datetime import datetime
import yaml
from pathlib import Path

module_dir = Path("modules")
metadata_dir = Path("metadata")
prompt_dir = Path("Prompt")
ai_log_path = Path("docs/AI-Log.md")

ai_name = "ChatGPT GPT-4o"
today = datetime.today().strftime("%Y-%m-%d")

modules = sorted([f for f in module_dir.glob("M*.py") if f.is_file()])
log_entries = []

for pyfile in modules:
    stem = pyfile.stem
    mod_id = stem.split("_")[0]
    mod_name = "_".join(stem.split("_")[1:])
    meta_file = metadata_dir / f"{stem}.yaml"
    prompt_file = prompt_dir / f"{stem}.md"

    title, desc = "(未設定標題)", ""
    if meta_file.exists():
        try:
            with open(meta_file, encoding="utf-8") as f:
                data = yaml.safe_load(f)
                title = data.get("title", title)
                desc = data.get("description", "")
        except Exception as e:
            print("警告：無法解析 {}：{}".format(meta_file.name, e))

    section = (
        "### {} - {} 模組\n\n"
        "- 使用 AI：{}\n"
        "- 建立日期：{}\n"
        "- 使用 metadata：{}\n"
        "- 提示詞：{}\n"
        "- 標題：{}\n"
        "- 備註：{}\n"
    ).format(
        mod_id,
        mod_name.replace("_", " "),
        ai_name,
        today,
        meta_file.name if meta_file.exists() else "未找到",
        prompt_file.name if prompt_file.exists() else "未找到",
        title,
        desc if desc else "無"
    )

    log_entries.append(section)

full_text = "# AI 協作日誌紀錄\n\n" + "\n---\n\n".join(log_entries) + "\n"

ai_log_path.parent.mkdir(parents=True, exist_ok=True)
ai_log_path.write_text(full_text.replace("\n", "\n"), encoding="utf-8")

print("✅ AI-Log.md 已成功更新：{}".format(ai_log_path))
