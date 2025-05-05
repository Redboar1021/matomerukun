from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def summarize_opinions(opinion_list):
    if not opinion_list:
        return "まだ意見がありません。"

    prompt = "以下は匿名の意見です。全体の傾向や主張を中立にまとめてください：\n\n" + "\n".join(opinion_list)

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "あなたは中立で公平な意見まとめの専門家です。"},
            {"role": "user", "content": prompt}
        ],
        max_tokens=500,
        temperature=0.7
    )

    return response.choices[0].message.content
