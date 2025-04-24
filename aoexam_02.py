import streamlit as st
from openai import OpenAI

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.title("大学志望理由 作成サポートAI")

st.subheader("✏️ ヒアリングフォーム")

# --- 入力項目 ---
name = st.text_input("氏名")
school = st.text_input("出身高校・学年")
university = st.text_input("志望大学")
faculty = st.text_input("志望学部・学科")
words = st.number_input("最大文字数", min_value=0, max_value=3000, step=1, format="%d")
reason = st.text_area("志望動機（きっかけ・エピソードなど）")
activities = st.text_area("学校や課外活動での経験")
future = st.text_area("将来の夢や目標")
strengths = st.text_area("自分の強み・アピールポイント")

if st.button("AIで志望理由を生成"):
    with st.spinner("生成中..."):

        prompt = f"""
あなたは日本の大学受験のエッセイ指導の専門家です。
以下の情報に基づいて、志望理由書の下書きを日本語で{words * 0.9}から{words}文字で作成してください。

【氏名】{name}
【高校・学年】{school}
【志望大学】{university}
【志望学部・学科】{faculty}
【きっかけ・動機】{reason}
【活動経験】{activities}
【将来の夢】{future}
【強み・性格】{strengths}

「拝啓、時下ますます…」や「敬具」などは不要です。書かないでください。
文体は、「ですます調」ではなく、「である調」で記述してください。
構成は、以下の順で、構築してください。
1) やりたいこと・目標
2) それをやりたい理由・経緯
3) これまでにやってきたこと
4) 大学でやりたいこと
5) その大学でなければいけない理由
全体を自然なストーリーで一貫させ、志望理由として読みやすくしてください。
"""

        chat_completion = client.chat.completions.create(
            model="gpt-4-turbo",  # または "gpt-3.5-turbo"
            messages=[
                {"role": "system", "content": "あなたは日本語エッセイ指導のプロです。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
        )

        st.success("生成完了！")
        st.text_area(
            "📄 生成された志望理由書（下書き）",
            value=chat_completion.choices[0].message.content,
            height=400
        )
