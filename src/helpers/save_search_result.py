from datetime import datetime
from pathlib import Path
from typing import Optional

def save_search_result(
    query: str,
    content: str,
    base_dir: str = "survey",
    ext: str = ".txt",
    *,
    timestamp: Optional[str] = None,
) -> None:
    """
    survey/yyyymmddhhss/ にディレクトリを用意し、
    `query` をファイル名にしたファイルを生成して `content` を書き込む。

    Parameters
    ----------
    query : str
        検索ワード。ファイル名に使う。
    content : str
        ファイルに書き込むテキスト（例: search_results_str）。
    base_dir : str, default "survey"
        ルートディレクトリ。
    ext : str, default ".txt"
        生成するファイル拡張子。
    timestamp : str | None
        任意のタイムスタンプ文字列。None なら現在時刻で生成。

    Returns
    -------
    pathlib.Path
        作成したファイルのフルパス。
    """
    # 1. yyyymmddhhss 形式のタイムスタンプ
    ts = timestamp or datetime.now().strftime("%Y%m%d%H%M%S")

    # 2. ディレクトリ作成（既に存在しても OK）
    folder = Path(base_dir) / ts
    folder.mkdir(parents=True, exist_ok=True)

    # Sanitize the query to create a safe file name
    safe_name = "".join(
        c if c.isalnum() or c in "-_." else "_"
        for c in query
    ).strip("_")

    file_path = folder / f"{safe_name}{ext}"

    file_path.write_text(content, encoding="utf-8")