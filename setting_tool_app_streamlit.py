# setting_tool_app_streamlit.py
import streamlit as st
from math import comb

# -----------------------------
# 設定差情報（確率）
# -----------------------------
bet_prob = [0.025, 0.050, 0.054, 0.079, 0.096, 0.104]   # BET高確
hydra_prob = [0.250, 0.250, 0.254, 0.300, 0.317, 0.333] # ヒドラ目
p300 = [0.400, 0.421, 0.421, 0.475, 0.488, 0.500]       # 300ゲーム
p450 = [0.183, 0.204, 0.208, 0.258, 0.292, 0.304]       # 450ゲーム
p650 = [0.100, 0.104, 0.108, 0.179, 0.192, 0.233]       # 650ゲーム
direct_prob = [0.017, 0.017, 0.021, 0.033, 0.042, 0.046] # 直撃
comment_ratio = [(50,50),(57,43),(43,57),(57.5,42.5),(42.5,57.5),(58,42)]
prior = [1/6]*6

# -----------------------------
# 二項分布に基づく尤度
# -----------------------------
def likelihood_binomial(observed, total, prob):
    if total == 0:
        return 1
    return comb(total, observed) * (prob**observed) * ((1-prob)**(total - observed))

# -----------------------------
# 設定判別関数
# -----------------------------
def calc_setting_probability(observed_data, comment_data=None):
    posterior = []
    for i in range(6):
        L = 1
        L *= likelihood_binomial(observed_data['bet'][0], observed_data['bet'][1], bet_prob[i])
        L *= likelihood_binomial(observed_data['hydra'][0], observed_data['hydra'][1], hydra_prob[i])
        L *= likelihood_binomial(observed_data['300'][0], observed_data['300'][1], p300[i])
        L *= likelihood_binomial(observed_data['450'][0], observed_data['450'][1], p450[i])
        L *= likelihood_binomial(observed_data['650'][0], observed_data['650'][1], p650[i])
        L *= likelihood_binomial(observed_data['direct'][0], observed_data['direct'][1], direct_prob[i])
        L *= prior[i]
        posterior.append(L)

    total = sum(posterior)
    posterior = [p/total for p in posterior]

    if comment_data and (comment_data['sally'] + comment_data['maple'] > 0):
        comment_likelihood = []
        total_comments = comment_data['sally'] + comment_data['maple']
        for i in range(6):
            s_prob = comment_ratio[i][0]/100
            Lc = likelihood_binomial(comment_data['sally'], total_comments, s_prob)
            comment_likelihood.append(Lc)
        sum_Lc = sum(comment_likelihood)
        comment_likelihood = [Lc/sum_Lc for Lc in comment_likelihood]
        posterior = [posterior[i]*comment_likelihood[i] for i in range(6)]
        total = sum(posterior)
        posterior = [p/total for p in posterior]

    best_setting = posterior.index(max(posterior)) + 1
    return posterior, best_setting

# -----------------------------
# Streamlitアプリ
# -----------------------------
st.title("L防振り 設定判別ツール")

import streamlit as st

st.set_page_config(page_title="設定推定ツール", layout="wide")

# CSSで入力欄の横幅を縮めつつPC・スマホ対応
st.markdown("""
<style>
/* PCでは横幅広め、スマホでは縮める */
@media (min-width: 768px) {
    div[data-testid="stNumberInput"] {
        max-width: 220px;  /* PC用 */
        margin-bottom: 6px;
    }
}

@media (max-width: 767px) {
    div[data-testid="stNumberInput"] {
        max-width: 160px;  /* スマホ用に縮小 */
        margin-bottom: 4px;
    }
}

div[data-testid="stNumberInput"] label {
    font-size: 0.85em;  /* ラベルを小さく */
}
</style>
""", unsafe_allow_html=True)

# --- 初あたり関連 ---
with st.expander("初あたり関連"):
    col1, col2, col3 = st.columns(3)
    with col1:
        atari_total = st.number_input("初あたり回数", 0, 1000, 3)
    with col2:
        bet_hit = st.number_input("BET高確発生回数", 0, 1000, 1)
    with col3:
        direct_hit = st.number_input("直撃回数", 0, 1000, 0)

# --- ヒドラ目関連 ---
with st.expander("ヒドラ目関連"):
    col1, col2 = st.columns(2)
    with col1:
        hydra_total = st.number_input("通常時ヒドラ目出現回数", 0, 1000, 10)
    with col2:
        hydra_hit = st.number_input("通常時ヒドラ目からのczへの当選回数", 0, 1000, 3)

# --- ゲーム経由CZ ---
with st.expander("ゲーム経由CZ"):
    col1, col2 = st.columns(2)
    with col1:
        total300 = st.number_input("300G経由", 0, 1000, 3)
        total450 = st.number_input("450G経由", 0, 1000, 2)
        total650 = st.number_input("650G経由", 0, 1000, 0)
    with col2:
        hit300 = st.number_input("300G czへの当選", 0, 1000, 1)
        hit450 = st.number_input("450G czへの当選", 0, 1000, 0)
        hit650 = st.number_input("650G czへの当選", 0, 1000, 0)

# --- ボナ終了時コメント ---
with st.expander("ボナ終了時コメント"):
    col1, col2 = st.columns(2)
    with col1:
        sally = st.number_input("サリーしか勝たん出現", 0, 1000, 5)
    with col2:
        maple = st.number_input("メイプルしか勝たん出現", 0, 1000, 5)

comment_data = {'sally': sally, 'maple': maple}



observed = {
    'bet': (bet_hit, atari_total),
    'hydra': (hydra_hit, hydra_total),
    '300': (hit300, total300),
    '450': (hit450, total450),
    '650': (hit650, total650),
    'direct': (direct_hit, atari_total)
}

if st.button("設定を推定する"):
    posterior, best_setting = calc_setting_probability(observed, comment_data)
    
    st.subheader("📊 結果")
    for i, p in enumerate(posterior, 1):
        st.write(f"設定{i}の期待度: {p*100:.2f}%")
    st.success(f"最も期待できる設定は: 設定{best_setting}")

st.info("""注記
- エピソード後の高確率ZONEはBET高確ではありません。
- 設定変更後の450,650Gでの当選はカウントしてはいけません。
- ヒドラ目関連について、ヒドラ目は通常時の高確でないときにひいた前提で設計しています（高確滞在かどうかの判別は難しいので）。高確中に引いた場合を考えると少し精度に影響が出ますが、かなり些細なものなので問題ありません。
- 不確定要素があったり記憶があいまいな場合はすべてカウントに含まないことをお勧めします。（例；当選契機が300gのゾーンか450gのゾーンか忘れた→それぞれ経由回数、当選回数にカウントしない）
- このツールの推定結果はあくまで推定値ですので、参考程度にお願いします。
""")























