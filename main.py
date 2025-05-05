import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import uuid
from summarize import summarize_opinions

# ----------- Firestore初期化 -----------
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase_key.json")
    firebase_admin.initialize_app(cred)
db = firestore.client()

# ----------- 共通スタイル -----------
st.set_page_config(page_title="意見まとめる君", page_icon="📮", layout="centered")
st.markdown("""
    <style>
        .title { font-size:2rem; font-weight:bold; margin-bottom:1rem; }
        .section { margin-top:2rem; margin-bottom:1rem; }
        .opinion-card {
            background-color: #f9f9f9;
            padding: 1em;
            border-radius: 10px;
            margin-bottom: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
    </style>
""", unsafe_allow_html=True)

# ----------- クエリパラメータからページ判定 -----------
params = st.query_params if hasattr(st, "query_params") else {}
page = params.get("page", "create")
topic_id = params.get("id", None)

# ----------- 議題作成ページ -----------
if page == "create":
    st.markdown("<div class='title'>📝 議題を作成する</div>", unsafe_allow_html=True)
    title = st.text_input("議題タイトル", placeholder="例：次の旅行先どうする？")
    if st.button("✅ 投稿ページURLを発行"):
        topic_id = str(uuid.uuid4())
        db.collection("topics").document(topic_id).set({"title": title})
        st.success("このURLをメンバーに共有してください：")
        url = f"?page=post&id={topic_id}"
        st.code(url)
        st.markdown(f"[👉 投稿ページへ移動]({url})", unsafe_allow_html=True)

# ----------- 意見投稿ページ -----------
elif page == "post":
    st.markdown("<div class='title'>💬 意見を投稿する</div>", unsafe_allow_html=True)
    if topic_id:
        doc = db.collection("topics").document(topic_id).get()
        if doc.exists:
            st.subheader(f"📌 議題：{doc.to_dict()['title']}")
            st.markdown("---")
            opinion = st.text_area("あなたの意見（匿名OK）", placeholder="例：〇〇の方が安いと思う")
            if st.button("🚀 投稿する"):
                db.collection("topics").document(topic_id).collection("opinions").add({"text": opinion})
                st.success("ご投稿ありがとうございました！")
            summary_url = f"?page=summary&id={topic_id}"
            st.markdown(f"<div style='margin-top:1rem;'><a href='{summary_url}' target='_self'>📊 結果を見る</a></div>", unsafe_allow_html=True)
        else:
            st.error("議題が見つかりませんでした。")
    else:
        st.warning("URLに `id` が必要です。")

# ----------- 結果ページ -----------
elif page == "summary":
    st.markdown("<div class='title'>📊 結果を表示する</div>", unsafe_allow_html=True)
    if topic_id:
        doc = db.collection("topics").document(topic_id).get()
        if doc.exists:
            st.subheader(f"📌 議題：{doc.to_dict()['title']}")
            st.markdown("---")
            opinions_ref = db.collection("topics").document(topic_id).collection("opinions").stream()
            opinions = [doc.to_dict()["text"] for doc in opinions_ref]

            if opinions:
                st.markdown("### 📝 投稿された意見")
                for i, op in enumerate(opinions):
                    st.markdown(f"<div class='opinion-card'>{i+1}. {op}</div>", unsafe_allow_html=True)

                if st.button("🤖 AIで要約する"):
                    with st.spinner("AIが意見をまとめています..."):
                        summary = summarize_opinions(opinions)
                    st.markdown("### ✅ AIによるまとめ")
                    st.success(summary)
            else:
                st.info("まだ投稿がありません。")
        else:
            st.error("議題が見つかりませんでした。")
    else:
        st.warning("URLに `id` が必要です。")
