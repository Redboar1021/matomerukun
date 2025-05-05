import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import uuid
from summarize import summarize_opinions
import os
import json

# ----------- Firestore初期化 -----------
if not firebase_admin._apps:
    firebase_key_json = os.getenv("FIREBASE_KEY_JSON")
    try:
        if firebase_key_json:
            cred = credentials.Certificate(json.loads(firebase_key_json))
        else:
            cred = credentials.Certificate("firebase_key.json")
        firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error("Firebaseの初期化に失敗しました。Secretsの設定を確認してください。")
        st.stop()
db = firestore.client()

# ----------- 共通スタイル -----------
st.set_page_config(page_title="意見まとめる君", page_icon="📬", layout="centered")
st.markdown("""
    <style>
        body {
            background-color: #e6f7ff;
        }
        .title {
            font-size: 2rem;
            font-weight: bold;
            margin-bottom: 1rem;
            color: #007acc;
        }
        .section {
            margin-top: 2rem;
            margin-bottom: 1rem;
        }
        .opinion-card {
            background-color: #f0faff;
            padding: 1em;
            border-radius: 10px;
            margin-bottom: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
    </style>
""", unsafe_allow_html=True)

# ----------- クエリパラメータからページ判定 -----------
params = st.query_params
page = params.get("page", "create")
topic_id = params.get("id", None)

# ----------- 議題作成ページ -----------
if page == "create":
    st.markdown("<div class='title'>📝 議題を作成する</div>", unsafe_allow_html=True)
    st.info("このツールは、匿名で投稿された意見をAIが中立的に要約するWebアプリです。議題を作成し、共有されたURLに他の人が意見を投稿できます。結果ページでは意見全体を見るか、要約だけ表示するかを選べます。")

    title = st.text_input("議題タイトル", placeholder="例：次の旅行先どうする？")
    display_mode = st.radio("結果ページに表示する内容を選んでください：", ("意見一覧とAI要約", "AI要約のみ"))

    if st.button("✅ 投稿ページURLを発行"):
        topic_id = str(uuid.uuid4())
        show_all = display_mode == "意見一覧とAI要約"
        db.collection("topics").document(topic_id).set({"title": title, "show_all": show_all})
        st.success("このURLをメンバーに共有してください：")
        url = f"https://matomerukun.streamlit.app/?page=post&id={topic_id}"
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
            opinion = st.text_area("あなたの意見（匿名OK）", placeholder="例：○○の方が安いと思う")
            if st.button("🚀 投稿する"):
                db.collection("topics").document(topic_id).collection("opinions").add({"text": opinion})
                st.success("ご投稿ありがとうございました！")
                st.markdown(f"[📊 結果を見る](?page=summary&id={topic_id})", unsafe_allow_html=True)
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
            data = doc.to_dict()
            st.subheader(f"📌 議題：{data['title']}")
            show_all = data.get("show_all", True)
            st.markdown("---")
            opinions_ref = db.collection("topics").document(topic_id).collection("opinions").stream()
            opinions = [doc.to_dict()["text"] for doc in opinions_ref]

            if not opinions:
                st.info("まだ投稿がありません。")
                st.stop()

            if show_all:
                st.markdown("### 📝 投稿された意見")
                for i, op in enumerate(opinions):
                    st.markdown(f"<div class='opinion-card'>{i+1}. {op}</div>", unsafe_allow_html=True)

            if st.button("🧐 AIで要約する"):
                with st.spinner("AIが意見をまとめています..."):
                    summary = summarize_opinions(opinions)
                st.markdown("### ✅ AIによるまとめ")
                st.success(summary)
        else:
            st.error("議題が見つかりませんでした。")
    else:
        st.warning("URLに `id` が必要です。")
