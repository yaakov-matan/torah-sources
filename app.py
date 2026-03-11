import os
import anthropic
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder=".")
CORS(app)

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """אתה אוצר של ציטוטים מכתבי הגות יהודית, מקורות קלאסיים ושירה יהודית.
תפקידך הוא לבחור ציטוט אחד מקורי, ככתבו וכלשונו, ממקורות יהודיים אמיתיים.

מקורות אפשריים — טקסטים קלאסיים (כפי שמופיעים בספריא sefaria.org.il):
תנ"ך, משנה, תלמוד בבלי, תלמוד ירושלמי, מדרש רבה, זוהר, משנה תורה לרמב"ם,
ספר החינוך, שולחן ערוך, תניא, פרי מגדים, מסילת ישרים, נפש החיים, וכדומה.

מקורות אפשריים — הוגים ומשוררים מודרניים:
הרב יהונתן זקס, הרב אברהם יצחק הכהן קוק, אברהם יהושע השל,
מרטין בובר, עמנואל לוינס, ש"י עגנון, ביאליק, נתן אלתרמן,
רחל המשוררת, לאה גולדברג, זלדה, יהודה עמיחי, אבות ישורון, וכדומה.

כאשר המשתמש שואל שאלה, אתה מוצא ציטוט מקורי ורלוונטי שמדבר אל השאלה —
בין אם מהמסורת הקלאסית ובין אם מהגות ושירה מודרנית.

פורמט תשובתך חייב להיות תמיד כך בדיוק — שלושה חלקים מופרדים בשורות ריקות:

[הציטוט המקורי המלא, ככתבו וכלשונו]

[שם המחבר / שם הספר]

[שם היצירה / פרק ופסוק / מקטע מדויק]

חוקים:
- הציטוט חייב להיות אמיתי ומדויק — לא פרפרזה ולא שחזור חופשי
- אל תוסיף הסברים, פרשנויות או מבוא לפני הציטוט
- אל תסיים את תשובתך בהסבר אחרי הציטוט
- אם אינך בטוח במקור המדויק, בחר ציטוט שאתה בטוח בו
- הציטוט יכול להיות בעברית, ביידיש, ארמית, או בתרגום ממקור אנגלי/גרמני
- כאשר מדובר בתרגום, ציין: "תרגום מאנגלית" / "תרגום מגרמנית" וכו'
- בחר ציטוטים עמוקים, מרגשים ורלוונטיים לשאלה
- ניתן למצוא טקסטים קלאסיים רבים בספריא: sefaria.org.il"""


@app.route("/")
def serve_index():
    return send_from_directory(".", "quotes.html")


@app.route("/api/quote", methods=["POST"])
def get_quote():
    data = request.get_json()
    if not data or "question" not in data:
        return jsonify({"error": "חסרה שאלה"}), 400

    question = data["question"].strip()
    if not question:
        return jsonify({"error": "השאלה ריקה"}), 400

    try:
        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": question}],
        )

        full_text = response.content[0].text.strip()
        parts = [p.strip() for p in full_text.split("\n\n") if p.strip()]

        quote = parts[0] if len(parts) > 0 else full_text
        author = parts[1] if len(parts) > 1 else ""
        source = parts[2] if len(parts) > 2 else ""

        return jsonify({"quote": quote, "author": author, "source": source})

    except anthropic.AuthenticationError:
        return jsonify({"error": "שגיאת אימות — בדוק את מפתח ה-API"}), 401
    except anthropic.RateLimitError:
        return jsonify({"error": "חריגה ממגבלת בקשות — נסה שוב בעוד רגע"}), 429
    except anthropic.APIError as e:
        return jsonify({"error": f"שגיאת API: {str(e)}"}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
