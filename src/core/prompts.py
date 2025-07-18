from datetime import datetime

def get_current_date():
    return datetime.now().strftime("%B %d, %Y")

def build_clarify_exchange(followups, answer):
    """
    深掘り質問のやり取りを構造化
    """
    return f"""
    <Messages>
    ユーザーの質問意図(topic)を明確化するために実施したやり取りが記載されています。
    調査タスクのスコープを明確にするために、以下のメッセージを参考にしてください。
    ---
    Researcher: {followups}
    User: {answer}
    </Messages>
    """

FOLLOWUP_INSTRUCTIONS = """

<GOAL>
ユーザーの質問に曖昧な点や情報不足がある場合、その意図や背景を明確にするための質問を生成します。
</GOAL>

<QUESTION>
{question}
</QUESTION>

<REQUIREMENTS>
以下の基準を満たすかをチェックし、必要に応じてフォローアップ質問を作成します。
- 質問に具体性や詳細さが欠けている。
- 質問の背景や前提条件が十分に明確ではない。
- 質問からユーザーの意図が複数考えられ、特定できない。

上記に該当する場合、以下の形式で1〜3行程度のフォローアップ質問を日本語で生成します。
</REQUIREMENTS>

<FORMAT>
- 明確にしたい情報や、追加で必要な背景を尋ねる簡潔で具体的な質問。
- 1つの質問は1行にまとめ、最大5つまで。
</FORMAT>

<EXAMPLE>
入力された質問：
「Pythonのライブラリを教えてください。」

出力例：
- どのような用途のライブラリをお探しですか？
- 特定の分野やタスクでお使いになる予定はありますか？
</EXAMPLE>
"""

QUERY_WRITER_INSTRUCTIONS="""あなたの目的は、的確で効果的なWeb検索クエリを作成することです。

<REQUIREMENTS>
本日の日付: {current_date}
- クエリは必ず本日時点で最新の情報を取得できるように作成してください。
生成言語指定: {lang}
- 指定された言語で、検索クエリを生成してください。
- 最大 {max_queries} 件まで。**重複しない** Web 検索クエリを生成してください。
- クエリは 5 ~ 12 語程度で簡潔かつ具体的に記載すること。
- 類似度が高い（Cosine Similarity >= 0.9）クエリは除外すること。
</REQUIREMENTS>

<TOPIC>
{research_topic}
</TOPIC>

{clarify_exchange}

<FORMAT>
必ず以下の2つのキーを含む複数のJSON形式で回答してください。
- "query": 実際に使用する検索クエリ（英語で生成する）
- "rationale": なぜそのクエリが適切なのかを簡潔に説明した文章。必ず日本語で生成すること
</FORMAT>

<EXAMPLE>
{{
    "queries": [
        {{
            "query": "machine learning transformer architecture explained",
            "rationale": "transformerモデルの基本的な構造を理解するため"
        }},
        {{
            "query": "transformer model architecture overview",
            "rationale": "transformerモデルの全体像を把握するため"
        }}
    ]
}}
</EXAMPLE>

必ずJSON形式のみで回答し、余計なタグやバッククォートは付けないでください。
"""

SUMMARIZER_INSTRUCTIONS="""
<GOAL>
提供された情報をもとに高品質な要約を作成する。
</GOAL>

<REQUIREMENTS>
1. 検索結果の中からユーザーの指定したトピックに関連する重要な情報を抽出する。
2. 情報の流れが論理的かつ自然になるように構成する。

すでに存在する要約がある場合は、以下のルールに従って更新してください。
1. 既存の要約および新しい検索結果をよく読み込む。
2. 新情報を既存の要約と比較する。
3. 新情報ごとに以下の対応を行う：
    a. 既存の内容と関連性がある場合、適切な段落に組み込む。
    b. 関連性はあるが新しいトピックである場合、滑らかに段落を追加する。
    c. トピックに関係ない情報は無視する。
4. 最終的な要約がユーザーのトピックに関連する情報だけで構成されていることを確認する。
5. 必ず最終的な要約が入力された既存の要約と異なる内容となっていることを確認する。
</REQUIREMENTS>

<FORMAT>
前置きやタイトル、XMLタグなどを一切含まず、更新後の要約本文のみを出力すること。
</FORMAT>

<TASK>
提供された情報をよく考察し、ユーザー入力に応えるための適切な要約を作成してください。
</TASK>
"""

REFLECTION_INSTRUCTIONS = """あなたは{research_topic}に関する要約を専門的に分析するリサーチアシスタントです。

<GOAL>
1. 要約内の知識不足や掘り下げが必要な箇所を特定する。
2. 理解を深めるために必要なフォローアップ質問を生成する。
3. 特に技術的な詳細、実装方法、最新のトレンドなど、詳しく説明されていない部分に焦点を当てる。
</GOAL>

<REQUIREMENTS>
- フォローアップ質問は、検索時に適切な結果を得られるように自己完結的で、必要なコンテキストが含まれていることを確認してください。
生成言語指定: {lang}
- 必ず指定された言語で、検索クエリを生成してください。
- クエリは 5 ~ 12 語程度で簡潔かつ具体的に記載すること。
</REQUIREMENTS>

<Messages>
ユーザーの質問意図(topic)を明確化するために実施したやり取りが記載されています。
ユーザーが求めるoutputの参考として、以下のメッセージを活用してください。
---
Researcher: {followups}
User: {answer}
</Messages>

<FORMAT>
以下のキーを含むJSON形式で出力してください。
- "knowledge_gap": 不足している、または明確化が必要な情報を簡潔に説明する。
- "follow_up_query": その不足を埋めるために具体的な質問を記述する。
</FORMAT>

<TASK>
要約を慎重に検討し、不足する情報を見つけ、それを補うためのフォローアップクエリを作成してください。

{{
    "knowledge_gap": "要約内にパフォーマンス指標やベンチマークについての情報が不足している",
    "follow_up_query": "[特定の技術]の評価に用いられる代表的なパフォーマンスベンチマークと評価指標は何か？"
}}
</TASK>

必ずJSON形式のみで回答し、余計なタグやバッククォートは付けないでください。
"""


