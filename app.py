from flask import Flask, render_template, request, redirect, url_for, session
import csv

app = Flask(__name__)
app.secret_key = 'replace_with_your_secret_key'  # Set a proper secret key

# Home route – landing page to start the questionnaire
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        session.clear()  # Clear previous responses, if any
        return redirect(url_for('question', q='age'))
    return render_template('index.html')

# Route to handle each interactive question (step-by-step)
@app.route('/question/<q>', methods=['GET', 'POST'])
def question(q):
    # List of questions and their prompts:
    QUESTIONS = {
        'age': 'What is your age?',
        'gender': 'What is your gender? (men/women/unisex)',
        'type': 'Do you want a designer perfume or a customized blend? (designer/customized)',
        'occasion': 'What is the occasion for which you want the perfume?',
        'mood': 'How would you describe your  mood?',
        'scents': 'What scents do you like? (e.g., citrus, floral, woody)',
        'personality': 'How would you describe your personality?'
    }
    if request.method == 'POST':
        # Save the answer for this question
        session[q] = request.form.get('answer')
        next_q = get_next_question(q)
        if next_q:
            return redirect(url_for('question', q=next_q))
        else:
            return redirect(url_for('result'))
    return render_template('question.html', question=q, prompt=QUESTIONS[q])

def get_next_question(current):
    # Order in which questions are asked
    order = ['age', 'gender', 'type', 'occasion', 'mood', 'scents', 'personality']
    try:
        idx = order.index(current)
        if idx + 1 < len(order):
            return order[idx + 1]
        else:
            return None
    except ValueError:
        return None

# Route to display the final recommendation/result
@app.route('/result')
def result():
    recommendation = get_recommendation(session)
    gender = session.get("gender", "").lower()
    # Theme color selection based on user gender:
    if gender == "men":
        theme = "blue"
    elif gender == "women":
        theme = "pink"
    else:
        theme = "purple"
    return render_template('result.html', recommendation=recommendation, theme=theme, answers=session)

def get_recommendation(answers):
    if answers.get('type', '').lower() == 'designer':
        perfumes = []
        try:
            with open('luxury_perfumes.csv', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    perfumes.append(row)
        except Exception as e:
            print("Error loading CSV file:", e)
            return {"error": "Failed to load perfumes data."}

        user_gender = answers.get("gender", "").strip().lower()
        user_occasion = answers.get("occasion", "").strip().lower()
        user_mood = answers.get("mood", "").strip().lower()
        # Split scents on common delimiters (comma, period)
        raw_scents = answers.get("scents", "").lower()
        user_scents = [s.strip() for s in raw_scents.replace('.', ',').split(',') if s.strip()]

        # First, filter by gender to ensure compatibility
        filtered_perfumes = []
        for perfume in perfumes:
            perfume_gender = perfume.get("Gender", "").strip().lower()
            # Allow if the perfume is explicitly for the chosen gender or is unisex.
            if user_gender == "men" and ("men" in perfume_gender or "unisex" in perfume_gender):
                filtered_perfumes.append(perfume)
            elif user_gender == "women" and ("women" in perfume_gender or "unisex" in perfume_gender):
                filtered_perfumes.append(perfume)
            # If user input isn't men/women explicitly, we can include every option.
            elif user_gender not in ["men", "women"]:
                filtered_perfumes.append(perfume)

        if not filtered_perfumes:
            return {"message": "No perfumes match your gender preference."}

        best_match = None
        best_score = -1

        for perfume in filtered_perfumes:
            score = 0

            # Gender is already filtered so you might even add bonus points:
            score += 2

            # Check Occasion – using simple substring matching
            perfume_occasion = perfume.get("Occasion", "").strip().lower()
            if user_occasion and user_occasion in perfume_occasion:
                score += 1

            # Check Mood – using the "Personality / Mood" column
            perfume_mood = perfume.get("Personality / Mood", "").strip().lower()
            if user_mood and user_mood in perfume_mood:
                score += 1

            # Check Scent Profile – iterate over each input scent keyword
            perfume_scent_profile = perfume.get("Scent Profile", "").strip().lower()
            for scent in user_scents:
                if scent in perfume_scent_profile:
                    score += 1

            if score > best_score:
                best_score = score
                best_match = perfume

        return best_match if best_match else {"message": "No matching perfume found."}

    else:
        # For a customized perfume blend:
        custom_notes = (f"Custom blend for a {answers.get('mood', 'neutral')} mood, "
                        f"infused with hints of {answers.get('scents', 'your favorite scents')}.")
        return {'Custom Perfume': custom_notes}


if __name__ == '__main__':
    app.run(debug=True)
