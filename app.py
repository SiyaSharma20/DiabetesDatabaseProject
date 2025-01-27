from flask import Flask, render_template, request
import mysql.connector
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64
import matplotlib
import plotly.graph_objects as go
import math
from matplotlib.ticker import FuncFormatter


# Use a non-GUI backend for Matplotlib
matplotlib.use("Agg")

app = Flask(__name__)

# Query 1: Average BMI
def query_average_bmi(gender_condition):
    try:
        db = mysql.connector.connect(
            host="localhost",
            port=3306,
            user="root",
            password="SiyaSharma1!",
            database="diabetes"
        )
        query = f"""
        SELECT AVG(Health_Status.BMI) AS Average_BMI
        FROM Health_Status
        JOIN Medical_and_Wellbeing ON Health_Status.Diabetes_ID = Medical_and_Wellbeing.Diabetes_ID
        JOIN Demographics ON Health_Status.Diabetes_ID = Demographics.Diabetes_ID
        WHERE Health_Status.HighChol = 1 
          AND (Medical_and_Wellbeing.HeartDisease = 1 OR Medical_and_Wellbeing.Stroke = 1)
          {gender_condition};
        """
        cursor = db.cursor(dictionary=True)
        cursor.execute(query)
        result = cursor.fetchone()
        db.close()
        return result['Average_BMI'] if result else None
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

# Query 2: Physical Activity Percentage
def query_physical_activity_percentage(gender_condition):
    try:
        db = mysql.connector.connect(
            host="localhost",
            port=3306,
            user="root",
            password="SiyaSharma1!",
            database="diabetes"
        )
        query = f"""
        SELECT 
            (SUM(CASE WHEN Lifestyle.PhysActivity = 1 THEN 1 ELSE 0 END) / COUNT(*)) * 100 AS PhysActivityPercentage
        FROM Diabetes_Status
        JOIN Lifestyle ON Diabetes_Status.Diabetes_ID = Lifestyle.Diabetes_ID
        JOIN Demographics ON Diabetes_Status.Diabetes_ID = Demographics.Diabetes_ID
        WHERE Diabetes_Status.Status = 2
        {gender_condition};
        """
        result = pd.read_sql(query, db)
        db.close()
        return result["PhysActivityPercentage"].iloc[0]
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

# General Utility Function
def fetch_filtered_data(query):
    try:
        db = mysql.connector.connect(
            host="localhost",
            port=3306,
            user="root",
            password="SiyaSharma1!",
            database="diabetes"
        )
        result = pd.read_sql(query, db)
        db.close()
        return result
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None


def generate_bmi_gauge(average_bmi):
    if average_bmi is None:
        return None

    # Determine the BMI category based on the value
    if average_bmi < 18.5:
        category = "Underweight"
    elif 18.5 <= average_bmi <= 24.9:
        category = "Healthy"
    elif 25 <= average_bmi <= 29.9:
        category = "Overweight"
    else:
        category = "Obese"

    # Create the gauge chart
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=average_bmi,
        number={ "font": {"size": 80},
        "valueformat" : ".2f",
        },  # Large font for BMI value
        title={"text": "Average BMI", "font": {"size": 24}},
        gauge={
            "axis": {"range": [10, 40], "tickwidth": 1, "tickcolor": "black"},
            "bar": {"color": "#FF6347"},
            "steps": [
                {"range": [10, 18.5], "color": "#ADD8E6"},  # Underweight
                {"range": [18.5, 24.9], "color": "#90EE90"},  # Healthy
                {"range": [25, 29.9], "color": "#FFD700"},  # Overweight
                {"range": [30, 40], "color": "#FF4500"},  # Obese
            ],
            "threshold": {
                "line": {"color": "red", "width": 4},
                "thickness": 0.75,
                "value": average_bmi,
            },
        }
    ))

    # Add text below the gauge, centered in the middle
    fig.add_annotation(
        text=f"<b>{category}</b>",  # Dynamic text (e.g., "Overweight")
        x=0.5,  # Center horizontally
        y=-0.05,  # Position below the gauge
        xref="paper",
        yref="paper",
        showarrow=False,
        font=dict(size=24, color="gray"),  # Customize font size and color
        align="center"
    )

    # Save the chart as a PNG image in memory
    img_bmi = io.BytesIO()
    fig.write_image(img_bmi, format="png", engine="kaleido")
    img_bmi.seek(0)

    # Encode the image in base64
    return base64.b64encode(img_bmi.getvalue()).decode("utf-8")
    #new stuff ends here



@app.route("/", methods=["GET", "POST"])
def display_graphs():
    # Filter for gender
    sex_filter = request.form.get("sex_filter", "")
    gender_condition = ""
    if sex_filter == "Male":
        gender_condition = "AND Demographics.Sex = 1"
    elif sex_filter == "Female":
        gender_condition = "AND Demographics.Sex = 0"

    # Query 1: Average BMI
    average_bmi = query_average_bmi(gender_condition)
    average_bmi = round(average_bmi, 2) if average_bmi else "No data available"
    #new for query 1 gauge chart
    bmi_gauge_chart_url = generate_bmi_gauge(average_bmi) if average_bmi else None


    # Query 2: Physical Activity Percentage
    physical_activity_percentage = query_physical_activity_percentage(gender_condition)
    physical_activity_percentage = round(physical_activity_percentage, 2) if physical_activity_percentage else "No data available"

    # Query 3: Education vs Smoking (Pie Chart)
    query_education_smoking = f"""
    SELECT Demographics.Education, Lifestyle.Smoker, COUNT(*) AS Count
    FROM Demographics
    JOIN Lifestyle ON Demographics.Diabetes_ID = Lifestyle.Diabetes_ID
    WHERE 1=1 {gender_condition}
    GROUP BY Demographics.Education, Lifestyle.Smoker
    ORDER BY Demographics.Education, Lifestyle.Smoker;
    """
    education_smoking_data = fetch_filtered_data(query_education_smoking)
    pivoted_data = education_smoking_data.pivot_table(index="Education", columns="Smoker", values="Count", fill_value=0)

    EDUCATION_LEVELS = {
    1: "No Schooling",
    2: "Grades 1-8",
    3: "Grades 9-11",
    4: "High School Graduate",
    5: "Some College",
    6: "College Graduate"
}

    charts = []
    counts = []
    for education_level, row in pivoted_data.iterrows():
        labels = ["Non-Smoker", "Smoker"]
        sizes = row.values
        colors = ["#87CEEB", "#FFA500"]
        explode = (0.05, 0)  # Slightly offset the first slice for emphasis
        plt.figure(figsize=(2, 2))  # Ensure consistent chart size
        plt.pie(
            sizes,
            labels=labels,
            autopct="%1.1f%%",
            startangle=140,
            colors=colors,
            explode=explode,
            textprops={"fontsize": 5},
            wedgeprops={"edgecolor": "white", "linewidth": 0.3},
        )
        #plt.title(f"Education Level {int(education_level)}", fontsize=6, pad=5, loc='center')
        buffer = io.BytesIO()
        plt.tight_layout()
        plt.savefig(buffer, format="png", dpi=150)
        buffer.seek(0)
        charts.append(base64.b64encode(buffer.getvalue()).decode("utf-8"))
        plt.close()

        counts.append({
            "education_level": EDUCATION_LEVELS.get(int(education_level), "Unknown"),
            "non_smoker_count": int(row[0]),
            "smoker_count": int(row[1]),
        })


    # Query 4: Income vs Healthcare Access
    INCOME_LEVELS = {
    1: "< 10K",
    2: "10K-15K",
    3: "15K-20K",
    4: "20K-25K",
    5: "25K-35K",
    6: "35K-50K",
    7: "50K-75K",
    8: "75K+"
    }
    
    query_income_healthcare_access = f"""
    SELECT Demographics.Income, AVG(Medical_and_Wellbeing.NoDoctor) AS Avg_No_Doctor
    FROM Demographics
    JOIN Medical_and_Wellbeing ON Demographics.Diabetes_ID = Medical_and_Wellbeing.Diabetes_ID
    WHERE 1=1 {gender_condition}
    GROUP BY Demographics.Income
    ORDER BY Demographics.Income;
    """
    income_healthcare_data = fetch_filtered_data(query_income_healthcare_access)

    img_income = io.BytesIO()
    plt.figure(figsize=(6, 3))
    
    # Replace integer income levels with descriptive labels for plotting
    income_labels = [INCOME_LEVELS.get(income, "Unknown") for income in income_healthcare_data["Income"]]

    # Convert the average values to percentages by multiplying by 100
    income_healthcare_data["Avg_No_Doctor"] *= 100  
    bars = plt.bar(income_labels, income_healthcare_data["Avg_No_Doctor"], color="coral")
    for bar in bars:
        value = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            value + 0.1,  # Position slightly above the bar
            f"{value:.2f}%",
            ha="center",
            fontsize=9
        )

    # Add % sign to the Y-axis
    def to_percent(y, _):
        return f"{y:.0f}%"

    plt.gca().yaxis.set_major_formatter(FuncFormatter(to_percent))

    plt.xticks(rotation=45, ha='right', fontsize=10)
    plt.title("Impact of Income on Healthcare Access")
    plt.tight_layout()
    plt.savefig(img_income, format="png")
    img_income.seek(0)
    income_chart_url = base64.b64encode(img_income.getvalue()).decode("utf-8")
    plt.close()

    # Query 5: Mental Health by Age
    query_mental_health_by_age = f"""
    SELECT Demographics.Age, AVG(Medical_and_Wellbeing.MentHlth) AS Avg_Mental_Health_Score
    FROM Demographics
    JOIN Medical_and_Wellbeing ON Demographics.Diabetes_ID = Medical_and_Wellbeing.Diabetes_ID
    WHERE 1=1 {gender_condition}
    GROUP BY Demographics.Age
    ORDER BY Demographics.Age;
    """
    mental_health_data = fetch_filtered_data(query_mental_health_by_age)

    img_mental = io.BytesIO()
    plt.figure(figsize=(6, 3))
    bars = plt.bar(mental_health_data["Age"], mental_health_data["Avg_Mental_Health_Score"], color="#5DADE2")
    for bar in bars:
        plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() - 0.5, f"{bar.get_height():.2f}", ha="center")
    plt.title("Average Mental Health Scores by Age")
    plt.tight_layout()
    plt.savefig(img_mental, format="png")
    img_mental.seek(0)
    mental_chart_url = base64.b64encode(img_mental.getvalue()).decode("utf-8")
    plt.close()

    return render_template(
        "graphs.html",
        average_bmi=average_bmi,
        physical_activity_percentage=physical_activity_percentage,
        charts=charts,
        counts=counts,
        income_chart_url=income_chart_url,
        mental_chart_url=mental_chart_url,
        zip=zip,
        sex_filter=sex_filter,
        bmi_gauge_chart_url=bmi_gauge_chart_url,

    )

if __name__ == "__main__":
    app.run(debug=True)