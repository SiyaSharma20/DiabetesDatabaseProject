from flask import Flask, render_template
import mysql.connector
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)

# Function to fetch data from MySQL
def query_mental_health_by_age():
    db = mysql.connector.connect(
        host="localhost",
        port=3306,
        user="root",
        password="Arjun123!",
        database="diabetes"
    )
    query = """
    SELECT Demographics.Age, AVG(Medical_and_Wellbeing.MentHlth) AS Avg_Mental_Health_Score
    FROM Demographics
    JOIN Medical_and_Wellbeing ON Demographics.Diabetes_ID = Medical_and_Wellbeing.Diabetes_ID
    JOIN Diabetes_Status ON Demographics.Diabetes_ID = Diabetes_Status.Diabetes_ID
    WHERE Diabetes_Status.Status = 2
    GROUP BY Demographics.Age
    ORDER BY Demographics.Age;
    """
    result = pd.read_sql(query, db)
    db.close()
    return result

@app.route("/")
def display_graph():
    # Fetch data from the database
    mental_health_data = query_mental_health_by_age()

    # Generate the bar graph
    img = io.BytesIO()
    plt.figure(figsize=(12, 8))
    plt.bar(
        mental_health_data["Age"],
        mental_health_data["Avg_Mental_Health_Score"],
        color="skyblue",
        edgecolor="black"
    )
    plt.title("Average Mental Health Scores by Age (Diabetic Patients)", fontsize=16)
    plt.xlabel("Age", fontsize=12)
    plt.ylabel("Average Mental Health Score", fontsize=12)
    plt.xticks(mental_health_data["Age"], rotation=45, fontsize=10)
    plt.grid(axis="y", linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig(img, format='png')
    img.seek(0)
    graph_url = base64.b64encode(img.getvalue()).decode('utf8')
    plt.close()

    # Render the graph on the webpage
    return render_template("graph.html", graph_url=graph_url)

if __name__ == "__main__":
    app.run(debug=True)
