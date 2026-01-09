import streamlit as st
from itertools import combinations
import json
import os

st.title("AIにつくってもらったもじゅーるしみゅれーたー")

# ---------------------------------------------------------
# CSS（セレクトボックス調整 + プレースホルダー + 結果カード + ボタン色）
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

/* 数値欄のプレースホルダー用の薄いグレー文字 */
.placeholder-option {
    color: #888 !important;
}

/* 結果カード */
.result-card {
    border: 1px solid #ccc;
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 16px;
    background-color: #fafafa;
    box-shadow: 1px 1px 3px rgba(0,0,0,0.1);
}
.result-card h3 {
    margin-top: 0;
}

/* 削除ボタン hover を薄い赤に */
button[kind="secondary"]:hover {
    background-color: #ffdddd !important;
    color: black !important;
}

/* 「＋ 新しいモジュールを追加」ボタンを薄緑に */
button[kind="secondary"][data-testid="baseButton-secondary"]:has(span:contains("新しいモジュールを追加")) {
    background-color: #ddffdd !important;
    color: black !important;
}
button[kind="secondary"][data-testid="baseButton-secondary"]:has(span:contains("新しいモジュールを追加")):hover {
    background-color: #ccffcc !important;
    color: black !important;
}

/* ▼ file_uploader の英語テキストを非表示にする */
div[data-testid="stFileUploader"] section div {
    display: none !important;
}
/* ▼ subheader（h3）のフォントサイズを小さくする */
h3 {
    font-size: 18px !important;
}
/* ▼ タイトル（h1）のフォントサイズを変更 */
h1 {
    font-size: 18px !important;   /* ← 好きなサイズに変更 */
}

</style>
""", unsafe_allow_html=True)



# ---------------------------------------------------------
# ステータス一覧（重複修正済み）
# ---------------------------------------------------------
STATUS_LIST = [
    "",
    "集中・幸運",
    "集中・攻撃速度",
    "集中・会心",
    "集中・詠唱",
    "筋力強化",
    "知力強化",
    "敏捷強化",
    "精鋭打撃",
    "特攻ダメージ強化",
    "特攻回復強化",
    "マスタリー回復強化",
    "物理耐性",
    "魔法耐性"
]

VALUE_LIST = ["0"] + list(range(1, 11))


# ---------------------------------------------------------
# ★★★ ステータス効果テーブル（ここに新しいステータスを追加してください） ★★★
# ---------------------------------------------------------
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
        (16, 19, "Lv5/最大HP+1500、全属性強度+60、幸運の一撃ダメージ倍率+4.7%、幸運の一撃回復倍率+3.7%"),
        (20, 999, "Lv6/最大HP+1800、全属性強度+80、幸運の一撃ダメージ倍率+7.8%、幸運の一撃回復倍率+6.2%"),
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
        (20, 999, "Lv6/適応物理・魔法攻撃力+50、詠唱速度+12%"),
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
        (1, 3, "Lv1/"),
        (4, 7, "Lv2/"),
        (8, 11, "Lv3/"),
        (12, 15, "Lv4/"),
        (16, 19, "Lv5/"),
        (20, 999, "Lv6/"),
    ],

    "知力強化": [
        (1, 3, "Lv1/"),
        (4, 7, "Lv2/"),
        (8, 11, "Lv3/"),
        (12, 15, "Lv4/"),
        (16, 19, "Lv5/"),
        (20, 999, "Lv6/"),
    ],

    "精鋭打撃": [
        (1, 3, "Lv1/適応物理・魔法攻撃力+5"),
        (4, 7, "Lv2/適応物理・魔法攻撃力+10"),
        (8, 11, "Lv3/適応物理・魔法攻撃力+15、適応筋力・知力・敏捷+10"),
        (12, 15, "Lv4/適応物理・魔法攻撃力+20、適応筋力・知力・敏捷+20"),
        (16, 19, "Lv5/適応物理・魔法攻撃力+25、適応筋力・知力・敏捷+30、精鋭以上対象ダメージ+3.9%"),
        (20, 999, "Lv6/適応物理・魔法攻撃力+30、適応筋力・知力・敏捷+40、精鋭以上対象ダメージ+6.6%"),
    ],

    "特攻ダメージ強化": [
        (1, 3, "Lv1/適応物理・魔法攻撃力+5"),
        (4, 7, "Lv2/適応物理・魔法攻撃力+10"),
        (8, 11, "Lv3/適応物理・魔法攻撃力+15、適応筋力・知力・敏捷+10"),
        (12, 15, "Lv4/適応物理・魔法攻撃力+20、適応筋力・知力・敏捷+20"),
        (16, 19, "Lv5/適応物理・魔法攻撃力+25、適応筋力・知力・敏捷+30、特殊攻撃属性ダメージ+7.2%"),
        (20, 999, "Lv6/適応物理・魔法攻撃力+30、適応筋力・知力・敏捷+40、特殊攻撃属性ダメージ+12%"),
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
        (16, 19, "Lv5/"),
        (20, 999, "Lv6/"),
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
}
# ---------------------------------------------------------
# 効果取得関数
# ---------------------------------------------------------
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
# ① 最適化（検索）タブ
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
            st.error("先に『モジュール登録』タブでモジュールを入力してください。")

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
# ② モジュール登録タブ（CSV保存・読み込み対応）
# =========================================================
with tab_register:

    st.subheader("モジュール倉庫（キャッシュに保存されません）")

    # ▼ 初期化
    if "modules" not in st.session_state:
        st.session_state["modules"] = []

    modules = st.session_state["modules"]

    # ---------------------------------------------------------
    # 📥 CSVダウンロード（1クリック）
    # ---------------------------------------------------------
    import pandas as pd

    if len(modules) > 0:
        df = pd.DataFrame(modules)
        csv = df.to_csv(index=False).encode("utf-8")

        st.download_button(
            label="📥 CSVとしてダウンロード",
            data=csv,
            file_name="modules.csv",
            mime="text/csv"
        )
    else:
        st.info("登録されているモジュールがありません。")

    # ---------------------------------------------------------
    # 📤 CSVアップロード（復元）
    # ---------------------------------------------------------
    uploaded_file = st.file_uploader("📤 CSVをアップロードして読み込む", type="csv")

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.session_state["modules"] = df.to_dict(orient="records")
        st.success("CSVを読み込みました！")
        st.rerun()

    # ---------------------------------------------------------
    # モジュール削除処理
    # ---------------------------------------------------------
    delete_index = st.session_state.get("delete_module", None)
    if delete_index is not None:
        if 0 <= delete_index < len(modules):
            del modules[delete_index]
        st.session_state["delete_module"] = None

    # ---------------------------------------------------------
    # モジュール一覧
    # ---------------------------------------------------------
    for i, module in enumerate(modules):

        if "name" not in module or not module["name"]:
            module["name"] = f"モジュール{i+1}"

        with st.expander(f"{module['name']}", expanded=False):

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
                s1 = st.selectbox(
                    "",
                    STATUS_LIST,
                    key=f"m{i}_s1",
                    index=0 if module.get("s1") is None else STATUS_LIST.index(module["s1"]),
                    label_visibility="collapsed"
                )
                v1 = st.selectbox(
                    "",
                    VALUE_LIST,
                    key=f"m{i}_v1",
                    index=0 if module.get("v1") is None else module["v1"],
                    label_visibility="collapsed"
                )
                module["s1"] = None if s1 == "" else s1
                module["v1"] = None if v1 == "0" else v1

            # ▼ ステータス2
            with col2:
                s2 = st.selectbox(
                    "",
                    STATUS_LIST,
                    key=f"m{i}_s2",
                    index=0 if module.get("s2") is None else STATUS_LIST.index(module["s2"]),
                    label_visibility="collapsed"
                )
                v2 = st.selectbox(
                    "",
                    VALUE_LIST,
                    key=f"m{i}_v2",
                    index=0 if module.get("v2") is None else module["v2"],
                    label_visibility="collapsed"
                )
                module["s2"] = None if s2 == "" else s2
                module["v2"] = None if v2 == "0" else v2

            # ▼ ステータス3
            with col3:
                s3 = st.selectbox(
                    "",
                    STATUS_LIST,
                    key=f"m{i}_s3",
                    index=0 if module.get("s3") is None else STATUS_LIST.index(module["s3"]),
                    label_visibility="collapsed"
                )
                v3 = st.selectbox(
                    "",
                    VALUE_LIST,
                    key=f"m{i}_v3",
                    index=0 if module.get("v3") is None else module["v3"],
                    label_visibility="collapsed"
                )
                module["s3"] = None if s3 == "" else s3
                module["v3"] = None if v3 == "0" else v3

            # ▼ 削除ボタン
            if st.button("このモジュールを削除", key=f"delete_{i}"):
                st.session_state["delete_module"] = i
                st.rerun()

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
        st.rerun()

    st.session_state["modules"] = modules
