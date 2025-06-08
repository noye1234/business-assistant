from flask import Flask, request, jsonify, send_file
import json
import os
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from openai import OpenAI

# Get OpenAI API key from environment variable
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize Flask app
app = Flask(__name__)

# Route for serving index.html
@app.route('/')
def index():
    return send_file('static/index.html')

# Route for matching requirements
@app.route('/match-requirements', methods=['POST'])
def match_requirements():
    user_data = request.get_json()
    size = user_data.get('size')
    seats = user_data.get('seats')
    features = user_data.get('features', [])

    # Load rules from JSON file
    with open('output/rules.json', 'r', encoding='utf-8') as f:
        rules_data = json.load(f)
    rules = rules_data.get("rules", [])

    matched_requirements = []
    for rule in rules:
        conditions_list = rule.get('conditions', None)
        if not conditions_list:
            continue

        # Check if any condition is met
        match = any(
            (('size_greater_than' in cond and size is not None and size > cond['size_greater_than'])
            or ('seats_greater_than' in cond and seats is not None and seats > cond['seats_greater_than'])
            or ('feature' in cond and cond['feature'] in features))
            for cond in conditions_list
        )

        if match:
            matched_requirements.append(rule.get('requirement', ''))

    # Generate AI report if API key exists
    if OPENAI_API_KEY:
        client = OpenAI(api_key=OPENAI_API_KEY)

        def generate_ai_report(user_data, matched_requirements):
            prompt = f"""
            יש לי את המידע הבא על עסק:
            - גודל העסק: {user_data.get('size')} מ"ר
            - מספר מקומות ישיבה: {user_data.get('seats')}
            - מאפיינים נוספים: {', '.join(user_data.get('features', []))}

            הדרישות הרגולטוריות שנמצאו עבור העסק הן:
            {chr(10).join(matched_requirements)}

            אנא צור דוח ברור בעברית שמסביר בקצרה ובשפה נגישה את הדרישות הרלוונטיות, מסודר לפי קטגוריות והמלצות פעולה.
            """
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "אתה עוזר מקצועי שעוזר לבעלי עסקים להבין רגולציות."},
                    {"role": "user", "content": prompt}
                ]
            )
            report_text = response.choices[0].message.content.strip()
            return report_text

    # Generate PDF report
    if matched_requirements:
        pdf_path = 'output/report.pdf'
        c = canvas.Canvas(pdf_path)

        # Register Hebrew font
        pdfmetrics.registerFont(TTFont('Arial', 'static/fonts/Arial.ttf'))
        c.setFont("Arial", 14)

        # Write title (reversed for RTL workaround)
        title = "דו\"ח דרישות מותאם אישית לעסק שלך:"
        c.drawRightString(500, 800, title[::-1])

        # Write each requirement (reversed for RTL)
        y = 770
        for req in matched_requirements:
            text = f"- {req}"
            c.drawRightString(500, y, text[::-1])
            y -= 20

        c.save()
        download_link = "/download-report"
    else:
        download_link = None

    # Return matched requirements and download link as JSON
    return jsonify({
        'matched_requirements': matched_requirements,
        'download_link': download_link
    })

# Route for downloading the PDF report
@app.route('/download-report')
def download_report():
    pdf_path = 'output/report.pdf'
    if os.path.exists(pdf_path):
        return send_file(pdf_path, as_attachment=True)
    return "לא נמצא דוח להורדה.", 404

# Run Flask app
if __name__ == '__main__':
    app.run(debug=True)
