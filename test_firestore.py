import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore

# Firestoreの初期化（重複防止）
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase_key.json")
    firebase_admin.initialize_app(cred)
db = firestore.client()

# Streamlit UI
st.title("🧪 Firebase Firestore 動作テスト")

# トピックIDを入力
topic_id = st.text_input("議題ID（自由な英数字でOK）", value="test-topic")

# 意見の投稿
opinion = st.text_area("あなたの意見を入力")
if st.button("意見を送信"):
    db.collection("topics").document(topic_id).collection("opinions").add({
        "text": opinion
    })
    st.success("意見を投稿しました")

# 投稿済み意見の表示
if st.button("投稿された意見を表示"):
    docs = db.collection("topics").document(topic_id).collection("opinions").stream()
    opinions = [doc.to_dict()["text"] for doc in docs]
    if opinions:
        st.subheader("📋 投稿一覧")
        for i, op in enumerate(opinions):
            st.markdown(f"{i+1}. {op}")
    else:
        st.info("まだ意見がありません")

from summarize import summarize_opinions

def get_opinions(topic_id):
    docs = db.collection("topics").document(topic_id).collection("opinions").stream()
    return [doc.to_dict()["text"] for doc in docs]


if st.button("AIで意見をまとめる"):
    opinions = get_opinions(topic_id)
    summary = summarize_opinions(opinions)
    st.markdown("### 🤖 AIによるまとめ")
    st.write(summary)
