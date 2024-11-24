from flask import Flask, render_template
import mysql.connector
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)

# Function to fetch pie chart data (Query 3)
def query_education_smoking():
    db = mysql.connector.connect(
        host="localhost",
        port=3306,
        user="root",
        password="Arjun123!",
        database="diabetes"
    )
    query = """
    SELECT Demographics.Education, Lifestyle.Smoker, COUNT(*) AS Count
    FROM Demographics
    JOIN Lifestyle ON Demographics.Diabetes_ID = Lifestyle.Diabetes_ID
    GROUP BY Demographics.Education, Lifestyle.Smoker
    ORDER BY Demographics.Education, Lifestyle.Smoker;
    """
    result = pd.read_sql(query, db)
    db.close()
    return result

# Function to fetch bar chart data (Query 5)
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
def display_graphs():
    # Fetch data for pie charts (Query 3)
    education_smoking_data = query_education_smoking()

    # Pivot the data
    pivoted_data = education_smoking_data.pivot_table(
        index="Education", 
        columns="Smoker", 
        values="Count", 
        fill_value=0
    )

    # Generate pie charts and encode them as base64
    charts = []
    counts = []
    for education_level, row in pivoted_data.iterrows():
        labels = ["Non-Smoker", "Smoker"]
        sizes = row.values
        colors = ["#87CEEB", "#FFA500"]
        plt.figure(figsize=(2.5, 2.5))
        plt.pie(
            sizes, 
            labels=labels, 
            autopct="%1.1f%%", 
            startangle=140, 
            colors=colors, 
            textprops={'fontsize': 8}, 
            wedgeprops={'edgecolor': 'white', 'linewidth': 1.2}
        )
        plt.title(f"Education Level {int(education_level)}", fontsize=10, pad=15)
        buffer = io.BytesIO()
        plt.tight_layout()
        plt.savefig(buffer, format="png", dpi=150)
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        charts.append(image_base64)
        plt.close()

        counts.append({
            "education_level": int(education_level),
            "non_smoker_count": int(row[0]),
            "smoker_count": int(row[1])
        })

    # Fetch data for bar chart (Query 5)
    mental_health_data = query_mental_health_by_age()

    # Generate the bar graph
    img = io.BytesIO()
    plt.figure(figsize=(8, 4))
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
    bar_chart_url = base64.b64encode(img.getvalue()).decode('utf8')
    plt.close()

    # Render both visualizations on the webpage
    return render_template("graphs.html", charts=charts, counts=counts, zip=zip, bar_chart_url=bar_chart_url)

if __name__ == "__main__":
    app.run(debug=True)
