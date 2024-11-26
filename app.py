from flask import Flask, render_template
import mysql.connector
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)


#Query 1
def query_average_bmi():
    try:
        db = mysql.connector.connect(
            host="localhost",
            port=3306,
            user="root",
            password="SiyaSharma1!",
            database="diabetes"
        )
        query = """
        SELECT AVG(Health_Status.BMI) AS Average_BMI
        FROM Health_Status
        JOIN Medical_and_Wellbeing ON Health_Status.Diabetes_ID = Medical_and_Wellbeing.Diabetes_ID
        WHERE Health_Status.HighChol = 1 
          AND (Medical_and_Wellbeing.HeartDisease = 1 OR Medical_and_Wellbeing.Stroke = 1);
        """
        cursor = db.cursor(dictionary=True)
        cursor.execute(query)
        result = cursor.fetchone()
        db.close()

        # Return the average BMI
        return result['Average_BMI'] if result else None
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None


# Query 2: Percentage of individuals with diabetes who engage in regular physical activity
def query_physical_activity_percentage():
    db = mysql.connector.connect(
        host="localhost",
        port=3306,
        user="root",
        password="SiyaSharma1!",
        database="diabetes"
    )
    query = """
    SELECT 
        (SUM(CASE WHEN Lifestyle.PhysActivity = 1 THEN 1 ELSE 0 END) / COUNT(*)) * 100 AS PhysActivityPercentage
    FROM Diabetes_Status
    JOIN Lifestyle ON Diabetes_Status.Diabetes_ID = Lifestyle.Diabetes_ID
    WHERE Diabetes_Status.Status = 2;
    """
    result = pd.read_sql(query, db)
    db.close()
    return result["PhysActivityPercentage"].iloc[0]


# Query 3: Data for Pie Charts (Smokers vs Non-Smokers by Education)
def query_education_smoking():
    db = mysql.connector.connect(
        host="localhost",
        port=3306,
        user="root",
        password="SiyaSharma1!",
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

# Query 4: Impact of Income on Healthcare Access using "NoDoctor"
def query_income_healthcare_access():
    db = mysql.connector.connect(
        host="localhost",
        port=3306,
        user="root",
        password="SiyaSharma1!",
        database="diabetes"
    )
    query = """
    SELECT Demographics.Income, AVG(Medical_and_Wellbeing.NoDoctor) AS Avg_No_Doctor
    FROM Demographics
    JOIN Medical_and_Wellbeing ON Demographics.Diabetes_ID = Medical_and_Wellbeing.Diabetes_ID
    GROUP BY Demographics.Income
    ORDER BY Demographics.Income;
    """
    result = pd.read_sql(query, db)
    db.close()
    return result


# Query 5: Mental Health Scores by Age
def query_mental_health_by_age():
    db = mysql.connector.connect(
        host="localhost",
        port=3306,
        user="root",
        password="SiyaSharma1!",
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
    
    #Query 1: 
    average_bmi = query_average_bmi()
    if average_bmi is None:
        average_bmi = "No data available"
    else:
        average_bmi = round(average_bmi, 2)


     #Query 2: percentage of physical activity
    physical_activity_percentage = query_physical_activity_percentage()
   
    # Query 3: Pie Charts (Education vs Smoking)
    education_smoking_data = query_education_smoking()
    pivoted_data = education_smoking_data.pivot_table(
        index="Education", 
        columns="Smoker", 
        values="Count", 
        fill_value=0
    )
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

    # Query 4: Bar Chart (Income vs NoDoctor)
    income_healthcare_data = query_income_healthcare_access()

    img_income = io.BytesIO()
    plt.figure(figsize=(6, 3))
    bars = plt.bar(
        income_healthcare_data["Income"],
        income_healthcare_data["Avg_No_Doctor"],
        color="coral",
        edgecolor="black"
    )

   # Add values to the bars dynamically
    for bar in bars:
        height = bar.get_height()
        if height < 0.2:  # Place above if the bar is tall enough
            plt.text(
                bar.get_x() + bar.get_width() / 2,
                height + 0.005,
                f"{height:.2f}",
                ha="center", va="bottom", fontsize=8
            )
        else:  # Place inside the bar if it's too short
            plt.text(
                bar.get_x() + bar.get_width() / 2,
                height - 0.005,
                f"{height:.2f}",
                ha="center", va="top", fontsize=8
            )

    plt.title("Impact of Income on Healthcare Access", fontsize=12)
    plt.xlabel("Income Levels", fontsize=10)
    plt.ylabel("Average 'NoDoctor' Count", fontsize=10)
    plt.xticks(income_healthcare_data["Income"], rotation=45, fontsize=8)
    plt.grid(axis="y", linestyle="--", alpha=0.7)
    plt.tight_layout()
    plt.savefig(img_income, format="png")
    img_income.seek(0)
    income_chart_url = base64.b64encode(img_income.getvalue()).decode("utf8")
    plt.close()



    # Query 5: Bar Chart (Mental Health Scores by Age)
    mental_health_data = query_mental_health_by_age()

    img_mental = io.BytesIO()
    plt.figure(figsize=(6, 3))
    bars = plt.bar(
        mental_health_data["Age"],
        mental_health_data["Avg_Mental_Health_Score"],
        color="#5DADE2",
        edgecolor="black"
    )

    # Add values to the bars dynamically
    for bar in bars:
        height = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            height - 0.1,
            f"{height:.2f}",
            ha="center", va="top", fontsize=8, color="black"
        )

    plt.title("Average Mental Health Scores by Age", fontsize=12)
    plt.xlabel("Age", fontsize=10)
    plt.ylabel("Average Mental Health Score", fontsize=10)
    plt.xticks(mental_health_data["Age"], rotation=45, fontsize=8)
    plt.grid(axis="y", linestyle="--", alpha=0.7)
    plt.tight_layout()
    plt.savefig(img_mental, format="png")
    img_mental.seek(0)
    mental_health_chart_url = base64.b64encode(img_mental.getvalue()).decode("utf8")
    plt.close()


    # Render all visualizations
    return render_template(
        "graphs.html",
        charts=charts,
        counts=counts,
        zip=zip,
        bar_chart_url=mental_health_chart_url,
        income_chart_url=income_chart_url,
        physical_activity_percentage=round(physical_activity_percentage, 2),
        average_bmi=average_bmi


    )

if __name__ == "__main__":
    app.run(debug=True)
