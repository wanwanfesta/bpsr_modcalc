import streamlit as st
import json
import math
from itertools import combinations
import pandas as pd
import streamlit.components.v1 as components

st.title("AIにつくってもらったもじゅーるしみゅれーたー")

# ---------------------------------------------------------
# LocalStorage を扱うための JS ブリッジ
# ---------------------------------------------------------
local_storage_js = """
<script>
function saveToLocalStorage(key, value) {
    localStorage.setItem(key, value);
}

function loadFromLocalStorage(key) {
    return localStorage.getItem(key);
}

window.addEventListener("message", (event) => {
    if (event.data.type === "load_request") {
        const value = loadFromLocalStorage(event.data.key);
        window.parent.postMessage(
            {type: "load_response", key: event.data.key, value: value},
            "*"
        );
    }
});
</script>
"""

st.markdown(local_storage_js, unsafe_allow_html=True)

# ---------------------------------------------------------
# LocalStorage 読み込み（JS → Streamlit）
# ---------------------------------------------------------
def load_from_local_storage(key):
    components.html(
        f"""
        <script>
            const value = localStorage.getItem("{key}");
            const msg = {{
                isStreamlitMessage: true,
                key: "{key}",
                value: value
            }};
            window.parent.postMessage(msg, "*");
        </script>
        """,
        height=0,
    )

    if "local_storage_buffer" not in st.session_state:
        st.session_state["local_storage_buffer"] = {}

    return st.session_state["local_storage_buffer"].get(key)

# ---------------------------------------------------------
# JS からのレスポンス受信
# ---------------------------------------------------------
def process_js_message():
    if "_streamlit_messages" in st.session_state:
        for msg in st.session_state["_streamlit_messages"]:
            if msg.get("isStreamlitMessage"):
                key = msg["key"]
                value = msg["value"]
                st.session_state["local_storage_buffer"][key] = value

process_js_message()

# ---------------------------------------------------------
# LocalStorage 保存（Streamlit → JS）
# ---------------------------------------------------------
def save_to_local_storage(key, value):
    st.markdown(
        f"""
        <script>
            saveToLocalStorage("{key}", `{value}`);
        </script>
        """,
        unsafe_allow_html=True
    )

# ---------------------------------------------------------
# NaN 安全変換
# ---------------------------------------------------------
def safe_int_index(value):
    if value is None:
        return 0
    if isinstance(value, float) and math.isnan(value):
        return 0
    try:
        return int(value)
    except:
        return 0

# ---------------------------------------------------------
# CSS（あなたの元コード）
# ---------------------------------------------------------
st.markdown("""
<style>
div[data-baseweb="select"] {
    margin-top: -6px !important;
    margin-bottom: -6px !important;
}
div[data-baseweb="select"] > div {
    min-height: 32px !important;
    padding-top: 2px !important;
    padding-bottom: 2px !important;
}
.placeholder-option { color: #888 !important; }
.result-card {
    border: 1px solid #ccc;
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 16px;
    background-color: #fafafa;
    box-shadow: 1px 1px 3px rgba(0,0,0,0.1);
}
.result-card h3 { margin-top: 0; }
h3 { font-size: 18px !important; }
h1 { font-size: 18px !important; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# ステータス一覧・効果テーブル
# ---------------------------------------------------------
STATUS_LIST = [
    "", "集中・幸運", "集中・攻撃速度", "集中・会心", "集中・詠唱",
    "筋力強化", "知力強化", "敏捷強化", "精鋭打撃",
    "特攻ダメージ強化", "特攻回復強化", "マスタリー回復強化",
    "物理耐性", "魔法耐性"
]

VALUE_LIST = ["0"] + list(range(1, 11))

EFFECT_TABLE = {
    "集中・会心": [
        (1, 3, "Lv1/最大HP+300"),
        (4, 7, "Lv2/最大HP+600"),
        (8, 11, "Lv3/最大HP+900、全属性強度+20"),
        (12, 15, "Lv4/最大HP+1200、全属性強度+40"),
        (16, 19, "Lv5/最大HP+1500、全属性強度+60、会心ダメージ・会心回復+7.1%"),
        (20, 999, "Lv6/最大HP+1800、全属性強度+80、会心ダメージ・会心回復+12%"),
    ],
}

def get_effect_text(status_name, total_value):
    if status_name not in EFFECT_TABLE:
        return ""
    for low, high, text in EFFECT_TABLE[status_name]:
        if low <= total_value <= high:
            return text
    return ""

# ---------------------------------------------------------
# タブ
# ---------------------------------------------------------
tab_optimize, tab_register = st.tabs(["組み合わせ検索", "モジュール倉庫"])
# =========================================================
# ① 組み合わせ検索タブ（安定版）
# =========================================================
with tab_optimize:

    if "search_rows" not in st.session_state:
        st.session_state["search_rows"] = 1

    if "search_conditions" not in st.session_state:
        st.session_state["search_conditions"] = [{} for _ in range(20)]

    st.subheader("検索条件")

    # ▼ 検索条件の動的追加
    for row in range(st.session_state["search_rows"]):

        col1, col2 = st.columns([7, 3])

        with col1:
            status = st.selectbox(
                "",
                STATUS_LIST,
                key=f"search_status_{row}",
                label_visibility="collapsed"
            )

        with col2:
            value = st.selectbox(
                "",
                [""] + list(range(1, 21)),
                key=f"search_value_{row}",
                label_visibility="collapsed"
            )

        st.session_state["search_conditions"][row] = {
            "status": status,
            "value": value
        }

        # ▼ 両方埋まったら次の行を追加
        if (
            row == st.session_state["search_rows"] - 1
            and status != ""
            and value != ""
            and st.session_state["search_rows"] < 20
        ):
            st.session_state["search_rows"] += 1
            st.rerun()

    st.write("---")

    # ▼ モジュール装備可能数
    slot = st.radio("モジュール装備可能数", [2, 3, 4])

    # ▼ ステータス別合計（20キャップ）
    def aggregate_statuses(combo):
        agg = {}
        for m in combo:
            for s_key, v_key in [("s1", "v1"), ("s2", "v2"), ("s3", "v3")]:
                s = m.get(s_key)
                v = m.get(v_key)
                if s and v:
                    v_int = int(v)
                    agg[s] = min(agg.get(s, 0) + v_int, 20)
        return agg

    # ▼ モジュールのステータス文字列
    def module_status_text(m):
        parts = []
        for s_key, v_key in [("s1", "v1"), ("s2", "v2"), ("s3", "v3")]:
            s = m.get(s_key)
            v = m.get(v_key)
            if s and v:
                parts.append(f"{s} {v}")
        return " / ".join(parts) if parts else "（ステータスなし）"

    # ▼ 実行
    if st.button("組み合わせ検索"):

        if "modules" not in st.session_state or len(st.session_state["modules"]) == 0:
            st.error("先に『モジュール倉庫』タブでモジュールを登録してください。")

        else:
            modules = st.session_state["modules"]

            # 条件抽出
            conditions = []
            for cond in st.session_state["search_conditions"]:
                s = cond.get("status")
                v = cond.get("value")
                if s and v:
                    conditions.append({"status": s, "value": int(v)})

            if len(modules) < slot:
                st.error("適切な組み合わせが存在しません")
            else:
                results = []

                for combo in combinations(modules, slot):
                    agg = aggregate_statuses(combo)

                    ok = True
                    for cond in conditions:
                        if agg.get(cond["status"], 0) < cond["value"]:
                            ok = False
                            break

                    if not ok:
                        continue

                    total_value = sum(agg.values())
                    results.append((total_value, agg, combo))

                st.subheader("検索結果")

                if not results:
                    st.error("適切な組み合わせが存在しません")
                else:
                    results.sort(key=lambda x: x[0], reverse=True)

                    for i, (total, agg, combo) in enumerate(results[:10]):
                        st.markdown("<div class='result-card'>", unsafe_allow_html=True)
                        st.markdown(f"### {i+1}件目")
                        st.write(f"全ステータス合計値: **{total}**")

                        st.write("**ステータス別合計**")
                        for s, v in agg.items():
                            effect = get_effect_text(s, v)
                            if effect:
                                st.write(f"- {s}: {v}（{effect}）")
                            else:
                                st.write(f"- {s}: {v}")

                        st.write("**モジュール一覧**")
                        for m in combo:
                            st.write(f"- {m['name']}（{module_status_text(m)}）")

                        st.markdown("</div>", unsafe_allow_html=True)

                    if len(results) > 10:
                        st.error("ヒット結果が多すぎます！")
# =========================================================
# ② モジュール倉庫タブ（LocalStorage + JSON 完全版）
# =========================================================
with tab_register:

    st.subheader("モジュール倉庫（自動保存されません）")

    # ---------------------------------------------------------
    # LocalStorage から復元
    # ---------------------------------------------------------
    stored = load_from_local_storage("modules_data")

    if stored and "modules" not in st.session_state:
        try:
            st.session_state["modules"] = json.loads(stored)
        except:
            st.session_state["modules"] = []

    if "modules" not in st.session_state:
        st.session_state["modules"] = []

    modules = st.session_state["modules"]

    # ---------------------------------------------------------
    # モジュール一覧（UI）
    # ---------------------------------------------------------
    for i, module in enumerate(modules):

        # 名前が空なら自動補完
        if "name" not in module or not module["name"]:
            module["name"] = f"モジュール{i+1}"

        with st.expander(f"{module['name']}", expanded=False):

            # ▼ モジュール名
            module_name = st.text_input(
                "",
                module["name"],
                key=f"name_{i}",
                label_visibility="collapsed"
            )
            module["name"] = module_name

            col1, col2, col3 = st.columns(3)

            # ▼ ステータス1
            with col1:
                s1_value = module.get("s1")
                s1_index = STATUS_LIST.index(s1_value) if s1_value in STATUS_LIST else 0

                s1 = st.selectbox(
                    "",
                    STATUS_LIST,
                    key=f"m{i}_s1",
                    index=s1_index,
                    label_visibility="collapsed"
                )

                v1 = st.selectbox(
                    "",
                    VALUE_LIST,
                    key=f"m{i}_v1",
                    index=safe_int_index(module.get("v1")),
                    label_visibility="collapsed"
                )

                module["s1"] = None if s1 == "" else s1
                module["v1"] = None if v1 == "0" else v1

            # ▼ ステータス2
            with col2:
                s2_value = module.get("s2")
                s2_index = STATUS_LIST.index(s2_value) if s2_value in STATUS_LIST else 0

                s2 = st.selectbox(
                    "",
                    STATUS_LIST,
                    key=f"m{i}_s2",
                    index=s2_index,
                    label_visibility="collapsed"
                )

                v2 = st.selectbox(
                    "",
                    VALUE_LIST,
                    key=f"m{i}_v2",
                    index=safe_int_index(module.get("v2")),
                    label_visibility="collapsed"
                )

                module["s2"] = None if s2 == "" else s2
                module["v2"] = None if v2 == "0" else v2

            # ▼ ステータス3
            with col3:
                s3_value = module.get("s3")
                s3_index = STATUS_LIST.index(s3_value) if s3_value in STATUS_LIST else 0

                s3 = st.selectbox(
                    "",
                    STATUS_LIST,
                    key=f"m{i}_s3",
                    index=s3_index,
                    label_visibility="collapsed"
                )

                v3 = st.selectbox(
                    "",
                    VALUE_LIST,
                    key=f"m{i}_v3",
                    index=safe_int_index(module.get("v3")),
                    label_visibility="collapsed"
                )

                module["s3"] = None if s3 == "" else s3
                module["v3"] = None if v3 == "0" else v3

            # ▼ 削除ボタン
            if st.button("このモジュールを削除", key=f"delete_{i}"):
                del modules[i]
                st.session_state["modules"] = modules
                save_to_local_storage("modules_data", json.dumps(modules))
                st.rerun()

    # ---------------------------------------------------------
    # ループ終了後に LocalStorage に1回だけ保存（key重複対策）
    # ---------------------------------------------------------
    save_to_local_storage("modules_data", json.dumps(modules))

    # ---------------------------------------------------------
    # モジュール追加
    # ---------------------------------------------------------
    if st.button("＋ 新しいモジュールを追加"):
        modules.append({
            "name": f"モジュール{len(modules)+1}",
            "s1": None, "v1": None,
            "s2": None, "v2": None,
            "s3": None, "v3": None
        })
        st.session_state["modules"] = modules
        save_to_local_storage("modules_data", json.dumps(modules))
        st.rerun()

    # ---------------------------------------------------------
    # JSON 保存（手動バックアップ）
    # ---------------------------------------------------------
    st.write("---")
    st.subheader("📦 JSON バックアップ")

    json_data = json.dumps(modules, ensure_ascii=False, indent=2)
    st.download_button(
        label="📥 モジュール情報をJSONとして保存",
        data=json_data,
        file_name="modules_backup.json",
        mime="application/json"
    )

    # ---------------------------------------------------------
    # JSON 読み込み（復元）※二重実行防止版
    # ---------------------------------------------------------
    uploaded_json = st.file_uploader("📤 JSONを読み込んで復元", type="json")

    if "json_loaded" not in st.session_state:
        st.session_state["json_loaded"] = False

    if uploaded_json is not None and not st.session_state["json_loaded"]:
        try:
            loaded = json.load(uploaded_json)
            st.session_state["modules"] = loaded
            save_to_local_storage("modules_data", json.dumps(loaded))

            st.session_state["json_loaded"] = True
            st.success("JSON を読み込み、モジュールを復元しました！")
            st.rerun()

        except Exception as e:
            st.error("JSON の読み込みに失敗しました。")
