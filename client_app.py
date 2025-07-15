import streamlit as st
import requests
import time
import json
import re
from urllib.parse import quote
from typing import Dict, Any, Optional

# 設定
AZURE_FUNCTIONS_URL = "http://localhost:7071"
POLLING_INTERVAL = 0.5  # 0.5秒間隔
TIMEOUT_MINUTES = 10

RESEARCH_STEPS = {
    'generate_query': {
        'name': '検索クエリ生成',
        'description': 'トピックに最適な検索クエリを作成',
        'icon': '🔍'
    },
    'web_research': {
        'name': 'Web検索',
        'description': 'インターネットで関連情報を検索',
        'icon': '🌐'
    },
    'summarize': {
        'name': '検索結果要約',
        'description': '発見した情報を要約・分析',
        'icon': '📝'
    },
    'reflection': {
        'name': 'リフレクション',
        'description': '知識ギャップを発見してより深い調査を計画',
        'icon': '💭'
    },
    'routing': {
        'name': 'ルーティング',
        'description': 'next Action ルーティング処理',
        'icon': '⚙️'
    },
    'waiting_for_followup': {
        'name': 'フォローアップ回答待ち',
        'description': 'ユーザーのフォローアップ回答を待機中',
        'icon': '⌛'
    },
    'finalize': {
        'name': 'レポート作成',
        'description': '調査結果まとめ',
        'icon': '📊'
    }
}


class DurableFunctionsClient:
    """Durable Functions APIクライアント"""

    @staticmethod
    def start_research(question: str) -> Dict[str, Any]:
        """調査を開始"""
        try:
            url = f"{AZURE_FUNCTIONS_URL}/api/deepresearch"
            params = {"question": question}
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"調査開始 Error: {str(e)}")
            return {}

    @staticmethod
    def get_status(status_query_get_uri: str) -> Dict[str, Any]:
        """ステータスを取得"""
        try:
            response = requests.get(status_query_get_uri, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"ステータス取得エラー: {str(e)}")
            return {}

    @staticmethod
    def send_followup(instance_id: str, event_name: str, answer: str) -> None:
        """フォローアップ回答を送信"""
        try:
            url = f"{AZURE_FUNCTIONS_URL}/runtime/webhooks/durabletask/instances/{instance_id}/raiseEvent/{event_name}"
            response = requests.post(url, json={"data": answer}, timeout=10)
            response.raise_for_status()
        except Exception as e:
            st.error(f"フォローアップ送信エラー: {e}")


def initialize_session_state():
    """セッション状態の初期化"""
    if 'research_active' not in st.session_state:
        st.session_state.research_active = False
    if 'instance_id' not in st.session_state:
        st.session_state.instance_id = None
    if 'status_query_uri' not in st.session_state:
        st.session_state.status_query_uri = None
    if 'completed_steps' not in st.session_state:
        st.session_state.completed_steps = set()
    if 'current_step' not in st.session_state:
        st.session_state.current_step = None
    if 'step_history' not in st.session_state:
        st.session_state.step_history = []
    if 'final_report' not in st.session_state:
        st.session_state.final_report = ""
    if 'error_message' not in st.session_state:
        st.session_state.error_message = ""
    if 'research_start_time' not in st.session_state:
        st.session_state.research_start_time = None
    if 'current_loop' not in st.session_state:
        st.session_state.current_loop = 0
    if 'web_search_results' not in st.session_state:
        st.session_state.web_search_results = []
    if 'all_sources' not in st.session_state:
        st.session_state.all_sources = []
    if 'view_mode' not in st.session_state:
        st.session_state.view_mode = 'process'
    if 'followup_sent' not in st.session_state:
        st.session_state.followup_sent = False
    if 'saved_followup_answer' not in st.session_state:
        st.session_state.saved_followup_answer = ""


def render_step_entry(step_info: Dict, loop_count: int = 0) -> None:
    """個別のステップエントリを表示"""
    step_key = step_info['step_key']
    status = step_info['status']
    details = step_info.get('details', {})
    timestamp = step_info.get('timestamp', '')

    if step_key == 'waiting_for_followup':
        with st.container():
            st.markdown(
                f"<strong>✅ {RESEARCH_STEPS[step_key]['icon']} {RESEARCH_STEPS[step_key]['name']}</strong>",
                unsafe_allow_html=True
            )
            st.write("**フォローアップ質問:**")
            st.write(details.get('followups', ''))
            if st.session_state.saved_followup_answer:
                st.write("**ユーザー回答:**")
                st.write(st.session_state.saved_followup_answer)
        return
    
    step_config = RESEARCH_STEPS.get(step_key, {})
    icon = step_config.get('icon', '⚙️')
    name = step_config.get('name', step_key)
    description = step_config.get('description', '')

    # ステータスに応じたスタイル
    if status == 'completed':
        status_icon = "✅"
        style = "color: green;"
    elif status == 'active':
        status_icon = "🔄"
        style = "color: blue;"
    else:
        status_icon = "⏳"
        style = "color: gray;"

    # ループ情報を含むタイトル
    loop_info = f" (ループ {loop_count + 1})" if loop_count > 0 else ""

    # ステップエントリ表示
    with st.container():
        st.markdown(f"""
        <div style="{style} padding: 8px 0;">
            <strong>{status_icon} {icon} {name}{loop_info}</strong><br>
            <small style="color: gray;">{description}</small>
            {f'<br><small style="color: #666;">{timestamp}</small>' if timestamp else ''}
        </div>
        """, unsafe_allow_html=True)

    # 詳細情報表示
    if step_key == 'web_research' and status in ['completed', 'active']:
        with st.expander(f"{name} - 詳細情報", expanded=(status == 'active')):
            for result in st.session_state.web_search_results:
                if result['loop_count'] == loop_count:
                    st.write("**検索結果:**")
                    st.text(result['result'])
                    st.write("**情報ソース:**")
                    for src in result.get('sources', []):
                        if isinstance(src, dict):
                            title = src.get('title', 'No Title')
                            url = src.get('url', '#')
                            st.markdown(f"- [{title}]({url})")
                        elif isinstance(src, str) and src.startswith("http"):
                            st.markdown(f"- [{src}]({src})")
                    st.markdown("---")

    elif details and status in ['completed', 'active']:
        # Web検索以外は常に展開して表示
        if step_key == 'generate_query' and 'queries' in details:
            st.write("**生成されたクエリ:**")
            queries = details['queries']
            if isinstance(queries, dict) and 'queries' in queries:
                queries = queries['queries']
            for i, query in enumerate(queries, 1):
                if isinstance(query, dict):
                    query_text = query.get('query', str(query))
                    rationale = query.get('rationale', '')
                    st.markdown(f"**{i}. {query_text}**")
                    if rationale:
                        st.markdown(f"   _理由: {rationale}_")
                else:
                    st.write(f"{i}. {query}")
                st.markdown("")

        elif step_key == 'summarize' and 'updatedSummary' in details:
            st.write("**要約:**")
            st.markdown(details['updatedSummary'])

        elif step_key == 'reflection' and 'query' in details:
            st.write("**次の検索クエリ:**")
            st.write(f'"{details["query"]}"')
            if 'knowledgeGap' in details:
                st.write("**発見された知識ギャップ:**")
                st.write(details['knowledgeGap'])

        elif step_key == 'routing' and 'decision' in details:
            decision = details['decision']
            reason = details.get('reason', '')
            if decision == 'continue':
                st.info(f"🔄 **継続判定**: {reason}")
                if 'nextQuery' in details:
                    st.write(f"**次のクエリ**: {details['nextQuery']}")
            else:
                st.success(f"✅ **完了判定**: {reason}")

        elif step_key == 'finalize':
            st.success("🎉 研究が完了しました！")


def update_progress_from_custom_status(custom_status: Dict[str, Any]) -> None:
    """custom_statusからプログレス更新"""
    if not custom_status:
        return

    step_type = custom_status.get('type')
    loop_count = custom_status.get('loopCount', 0)
    data = custom_status.get('data', {})

    if step_type:
        st.session_state.current_loop = loop_count
        st.session_state.current_step = step_type
        if step_type == 'waiting_for_followup':
            # イベントIDを保持
            st.session_state.event_id = data.get('eventId')

        unique_id = f"{step_type}_{loop_count}_{int(time.time() * 1000)}"
        step_entry = {
            'step_key': step_type,
            'status': 'completed',
            'details': data,
            'loop_count': loop_count,
            'timestamp': time.strftime('%H:%M:%S'),
            'unique_id': unique_id
        }

        if step_type == 'web_research' and 'researchResult' in data:
            # 重複チェック: 同じループと結果が既に存在しない場合のみ追加
            exists = any(
                r.get('loop_count') == loop_count and r.get('result') == data['researchResult']
                for r in st.session_state.web_search_results
            )
            if not exists:
                search_result = {
                    'result': data['researchResult'],
                    'sources': data.get('source', []),
                    'loop_count': loop_count,
                    'step_id': unique_id,
                    'timestamp': time.strftime('%H:%M:%S')
                }
                st.session_state.web_search_results.append(search_result)
                for source in data.get('source', []):
                    if source not in st.session_state.all_sources:
                        st.session_state.all_sources.append(source)

        existing_entry = None
        for i, entry in enumerate(st.session_state.step_history):
            if (entry['step_key'] == step_type and
                    entry['loop_count'] == loop_count):
                existing_entry = i
                break

        if existing_entry is not None:
            st.session_state.step_history[existing_entry] = step_entry
        else:
            st.session_state.step_history.append(step_entry)

        if step_type == 'finalize':
            if 'finalSummary' in data:
                st.session_state.final_report = data['finalSummary']
            if 'sources' in data:
                for source in data['sources']:
                    if source not in st.session_state.all_sources:
                        st.session_state.all_sources.append(source)


def poll_durable_functions():
    """Durable Functionsをポーリング"""
    if not st.session_state.research_active or not st.session_state.status_query_uri:
        return

    if st.session_state.research_start_time:
        elapsed = time.time() - st.session_state.research_start_time
        if elapsed > TIMEOUT_MINUTES * 60:
            st.session_state.research_active = False
            st.error(f"⏰ 研究がタイムアウトしました（{TIMEOUT_MINUTES}分）")
            return

    status_data = DurableFunctionsClient.get_status(st.session_state.status_query_uri)
    if not status_data:
        return

    runtime_status = status_data.get('runtimeStatus')
    custom_status = status_data.get('customStatus')

    if custom_status:
        update_progress_from_custom_status(custom_status)

    if runtime_status in ['Completed', 'Failed', 'Terminated']:
        st.session_state.research_active = False
        if runtime_status == 'Completed':
            output = status_data.get('output', '')
            if output:
                st.session_state.final_report = output
            st.session_state.view_mode = 'result'
            st.success("🎉 研究が正常に完了しました！")
        else:
            msg = f"❌ 研究が異常終了しました: {runtime_status}"
            if 'output' in status_data:
                msg += f"\nエラー詳細: {status_data['output']}"
            st.session_state.error_message = msg


def main():
    st.set_page_config(
        page_title="Deep Research with Durable Functions",
        page_icon="🔬",
        layout="wide"
    )

    initialize_session_state()

    # ヘッダー
    st.title("🔬 Deep Research with Durable Functions")
    st.markdown("---")

    # 入力セクション
    st.subheader("📝 調査したいトピックを入力してください")
    col1, col2 = st.columns([4, 1])
    with col1:
        question = st.text_input(
            "質問を入力してください",
            placeholder="例: AI Agent をDurable Functionsで構築するコツ",
            disabled=st.session_state.research_active,
            label_visibility="collapsed"
        )
    with col2:
        start_button = st.button(
            "🚀 Research開始",
            disabled=st.session_state.research_active or not question.strip(),
            use_container_width=True
        )

    if start_button and question.strip():
        with st.spinner("調査を開始しています..."):
            result = DurableFunctionsClient.start_research(question.strip())
            if result and 'statusQueryGetUri' in result:
                st.session_state.research_active = True
                st.session_state.instance_id = result.get('id')
                st.session_state.status_query_uri = result['statusQueryGetUri']
                st.session_state.completed_steps = set()
                st.session_state.current_step = None
                st.session_state.step_history = []
                st.session_state.final_report = ""
                st.session_state.error_message = ""
                st.session_state.research_start_time = time.time()
                st.session_state.current_loop = 0
                st.session_state.web_search_results = []
                st.session_state.all_sources = []
                st.session_state.view_mode = 'process'
                st.rerun()

    if st.session_state.error_message:
        st.error(st.session_state.error_message)

    if st.session_state.research_active:
        poll_durable_functions()
        # フォローアップ回答待機時のUI
        if st.session_state.current_step == 'waiting_for_followup' and not st.session_state.followup_sent:
            last_entry = st.session_state.step_history[-1]
            followup = last_entry.get('details', {}).get('followups', '')
            st.subheader("フォローアップ回答")
            st.write(followup)
            answer = st.text_input("フォローアップ回答を入力してください", key="followup_answer")
            if st.button("送信", key="send_followup"):
                DurableFunctionsClient.send_followup(
                    st.session_state.instance_id,
                    f"followup_response_{st.session_state.event_id}",
                    answer
                )
                # 回答送信後、通常のポーリングに戻す
                st.session_state.saved_followup_answer = answer
                st.session_state.followup_sent = True
                st.session_state.current_step = None
                st.rerun()
            return
        st.markdown("---")
        col1, col2 = st.columns([3, 1])
        with col1:
            if st.session_state.current_step:
                info = RESEARCH_STEPS.get(st.session_state.current_step, {})
                st.subheader("現在の調査完了状況：")
                st.markdown(f"### {info.get('icon','⚙️')} {info.get('name','処理中')}")
                st.write(info.get('description','処理を実行中です...'))
            else:
                st.subheader("🚀 調査を開始しています...")
        with col2:
            st.markdown("""
            <div style="text-align: center; padding: 20px;">
                <div style="display: inline-block; width: 40px; height: 40px;
                            border: 4px solid #f3f3f3; border-top: 4px solid #3498db;
                            border-radius: 50%; animation: spin 1s linear infinite;">
                </div>
            </div>
            <style>
            @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
            </style>
            """, unsafe_allow_html=True)
        if st.session_state.current_loop > 0:
            st.info(f"**調査ループ**: {st.session_state.current_loop + 1} 回目")
        st.markdown("---")
        st.subheader("📋 調査過程")
        for step_entry in st.session_state.step_history:
            render_step_entry(step_entry, step_entry['loop_count'])
        time.sleep(POLLING_INTERVAL)
        st.rerun()

    if st.session_state.final_report and not st.session_state.research_active:
        st.markdown("---")
        col1, col2, col3 = st.columns([2, 2, 6])
        with col1:
            if st.button("📋 調査過程", type="primary" if st.session_state.view_mode == 'process' else "secondary"):
                st.session_state.view_mode = 'process'
                st.rerun()
        with col2:
            if st.button("📄 調査結果", type="primary" if st.session_state.view_mode == 'result' else "secondary"):
                st.session_state.view_mode = 'result'
                st.rerun()
        if st.session_state.view_mode == 'result':
            st.subheader("📄 調査結果")
            processed_report = st.session_state.final_report
            st.markdown(processed_report)

        else:
            st.subheader("📋 調査過程")
            for step_entry in st.session_state.step_history:
                render_step_entry(step_entry, step_entry['loop_count'])
        st.markdown("---")
        if st.button("🔄 新しい研究を開始"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()


if __name__ == "__main__":
    main()