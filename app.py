from flask import Flask, request, jsonify, send_from_directory
import json

app = Flask(__name__)

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

def check_condition(cond, size, seats, features):
    # בדיקת גודל
    if 'size_greater_than' in cond:
        if size is None or size <= cond['size_greater_than']:
            return False

    # בדיקת מקומות ישיבה
    if 'seats_greater_than' in cond:
        if seats is None or seats <= cond['seats_greater_than']:
            return False

    # בדיקת מאפיין
    if 'feature' in cond:
        if cond['feature'] not in features:
            return False

    return True

@app.route('/match-requirements', methods=['POST'])
def match_requirements():
    user_data = request.get_json()
    size = user_data.get('size')
    seats = user_data.get('seats')
    features = user_data.get('features', [])

    with open('output/rules.json', 'r', encoding='utf-8') as f:
        rules_data = json.load(f)
    rules = rules_data.get("rules", [])

    matched_requirements = []
    for rule in rules:
        conditions_list = rule.get('conditions', None)
        if not conditions_list:
            continue  # אין תנאים בכלל? מדלגים

        # עכשיו - מספיק שאחד מהם מתקיים!
        match = False
        for cond in conditions_list:
            if 'size_greater_than' in cond:
                if size is not None and size > cond['size_greater_than']:
                    match = True
                    break
            if 'seats_greater_than' in cond:
                if seats is not None and seats > cond['seats_greater_than']:
                    match = True
                    break
            if 'feature' in cond:
                if cond['feature'] in features:
                    match = True
                    break

        if match:
            matched_requirements.append(rule.get('requirement', ''))

    return jsonify({'matched_requirements': matched_requirements})


if __name__ == '__main__':
    app.run(debug=True)
