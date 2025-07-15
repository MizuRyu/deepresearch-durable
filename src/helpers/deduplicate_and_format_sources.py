import os
import requests
import chardet
import lxml.html

from typing import Dict, Any, List, Union
from loguru import logger
from readability import Document

def deduplicate_and_format_sources(
    search_response: Union[Dict[str, Any], List[Dict[str, Any]]],
    max_tokens_per_source: int,
    fetch_full_page: bool = False
) -> str:
    """
    検索APIからのレスポンスを構造化し、URLの重複を排除したテキストを生成します。

    Args:
        search_response (Union[Dict[str, Any], List[Dict[str, Any]]]):
            - dictの場合: 'results'キーに検索結果リストを持つ。
            - listの場合: 各要素が dict で、'results'キーから得たリストを平坦化する。
        max_tokens_per_source (int):
            本文抽出時に許容する最大トークン数（1トークン≒4文字で計算）。
        fetch_full_page (bool, optional):
            True の場合、Tavily の raw_content またはフォールバックで取得したHTMLから
            Readability＋lxmlで本文を抽出し、トークン数制限で切り詰めて付加する。デフォルトは False。

    Returns:
        str:
            各ソースのタイトル、URL、要約スニペット、および
            必要に応じて全文抽出結果を含むフォーマット済み文字列。
    """
    # 検索結果リストに変換
    if isinstance(search_response, dict):
        sources_list = search_response['results']
    elif isinstance(search_response, list):
        sources_list = []
        for response in search_response:
            if isinstance(response, dict) and 'results' in response:
                sources_list.extend(response['results'])
            else:
                sources_list.extend(response)
    else:
        raise ValueError("Input must be either a dict with 'results' or a list of search results")
    
    # URL重複削除
    # TODO: URLのprefixとsuffixを比較対象に設定して重複を検知する必要がありそう（ms learnのja-JP/en-USどっちもとれちゃう問題）
    unique_sources = {}
    for source in sources_list:
        if source['url'] not in unique_sources:
            unique_sources[source['url']] = source
    
    # 出力用フォーマット組み立て
    formatted_text = "Sources:\n\n"
    for i, source in enumerate(unique_sources.values(), 1):
        formatted_text += f"記事タイトル: {source['title']}\nーー\n"
        formatted_text += f"内容抜粋: {source['content']}\nーー\n"

        if fetch_full_page:
            # Tavily の raw_content を使う場合
            raw_content_html = source["raw_content"] or ""

            if isinstance(raw_content_html, (bytes, bytearray)):
                detected = chardet.detect(raw_content_html)
                encoding = detected.get("encoding") or "utf-8"
                raw_content_html = raw_content_html.decode(encoding, errors="replace")
            full_text = raw_content_html
            if not raw_content_html:
            # Tavily の raw_content を使わず、独自で HTML を取得
                url = source["url"]
                headers = {
                    "User-Agent": "Mozilla/5.0 (compatible; MizuRyuBot/1.0; +https://github.com/MizuRyu)"
                }

                try:
                    resp = requests.get(url, headers=headers, timeout=10)
                    resp.raise_for_status()

                    content_type = resp.headers.get("Content-Type", "")
                    if "text/html" not in content_type:
                        logger.warning(f"URL {url} does not return HTML content.")
                        full_text = ""
                        continue
                    
                    raw_content_html = resp.content
                    charset = chardet.detect(raw_content_html).get("encoding") or "utf-8"
                    raw_content_html = raw_content_html.decode(charset, errors="replace")
                    # Readability→lxml で本文のみ抽出
                    doc = Document(raw_content_html)
                    summary_html = doc.summary()
                    root = lxml.html.fromstring(summary_html)
                    full_text = "\n".join(
                        line.strip() for line in root.text_content().splitlines() if line.strip()
                    )

                except Exception as e:
                    logger.error(f"Failed to fetch {url}: {e}")
                    full_text = ""

            # トークン数×4 文字で出力長制限
            limit = max_tokens_per_source * 4
            if len(full_text) > limit:
                full_text = full_text[:limit] + "... [truncated]"

            formatted_text += f"Full source content limited to {max_tokens_per_source} tokens: {full_text}\n\n"

    return formatted_text.strip()

def format_sources(search_results: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    検索結果をタイトルと URL を抽出。

    引数:
        search_results (Dict[str, Any]):
            'results' キーに検索結果オブジェクトのリストを持つ dict

    戻り値:
        List[Dict[str, str]]:
            各ソースのタイトルと URL を含む辞書のリスト
    """
    return [
        {
            "title": source.get("title", "No title available"),
            "url": source.get("url", "No URL available")
        }
        for source in search_results.get("results", [])
    ]