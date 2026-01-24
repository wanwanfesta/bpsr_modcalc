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
    "",
    "筋力強化", "敏捷強化", "知力強化", "特攻ダメージ強化", "精鋭打撃",
    "集中・会心", "集中・幸運", "集中・攻撃速度", "集中・詠唱",
    "物理耐性", "魔法耐性",
    "特攻回復強化", "マスタリー回復強化",
    "極・ダメージ増強", "極・適応力", "極・幸運会心", "極・HP変動",
    "極・絶境守護", "極・HP吸収",
    "極・HP凝縮", "極・応急処置",
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

    "集中・幸運": [
        (1, 3, "Lv1/最大HP+300"),
        (4, 7, "Lv2/最大HP+600"),
        (8, 11, "Lv3/最大HP+900、全属性強度+20"),
        (12, 15, "Lv4/最大HP+1200、全属性強度+40"),
        (16, 19, "Lv5/最大HP+1500、全属性強度+60、幸運の一撃のダメージ倍率+4.7%、幸運の一撃回復の倍率+3.7%"),
        (20, 999, "Lv6/最大HP+1800、全属性強度+80、幸運の一撃のダメージ倍率+7.8%、幸運の一撃回復の倍率+6.2%"),
    ],

    "集中・攻撃速度": [
        (1, 3, "Lv1/適応物理・魔法攻撃力+5"),
        (4, 7, "Lv2/適応物理・魔法攻撃力+10"),
        (8, 11, "Lv3/適応物理・魔法攻撃力+20"),
        (12, 15, "Lv4/適応物理・魔法攻撃力+30"),
        (16, 19, "Lv5/適応物理・魔法攻撃力+40、攻撃速度+3.6%"),
        (20, 999, "Lv6/適応物理・魔法攻撃力+50、攻撃速度+6%"),
    ],

    "集中・詠唱": [
        (1, 3, "Lv1/適応物理・魔法攻撃力+5"),
        (4, 7, "Lv2/適応物理・魔法攻撃力+10"),
        (8, 11, "Lv3/適応物理・魔法攻撃力+20"),
        (12, 15, "Lv4/適応物理・魔法攻撃力+30"),
        (16, 19, "Lv5/適応物理・魔法攻撃力+40、詠唱速度+7.2%"),
        (20, 999, "Lv6/適応物理・魔法攻撃力+50、攻撃速度+12%"),
    ],

    "筋力強化": [
        (1, 3, "Lv1/物理攻撃力+5"),
        (4, 7, "Lv2/物理攻撃力+10"),
        (8, 11, "Lv3/物理攻撃力+15、筋力+10"),
        (12, 15, "Lv4/物理攻撃力+20、筋力+20"),
        (16, 19, "Lv5/物理攻撃力+25、筋力+30、物理防御力無視+11.5%"),
        (20, 999, "Lv6/物理攻撃力+30、筋力+40、物理防御力無視+18.8%"),
    ],

    "敏捷強化": [
        (1, 3, "Lv1/物理攻撃力+5"),
        (4, 7, "Lv2/物理攻撃力+10"),
        (8, 11, "Lv3/物理攻撃力+15、敏捷+10"),
        (12, 15, "Lv4/物理攻撃力+20、敏捷+20"),
        (16, 19, "Lv5/物理攻撃力+25、敏捷+30、物理ダメージ+3.6%"),
        (20, 999, "Lv6/物理攻撃力+30、敏捷+40、物理ダメージ+6%"),
    ],

    "知力強化": [
        (1, 3, "Lv1/魔法攻撃+5"),
        (4, 7, "Lv2/魔法攻撃+10"),
        (8, 11, "Lv3/魔法攻撃+15、知力+10"),
        (12, 15, "Lv4/魔法攻撃+20、知力+20"),
        (16, 19, "Lv5/魔法攻撃+25、知力+30、魔法ダメージ+3.6%"),
        (20, 999, "Lv6/魔法攻撃+30、知力+40、魔法ダメージ+6%"),
    ],

    "精鋭打撃": [
        (1, 3, "Lv1/適応物理・魔法攻撃力+5"),
        (4, 7, "Lv2/適応物理・魔法攻撃力+10"),
        (8, 11, "Lv3/適応物理・魔法攻撃力+15、適応筋力・知力・敏捷+10"),
        (12, 15, "Lv4/適応物理・魔法攻撃力+20、適応筋力・知力・敏捷+20"),
        (16, 19, "Lv5/適応物理・魔法攻撃力+25、適応筋力・知力・敏捷+30、精鋭以上の対象へのダメージ+3.9%"),
        (20, 999, "Lv6/適応物理・魔法攻撃力+30、適応筋力・知力・敏捷+40、精鋭以上の対象へのダメージ+6.6%"),
    ],

    "特攻ダメージ強化": [
        (1, 3, "Lv1/適応物理・魔法攻撃力+5"),
        (4, 7, "Lv2/適応物理・魔法攻撃力+10"),
        (8, 11, "Lv3/適応物理・魔法攻撃力+15、適応筋力・知力・敏捷+10"),
        (12, 15, "Lv4/適応物理・魔法攻撃力+20、適応筋力・知力・敏捷+20"),
        (16, 19, "Lv5/適応物理・魔法攻撃力+25、適応筋力・知力・敏捷+30、特殊攻撃の属性ダメージ+7.2%"),
        (20, 999, "Lv6/適応物理・魔法攻撃力+30、適応筋力・知力・敏捷+40、特殊攻撃の属性ダメージ+12%"),
    ],

    "特攻回復強化": [
        (1, 3, "Lv1/魔法攻撃+5"),
        (4, 7, "Lv2/魔法攻撃+10"),
        (8, 11, "Lv3/魔法攻撃+15、知力+10"),
        (12, 15, "Lv4/魔法攻撃+20、知力+20"),
        (16, 19, "Lv5/魔法攻撃+25、知力+30、特殊攻撃回復+7.2%"),
        (20, 999, "Lv6/魔法攻撃+30、知力+40、特殊攻撃回復+12%"),
    ],

    "マスタリー回復強化": [
        (1, 3, "Lv1/魔法攻撃+5"),
        (4, 7, "Lv2/魔法攻撃+10"),
        (8, 11, "Lv3/魔法攻撃+15、知力+10"),
        (12, 15, "Lv4/魔法攻撃+20、知力+20"),
        (16, 19, "Lv5/魔法攻撃+25、知力+30、マスタリースキル回復+7.2%"),
        (20, 999, "Lv6/魔法攻撃+30、知力+40、マスタリースキル回復+12%"),
    ],

    "物理耐性": [
        (1, 3, "Lv1/物理防御力+80"),
        (4, 7, "Lv2/物理防御力+160"),
        (8, 11, "Lv3/物理防御力+240、全属性攻撃力+5"),
        (12, 15, "Lv4/物理防御力+320、全属性攻撃力+10"),
        (16, 19, "Lv5/物理防御力+400、全属性攻撃力+15、物理軽減+3.6%"),
        (20, 999, "Lv6/物理防御力+480、全属性攻撃力+20、物理軽減+6%"),
    ],

    "魔法耐性": [
        (1, 3, "Lv1/耐久力+30"),
        (4, 7, "Lv2/耐久力+60"),
        (8, 11, "Lv3/耐久力+90、最大HP+1%"),
        (12, 15, "Lv4/耐久力+120、最大HP+2%"),
        (16, 19, "Lv5/耐久力+150、最大HP+3%、魔法軽減+3.6%"),
        (20, 999, "Lv6/耐久力+180、最大HP+4%、魔法軽減+6%"),
    ],
    "極・ダメージ増強": [
        (1, 3, "Lv1/適応物理・魔法攻撃力+10"),
        (4, 7, "Lv2/適応物理・魔法攻撃力+20"),
        (8, 11, "Lv3/適応物理・魔法攻撃力+30、適応筋力・知力・敏捷+20"),
        (12, 15, "Lv4/適応物理・魔法攻撃力+40、適応筋力・知力・敏捷+40"),
        (16, 19, "Lv5/適応物理・魔法攻撃力+50、適応筋力・知力・敏捷+60、ダメージを与えた時20%の確率でその対象に与えるダメージ+1.65%(最大4スタック、持続8秒)"),
        (20, 999, "Lv6/適応物理・魔法攻撃力+60、適応筋力・知力・敏捷+80、ダメージを与えた時20%の確率でその対象に与えるダメージ+2.75%(最大4スタック、持続8秒)"),
    ],

    "極・HP変動": [
        (1, 3, "Lv1/最大HP+600"),
        (4, 7, "Lv2/最大HP+1200"),
        (8, 11, "Lv3/最大HP+1800、適応筋力・知力・敏捷+20"),
        (12, 15, "Lv4/最大HP+2400、適応筋力・知力・敏捷+40"),
        (16, 19, "Lv5/最大HP+3000、適応筋力・知力・敏捷+60、現在HPが変化すると会心・器用・ファスト・万能・幸運の中で最も高いステータスが+6%(持続5秒)"),
        (20, 999, "Lv6/最大HP+3600、適応筋力・知力・敏捷+80、現在HPが変化すると会心・器用・ファスト・万能・幸運の中で最も高いステータスが+10%(持続5秒)"),
    ],

    "極・適応力": [
        (1, 3, "Lv1/適応物理・魔法攻撃力+10"),
        (4, 7, "Lv2/適応物理・魔法攻撃力+20"),
        (8, 11, "Lv3/適応物理・魔法攻撃力+30、適応筋力・知力・敏捷+20"),
        (12, 15, "Lv4/適応物理・魔法攻撃力+40、適応筋力・知力・敏捷+40"),
        (16, 19, "Lv5/適応物理・魔法攻撃力+50、適応筋力・知力・敏捷+60、戦闘開始後に移動速度+18%/攻撃力+6%(攻撃を受けると消失し、5秒間ダメージを受けずにいると再獲得)"),
        (20, 999, "Lv6/適応物理・魔法攻撃力+60、適応筋力・知力・敏捷+80、戦闘開始後に移動速度+30%/攻撃力+10%(攻撃を受けると消失し、5秒間ダメージを受けずにいると再獲得)"),
    ],

    "極・HP凝縮": [
        (1, 3, "Lv1/適応物理・魔法攻撃力+10"),
        (4, 7, "Lv2/適応物理・魔法攻撃力+20"),
        (8, 11, "Lv3/適応物理・魔法攻撃力+30、適応筋力・知力・敏捷+20"),
        (12, 15, "Lv4/適応物理・魔法攻撃力+40、適応筋力・知力・敏捷+40"),
        (16, 19, "Lv5/適応物理・魔法攻撃力+50、適応筋力・知力・敏捷+60、自身のHPが50%を上回るとき超過量5%につき回復量+0.66%"),
        (20, 999, "Lv6/適応物理・魔法攻撃力+60、適応筋力・知力・敏捷+80、自身のHPが50%を上回るとき超過量5%につき回復量+1.1%"),
    ],

    "極・応急処置": [
        (1, 3, "Lv1/魔法攻撃力+10"),
        (4, 7, "Lv2/魔法攻撃力+20"),
        (8, 11, "Lv3/魔法攻撃力+30、知力+20"),
        (12, 15, "Lv4/魔法攻撃力+40、知力+40"),
        (16, 19, "Lv5/魔法攻撃力+50、知力+60、HP50%未満時に攻撃を受けると回復オーラを獲得。5秒間自身と周囲の味方最大10名のHPを毎秒7.2%回復する(リキャスト30秒)"),
        (20, 999, "Lv6/魔法攻撃力+60、知力+80、HP50%未満時に攻撃を受けると回復オーラを獲得。5秒間自身と周囲の味方最大10名のHPを毎秒12%回復する(リキャスト30秒)"),
    ],

    "極・絶境守護": [
        (1, 3, "Lv1/最大HP+600"),
        (4, 7, "Lv2/最大HP+1200"),
        (8, 11, "Lv3/最大HP+1800、筋力+20"),
        (12, 15, "Lv4/最大HP+2400、筋力+40"),
        (16, 19, "Lv5/最大HP+3000、筋力+60、ダメージ軽減+2%、HPが70%未満のとき20%下がるごとに2.4%のダメージ軽減を獲得する(最大3スタック)"),
        (20, 999, "Lv6/最大HP+3600、筋力+80、ダメージ軽減+3.5%、HPが70%未満のとき20%下がるごとに4%のダメージ軽減を獲得する(最大3スタック)"),
    ],

    "極・HP吸収": [
        (1, 3, "Lv1/物理攻撃力+10"),
        (4, 7, "Lv2/物理攻撃力+20"),
        (8, 11, "Lv3/物理攻撃力+30、筋力+20"),
        (12, 15, "Lv4/物理攻撃力+40、筋力+40"),
        (16, 19, "Lv5/物理攻撃力+50、筋力+60、クラススキルがダメージを与えたとき、そのダメージの1.8%相当のHPを回復する(最大HPの5%が上限)"),
        (20, 999, "Lv6/物理攻撃力+60、筋力+80、クラススキルがダメージを与えたとき、そのダメージの3%相当のHPを回復する(最大HPの5%が上限)"),
    ],

    "極・幸運会心": [
        (1, 3, "Lv1/適応物理・魔法攻撃力+10"),
        (4, 7, "Lv2/適応物理・魔法攻撃力+20"),
        (8, 11, "Lv3/適応物理・魔法攻撃力+30、適応筋力・知力・敏捷+20"),
        (12, 15, "Lv4/適応物理・魔法攻撃力+40、適応筋力・知力・敏捷+40"),
        (16, 19, "Lv5/適応物理・魔法攻撃力+50、適応筋力・知力・敏捷+60、パーティ全員の会心ダメージ+3.1%/幸運ダメージ+2%(自身は2倍の効果を獲得し、同時に複数は有効にならない)"),
        (20, 999, "Lv6/適応物理・魔法攻撃力+60、適応筋力・知力・敏捷+80、パーティ全員の会心ダメージ+5.2%/幸運ダメージ+3.4%(自身は2倍の効果を獲得し、同時に複数は有効にならない)"),
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
                    agg[s] = agg.get(s, 0) + v_int
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

    st.markdown("""
    <div style="font-size:13px; font-weight:normal; line-height:1.5;">
    ☆登録の仕方☆<br>
    1. スプレッドシートを開く<br>
    2. モジュール内容を記入して CSV ファイルとしてダウンロード<br>
    3. 下の CSV 読み込み欄にダウンロードしたファイルをドラッグ＆ドロップ<br>
    <br>
    ※手動での登録も可能ですが、ブラウザ更新時にリセットされます。
    </div>
    """, unsafe_allow_html=True)

    st.markdown(
    '<a href="https://docs.google.com/spreadsheets/d/1sQOyxh46OnNera2yMkagimaa7D_KRKjhWLdUmgfWFEw/edit?gid=0#gid=0" target="_blank" style="text-decoration:none;">'
    '<button style="padding:8px 16px; font-size:16px;">📄 スプレッドシートを開く</button>'
    '</a>',
    unsafe_allow_html=True
)


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
            col_del_left, col_del_right = st.columns([1, 0.25])
            with col_del_right:
             if st.button("✕ 削除", key=f"delete_{i}"):
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
    # CSV 読み込み（倉庫に追加） 
    # ---------------------------------------------------------
    st.write("---")
    if "csv_processed" not in st.session_state:
        st.session_state["csv_processed"] = False
    uploaded_csv = st.file_uploader("📤 CSVを読み込んで倉庫に追加", type="csv")

if uploaded_csv is not None and not st.session_state["csv_processed"]:
    try:
        df = pd.read_csv(uploaded_csv, header=1)

        new_modules = []
        for _, row in df.iterrows():
            name = row.get("モジュール名（変更可）", "")
            if not isinstance(name, str) or name.strip() == "":
                continue  # モジュール名が空ならスキップ

            # ▼ 効果・数値がすべて空ならスキップ
            has_effect = any([
                pd.notna(row.get("効果1")),
                pd.notna(row.get("効果2")),
                pd.notna(row.get("効果3")),
                pd.notna(row.get("数値1")),
                pd.notna(row.get("数値2")),
                pd.notna(row.get("数値3")),
            ])
            if not has_effect:
                continue

            new_modules.append({
                "name": name,
                "s1": row.get("効果1") if pd.notna(row.get("効果1")) else None,
                "v1": str(int(row.get("数値1"))) if pd.notna(row.get("数値1")) else None,
                "s2": row.get("効果2") if pd.notna(row.get("効果2")) else None,
                "v2": str(int(row.get("数値2"))) if pd.notna(row.get("数値2")) else None,
                "s3": row.get("効果3") if pd.notna(row.get("効果3")) else None,
                "v3": str(int(row.get("数値3"))) if pd.notna(row.get("数値3")) else None,
            })

        modules.extend(new_modules)
        st.session_state["modules"] = modules
        save_to_local_storage("modules_data", json.dumps(modules))

        st.success(f"CSV から {len(new_modules)} 件のモジュールを追加しました！")
        st.session_state["csv_processed"] = True
        st.session_state["uploaded_csv"] = None
        st.rerun()


    except Exception as e:
        st.error("CSV の読み込みに失敗しました。形式を確認してください。")

