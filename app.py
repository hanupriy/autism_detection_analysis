import os
from flask import Flask, render_template, request, send_file, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors

# Import the mock prediction function
from autism_chatbot_gui import run_prediction, create_mock_datasets, generate_mock_graphs

app = Flask(__name__)

# Ensure required directories exist
os.makedirs("outputs", exist_ok=True)
os.makedirs("reports/generated_pdf_reports", exist_ok=True)
create_mock_datasets()
generate_mock_graphs()

app.secret_key = "super_secret_key_for_neuroscreen"

# Initialize SQLite DB
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL,
                  phone TEXT UNIQUE NOT NULL,
                  password TEXT NOT NULL)''')
    conn.commit()
    conn.close()

init_db()

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name")
        phone = request.form.get("phone")
        password = request.form.get("password")
        
        hashed_pw = generate_password_hash(password)
        
        try:
            conn = sqlite3.connect('users.db')
            c = conn.cursor()
            c.execute("INSERT INTO users (name, phone, password) VALUES (?, ?, ?)", (name, phone, hashed_pw))
            conn.commit()
            conn.close()
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash("Phone number already registered. Please login.", "danger")
            
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        phone = request.form.get("phone")
        password = request.form.get("password")
        
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("SELECT id, name, password FROM users WHERE phone = ?", (phone,))
        user_row = c.fetchone()
        conn.close()
        
        if user_row and check_password_hash(user_row[2], password):
            session['user_id'] = user_row[0]
            session['user_name'] = user_row[1]
            flash(f"Welcome back, {user_row[1]}!", "success")
            return redirect(url_for('screening'))
        else:
            flash("Invalid phone number or password.", "danger")
            
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

@app.route("/screening", methods=["GET"])
@login_required
def screening():
    return render_template("screening.html")

@app.route("/predict", methods=["POST"])
@login_required
def predict():
    # Extract form data
    name = request.form.get("patient_name", "Unknown Patient")
    age = int(request.form.get("age", 0))
    gender = request.form.get("gender", "Unknown")
    
    # Extract behavioral scores
    eye_contact = int(request.form.get("eye_contact", 0))
    communication = int(request.form.get("communication", 0))
    behavior = int(request.form.get("behavior", 0))
    social = int(request.form.get("social", 0))
    
    # Run prediction model
    risk_status, confidence = run_prediction(name, age, gender, eye_contact, communication, behavior, social)
    
    if risk_status == "High Risk":
        treatment = "Intensive therapy, medical intervention, and extensive caregiver support. Consult a pediatric developmental specialist immediately for a formal diagnosis. Highly recommend early intensive behavioral intervention (like ABA)."
    elif risk_status == "Moderate Risk":
        treatment = "Special education programs, social skills training, and continuous monitoring. Consider targeted speech or occupational therapy based on specific behavioral challenges."
    else:
        treatment = "Continue regular pediatric developmental checkups. Engage in interactive play and monitor developmental milestones. Early behavioral therapy and speech therapy can be considered if mild concens persist."
        
    # Prepare result data
    result_data = {
        "name": name,
        "age": age,
        "gender": gender,
        "risk_status": risk_status,
        "confidence": confidence,
        "treatment": treatment,
        "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Generate PDF Report automatically
    pdf_filename = generate_pdf_report(result_data)
    result_data["pdf_filename"] = pdf_filename
    
    # Render Result template
    return render_template("result.html", result=result_data)

@app.route("/download/<filename>")
def download_pdf(filename):
    filepath = os.path.join("reports", "generated_pdf_reports", filename)
    return send_file(filepath, as_attachment=True)

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message", "").lower()
    response = ""
    
    # Simple rule-based chatbot logic
    if "hello" in user_message or "hi" in user_message:
        response = "Hello! I am the NeuroScreen assistant. I can help answer questions about autism traits, behavioral scoring (0-10), and the assessment process."
    
    elif "eye contact" in user_message:
        response = "Eye contact score (0-10): Rate the level of difficulty the child has with eye contact. 0 = Typical/appropriate eye contact. 5 = Occasional difficulty or fleeting contact. 10 = Consistently avoids or struggles with eye contact."
        
    elif "communication" in user_message:
        response = "Communication score (0-10): Rate the level of communication challenges. 0 = Typical communication for their age. 5 = Mild delays or struggles. 10 = Significant delays, echolalia, or non-verbal."
        
    elif "behavior" in user_message:
        response = "Behavior score (0-10): Rate the presence of repetitive/restrictive behaviors. 0 = No significant repetitive behaviors. 5 = Occasional repetitive behaviors. 10 = Frequent and intense repetitive behaviors (e.g., hand-flapping, rocking)."
        
    elif "social" in user_message:
        response = "Social Interaction score (0-10): Rate the level of difficulty with social interaction. 0 = Actively seeks and enjoys interactions. 5 = Sometimes struggles to initiate or sustain play. 10 = Rarely responds to name, prefers isolation, struggles with peers."
        
    elif "autism" in user_message or "asd" in user_message:
        response = "Autism Spectrum Disorder (ASD) is a developmental disability that can cause significant social, communication and behavioral challenges. Early diagnosis and intervention can have a significant positive impact."
        
    elif "treatment" in user_message or "therapy" in user_message:
        response = "Recommended treatments often include Behavioral Therapies (like ABA), Speech-Language Therapy, Occupational Therapy, and sometimes specialized educational support. Always consult a medical professional for a personalized plan."
        
    elif "score" in user_message:
        response = "The behavioral scores are on a scale of 0 to 10, representing the SEVERITY of the traits. A lower score (closer to 0) indicates typical development (low risk). A higher score (closer to 10) indicates a strong presence of autism-related traits (high risk)."
        
    elif "accuracy" in user_message or "model" in user_message:
        response = "This screening tool uses a Random Forest Machine Learning model. It was trained on clinical parameters to identify patterns corresponding to ASD traits. You can view the accuracy graph on the home page."
        
    elif "age" in user_message:
        response = "Autism traits can be observed as early as 18 months of age, but a reliable diagnosis by an experienced professional can typically be made by age 2. This screening algorithm is designed for ages 2 to 12."
        
    elif "gender" in user_message or "boy" in user_message or "girl" in user_message:
        response = "ASD is diagnosed approximately 4 times more often in boys than in girls. However, research suggests that girls may present traits differently or 'mask' them, leading to under-diagnosis."
        
    elif "cause" in user_message or "why" in user_message:
        response = "There is no single known cause for autism. Research suggests it develops from a combination of genetic and non-genetic, or environmental, influences. Vaccines DO NOT cause autism."
        
    elif "cure" in user_message:
        response = "There is no 'cure' for Autism Spectrum Disorder, and many advocates emphasize that autism is a natural variation of human neurology (neurodiversity). Therapies focus on improving quality of life and supporting development."
        
    elif "pdf" in user_message or "report" in user_message:
        response = "Once you complete the screening form, the system will automatically generate a downloadable PDF report containing the prediction, confidence score, and tailored recommendations."
        
    elif "contact" in user_message or "doctor" in user_message:
        response = "If the screening result indicates a 'High Risk' or 'Moderate Risk', it is highly recommended to schedule an appointment with a pediatrician, child psychologist, or pediatric neurologist for a formal evaluation."
        
    elif "help" in user_message or "questions" in user_message:
        response = ("Here are some topics you can ask me about:<br>"
                    "• <b>Scoring guidance:</b> Ask about 'eye contact', 'communication', 'behavior', 'social', or general 'scoring'.<br>"
                    "• <b>Autism info:</b> Ask about 'autism', 'treatments', 'age', 'gender', 'causes', or 'cure'.<br>"
                    "• <b>Technical info:</b> Ask about the 'model accuracy' or the 'PDF report'.")
        
    else:
        response = ("I'm a simple assistant. Ask me for 'help' or 'questions' to see a list of topics I understand, such as 'treatments', 'causes', or how to score 'behavior'!")
        
    return {"reply": response}

@app.route("/outputs/<filename>")
def serve_output(filename):
    filepath = os.path.join("outputs", filename)
    return send_file(filepath)

def generate_pdf_report(data):
    # Generates a personalized PDF report
    filename = f"Report_{data['name'].replace(' ', '_')}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
    filepath = os.path.join("reports", "generated_pdf_reports", filename)
    
    c = canvas.Canvas(filepath, pagesize=letter)
    width, height = letter
    
    # Header
    c.setFont("Helvetica-Bold", 24)
    c.drawString(50, height - 50, "Autism Prediction Screening Report")
    
    # Patient Info section
    c.setFont("Helvetica", 14)
    c.drawString(50, height - 100, f"Patient Name: {data['name']}")
    c.drawString(50, height - 120, f"Age: {data['age']}")
    c.drawString(50, height - 140, f"Gender: {data['gender']}")
    c.drawString(50, height - 160, f"Date Code: {data['date']}")
    
    # Result section
    c.setFont("Helvetica-Bold", 16)
    if data['risk_status'] == "High Risk":
        c.setFillColor(colors.red)
    elif data['risk_status'] == "Moderate Risk":
        c.setFillColor(colors.orange)
    else:
        c.setFillColor(colors.green)
        
    c.drawString(50, height - 200, f"Prediction Result: {data['risk_status']}")
    
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 14)
    c.drawString(50, height - 230, f"Confidence Score: {data['confidence']}%")
    
    # Treatment recommendations
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 260, "Recommended Actions:")
    c.setFont("Helvetica", 12)
    
    text_obj_treat = c.beginText(50, height - 280)
    for line in simple_wrap(data['treatment'], 80):
        text_obj_treat.textLine(line)
    c.drawText(text_obj_treat)
    
    # Summary paragraph
    c.setFont("Helvetica-Oblique", 12)
    summary_text = f"Based on the provided behavioral scores and patient details, the machine learning model indicates a '{data['risk_status']}' with a confidence level of {data['confidence']}%. Please note that this is a screening tool and should be verified by a medical professional."
    
    # Break summary_text into multiple lines
    text_obj = c.beginText(50, height - 350)
    for line in simple_wrap(summary_text, 80):
        text_obj.textLine(line)
    c.drawText(text_obj)
    
    c.save()
    return filename

def simple_wrap(text, width):
    words = text.split()
    lines = []
    current_line = []
    current_length = 0
    
    for word in words:
        if current_length + len(word) > width:
            lines.append(" ".join(current_line))
            current_line = [word]
            current_length = len(word)
        else:
            current_line.append(word)
            current_length += len(word) + 1
            
    if current_line:
        lines.append(" ".join(current_line))
    return lines

if __name__ == "__main__":
    app.run(debug=True)
