import pandas as pd
import numpy as np
import os

# FIX: Prevent Tkinter thread errors in Flask
import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import pickle


def create_mock_datasets():
    if not os.path.exists("train_dataset.xlsx") or not os.path.exists("test_dataset.xlsx"):
        print("Generating realistic datasets...")
        np.random.seed(42)
        n_samples = 500

        # Features
        age = np.random.randint(2, 12, n_samples)
        gender = np.random.choice(["Male", "Female", "Other"], n_samples)

        # Autism risk labels
        labels = np.random.binomial(1, 0.4, n_samples)

        # Behavioral features
        eye_contact = np.where(labels == 1, np.random.randint(6, 11, n_samples), np.random.randint(0, 6, n_samples))
        communication = np.where(labels == 1, np.random.randint(5, 11, n_samples), np.random.randint(0, 6, n_samples))
        behavior = np.where(labels == 1, np.random.randint(6, 11, n_samples), np.random.randint(1, 7, n_samples))
        social = np.where(labels == 1, np.random.randint(5, 11, n_samples), np.random.randint(0, 6, n_samples))

        # Add noise
        eye_contact = np.clip(eye_contact + np.random.randint(-1, 2, n_samples), 0, 10)
        communication = np.clip(communication + np.random.randint(-1, 2, n_samples), 0, 10)
        behavior = np.clip(behavior + np.random.randint(-1, 2, n_samples), 0, 10)
        social = np.clip(social + np.random.randint(-1, 2, n_samples), 0, 10)

        df = pd.DataFrame({
            "Age": age,
            "Gender": gender,
            "Eye_Contact": eye_contact,
            "Communication": communication,
            "Behavior": behavior,
            "Social_Interaction": social,
            "Risk": labels
        })

        df.to_excel("processed_data.xlsx", index=False)

        train_df, test_df = train_test_split(df, test_size=0.2, random_state=42)

        train_df.to_excel("train_dataset.xlsx", index=False)
        test_df.to_excel("test_dataset.xlsx", index=False)

        print("Datasets generated successfully.")


def train_and_evaluate_model():
    """Load dataset, train RandomForest model, evaluate and generate graphs"""
    
    create_mock_datasets()

    train_df = pd.read_excel("train_dataset.xlsx")
    test_df = pd.read_excel("test_dataset.xlsx")

    # ML Features
    X_train = train_df[["Age", "Eye_Contact", "Communication", "Behavior", "Social_Interaction"]]
    y_train = train_df["Risk"]

    X_test = test_df[["Age", "Eye_Contact", "Communication", "Behavior", "Social_Interaction"]]
    y_test = test_df["Risk"]

    model = RandomForestClassifier(n_estimators=100, random_state=42)

    model.fit(X_train, y_train)

    # Predictions
    train_pred = model.predict(X_train)
    test_pred = model.predict(X_test)

    train_acc = accuracy_score(y_train, train_pred) * 100
    test_acc = accuracy_score(y_test, test_pred) * 100

    # Save trained model
    with open("autism_rf_model.pkl", "wb") as f:
        pickle.dump(model, f)

    generate_machine_learning_graphs(train_acc, test_acc, train_df)


def generate_machine_learning_graphs(train_acc, test_acc, df):

    os.makedirs("outputs", exist_ok=True)

    # Accuracy Graph
    plt.figure(figsize=(6,4))
    plt.bar(
        ["Training Accuracy", "Validation Accuracy"],
        [train_acc, test_acc],
        color=['#1a56db', '#16a34a']
    )

    plt.title("Random Forest Model Accuracy")
    plt.ylim(0,110)

    for i,v in enumerate([train_acc, test_acc]):
        plt.text(i, v+2, f"{v:.1f}%", ha="center", fontweight="bold")

    plt.ylabel("Accuracy (%)")
    plt.tight_layout()

    plt.savefig("outputs/accuracy_graph.png")
    plt.close()

    # Dataset Distribution Pie Chart
    risk_count = df["Risk"].value_counts()

    plt.figure(figsize=(6,4))
    plt.pie(
        [risk_count.get(1,0), risk_count.get(0,0)],
        labels=["High Risk Profile","Low Risk Profile"],
        autopct="%1.1f%%",
        colors=["#dc2626","#16a34a"],
        startangle=90
    )

    plt.title("Training Dataset Distribution")
    plt.tight_layout()

    plt.savefig("outputs/prediction_results.png")
    plt.close()


def run_prediction(name, age, gender, eye_contact, communication, behavior, social):
    """Predict autism risk from user input"""

    if not os.path.exists("autism_rf_model.pkl"):
        train_and_evaluate_model()

    with open("autism_rf_model.pkl","rb") as f:
        model = pickle.load(f)

    input_data = pd.DataFrame([{
        "Age": age,
        "Eye_Contact": eye_contact,
        "Communication": communication,
        "Behavior": behavior,
        "Social_Interaction": social
    }])

    prediction = model.predict(input_data)[0]
    probabilities = model.predict_proba(input_data)[0]

    risk_prob = probabilities[1] if len(probabilities) > 1 else (1.0 if prediction == 1 else 0.0)

    confidence = round(risk_prob * 100, 2)

    if confidence >= 70:
        risk_status = "High Risk"

    elif confidence >= 40:
        risk_status = "Moderate Risk"

    else:
        risk_status = "Low Risk"
        confidence = round((1 - risk_prob) * 100, 2)

    return risk_status, confidence


def generate_mock_graphs():
    train_and_evaluate_model()


if __name__ == "__main__":
    train_and_evaluate_model()
    print("Model training complete.")