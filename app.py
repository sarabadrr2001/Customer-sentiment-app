from flask import Flask, render_template, request
from textblob import TextBlob
from deep_translator import GoogleTranslator
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import os

app = Flask(__name__)

# -----------------------------------------------------
# 🔹 دالة تحليل المشاعر (مع تعديل I don't like → Negative)
# -----------------------------------------------------
def analyze_text(feedback):

    # ترجمة النص لو عربي
    try:
        translated = GoogleTranslator(source="auto", target="en").translate(feedback)
    except:
        translated = feedback

    # تحسين القرار: تحويل جمل "I don't like" دائمًا لـ Negative
    lowered = translated.lower()
    if "don't like" in lowered or "dont like" in lowered or "didn't like" in lowered:
        return "Negative", -0.7, 15.0, translated

    # تحليل TextBlob
    blob = TextBlob(translated)
    score = blob.sentiment.polarity  # -1 إلى 1
    percentage = round((score + 1) / 2 * 100, 2)

    # تحديد نوع المشاعر
    if score > 0.1:
        sentiment = "Positive"
    elif score < -0.1:
        sentiment = "Negative"
    else:
        sentiment = "Neutral"

    return sentiment, score, percentage, translated



# -----------------------------------------------------
# 🔹 الصفحة الرئيسية
# -----------------------------------------------------
@app.route("/", methods=["GET", "POST"])
def home():
    single_result = None
    chart_generated = False
    excel_result = None
    excel_chart = False

    # -----------------------------------------------------
    # جزء تحليل الجملة الواحدة
    # -----------------------------------------------------
    if request.method == "POST" and "single_feedback" in request.form:
        feedback = request.form["single_feedback"]
        sentiment, score, percentage, translated = analyze_text(feedback)

        # رسم بياني لجملة واحدة
        labels = ["Positive", "Negative", "Neutral"]
        values = [
            100 if sentiment == "Positive" else 0,
            100 if sentiment == "Negative" else 0,
            100 if sentiment == "Neutral" else 0,
        ]
        colors = ["#4CAF50", "#E53935", "#FBC02D"]

        plt.figure(figsize=(4, 4))
        plt.bar(labels, values, color=colors)
        plt.title("Sentiment Result")
        plt.ylim(0, 100)

        chart_path = "static/images/single_chart.png"
        plt.savefig(chart_path)
        plt.close()

        chart_generated = True

        single_result = {
            "sentiment": sentiment,
            "score": round(score, 3),
            "percentage": percentage,
            "translated": translated
        }



    # -----------------------------------------------------
    # 🔹 جزء تحليل ملف Excel
    # -----------------------------------------------------
    if request.method == "POST" and "excel_file" in request.files:
        file = request.files["excel_file"]

        if file.filename != "":
            df = pd.read_excel(file)

            sentiments = []
            for text in df[df.columns[0]]:
                s, _, _, _ = analyze_text(str(text))
                sentiments.append(s)

            df["Sentiment"] = sentiments

            # حساب النسب:
            total = len(df)
            positive_count = (df["Sentiment"] == "Positive").sum()
            negative_count = (df["Sentiment"] == "Negative").sum()
            neutral_count = (df["Sentiment"] == "Neutral").sum()

            positive_pct = round((positive_count / total) * 100, 2)
            negative_pct = round((negative_count / total) * 100, 2)
            neutral_pct = round((neutral_count / total) * 100, 2)

            excel_result = {
                "positive": positive_pct,
                "negative": negative_pct,
                "neutral": neutral_pct
            }

            # الرسم البياني التجميعي
            count = df["Sentiment"].value_counts()
            plt.figure(figsize=(5, 4))
            count.plot(kind="bar", color=["#4CAF50", "#E53935", "#FBC02D"])
            plt.title("Overall Sentiment Summary")
            plt.ylabel("Count")

            chart_path = "static/images/excel_chart.png"
            plt.savefig(chart_path)
            plt.close()

            excel_chart = True


    # -----------------------------------------------------
    # 🔹 إرجاع النتائج للصفحة
    # -----------------------------------------------------
    return render_template(
        "index.html",
        single_result=single_result,
        chart_generated=chart_generated,
        excel_result=excel_result,
        excel_chart=excel_chart
    )


# -----------------------------------------------------
# 🔥 هذا السطر الصحيح للتشغيل والرفع
# -----------------------------------------------------
if __name__ == "_main_":
    app.run(host="0.0.0.0", port=10000)
