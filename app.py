from flask import Flask, render_template, request
import mysql.connector
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64
import matplotlib

# Use a non-GUI backend for Matplotlib
matplotlib.use("Agg")

app = Flask(__name__)

# Database connection function
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="SiyaSharma1!",
        database="diabetes"
    )

# Query data for the prediction model
def fetch_data_for_model():
    try:
        db = get_db_connection()
        
        query = """
        SELECT 
            HighBP, HighChol, CholCheck, BMI, Smoker, Stroke,
            HeartDisease AS HeartDiseaseorAttack, PhysActivity, Fruits, Veggies,
            HighAlcoholConsumption AS HvyAlcoholConsump, 
            NoDoctor AS NoDocbcCost, GenHlth,
            MentHlth, PhysHlth, DiffWalk, Sex, Age, Education, Income, Status AS Diabetes_012
        FROM Health_Status
        JOIN Medical_and_Wellbeing ON Health_Status.Diabetes_ID = Medical_and_Wellbeing.Diabetes_ID
        JOIN Lifestyle ON Health_Status.Diabetes_ID = Lifestyle.Diabetes_ID
        JOIN Demographics ON Health_Status.Diabetes_ID = Demographics.Diabetes_ID
        JOIN Diabetes_Status ON Health_Status.Diabetes_ID = Diabetes_Status.Diabetes_ID
        """
        data = pd.read_sql(query, db)
        db.close()
        return data
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

# Train the model once at the start of the application
try:
    diabetes_data = fetch_data_for_model()
    if diabetes_data is None or diabetes_data.empty:
        raise ValueError("Unable to fetch data from the database or database is empty.")
    X = diabetes_data.drop(columns=["Diabetes_012"])
    y = diabetes_data["Diabetes_012"]
    X_const = sm.add_constant(X)
    model = sm.MNLogit(y, X_const).fit()
except Exception as e:
    print(f"Error while training the model: {e}")
    model = None

# Predict the diabetes outcome
def predict_diabetes(user_input):
    if model is None:
        return "Model is not available. Please check the database connection or training process."

    # Prepare user input
    user_input_df = pd.DataFrame([user_input])
    user_input_const = sm.add_constant(user_input_df, has_constant='add')
    
    # Predict probabilities
    predicted_probabilities = model.predict(user_input_const)
    
    # Classify the prediction
    predicted_class = np.argmax(predicted_probabilities.values[0])
    return ["No Diabetes", "Pre-Diabetes", "Diabetes"][predicted_class]

def map_age_to_category(age):
    """
    Map actual age to the corresponding age category for the model.
    """
    if age < 18:
        raise ValueError("Age must be 18 or older.")
    if 18 <= age <= 24:
        return 0
    elif 25 <= age <= 29:
        return 1
    elif 30 <= age <= 34:
        return 2
    elif 35 <= age <= 39:
        return 3
    elif 40 <= age <= 44:
        return 4
    elif 45 <= age <= 49:
        return 5
    elif 50 <= age <= 54:
        return 6
    elif 55 <= age <= 59:
        return 7
    elif 60 <= age <= 64:
        return 8
    elif 65 <= age <= 69:
        return 9
    elif 70 <= age <= 74:
        return 10
    elif 75 <= age <= 79:
        return 11
    else:  # 80+
        return 12


# Query 1: Average BMI
def query_average_bmi(gender_condition):
    try:
        db = mysql.connector.connect(
            host="localhost",
            port=3306,
            user="root",
            password="Arjun123!",
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
            password="Arjun123!",
            database="diabetes"
        )
        # Query for overall percentage
        overall_query = f"""
        SELECT 
            (SUM(CASE WHEN Lifestyle.PhysActivity = 1 THEN 1 ELSE 0 END) / COUNT(*)) * 100 AS PhysActivityPercentage
        FROM Diabetes_Status
        JOIN Lifestyle ON Diabetes_Status.Diabetes_ID = Lifestyle.Diabetes_ID
        JOIN Demographics ON Diabetes_Status.Diabetes_ID = Demographics.Diabetes_ID
        WHERE Diabetes_Status.Status = 2
        {gender_condition};
        """
        overall_result = pd.read_sql(overall_query, db)["PhysActivityPercentage"].iloc[0]

        # Query for percentage by age group
        age_group_query = f"""
        SELECT Demographics.Age, 
               (SUM(CASE WHEN Lifestyle.PhysActivity = 1 THEN 1 ELSE 0 END) / COUNT(*)) * 100 AS PhysActivityPercentage
        FROM Diabetes_Status
        JOIN Lifestyle ON Diabetes_Status.Diabetes_ID = Lifestyle.Diabetes_ID
        JOIN Demographics ON Diabetes_Status.Diabetes_ID = Demographics.Diabetes_ID
        WHERE Diabetes_Status.Status = 2
        {gender_condition}
        GROUP BY Demographics.Age
        ORDER BY Demographics.Age;
        """
        age_group_result = pd.read_sql(age_group_query, db)
        db.close()

        return overall_result, age_group_result
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None, None

# General Utility Function
def fetch_filtered_data(query):
    try:
        db = mysql.connector.connect(
            host="localhost",
            port=3306,
            user="root",
            password="Arjun123!",
            database="diabetes"
        )
        result = pd.read_sql(query, db)
        db.close()
        return result
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None
    
# General Utility Function
def fetch_filtered_data(query, gender_condition=""):
    try:
        db = mysql.connector.connect(
            host="localhost",
            port=3306,
            user="root",
            password="Arjun123!",
            database="diabetes"
        )
        formatted_query = query.format(gender_condition=gender_condition)
        result = pd.read_sql(formatted_query, db)
        db.close()
        return result
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

    
# Render Bar Plot for Queries
def generate_bar_plot(data, x_col, y_col, title, xlabel, ylabel, color, rotation=45, multiply_y_by_100=False):
    img = io.BytesIO()
    plt.figure(figsize=(8, 4))

    # Apply multiplier for specific cases
    y_values = data[y_col] * 100 if multiply_y_by_100 else data[y_col]
    bars = plt.bar(data[x_col], y_values, color=color)
    plt.xlabel(xlabel, fontsize=12)
    plt.ylabel(ylabel, fontsize=12)
    plt.title(title, fontsize=14)

    # Set x-ticks to fixed values: 0, 1, 2
    plt.xticks([0, 1, 2], fontsize=12)

    for bar in bars:
        plt.text(
                bar.get_x() + bar.get_width() / 2,  # X position (center of the bar)
                bar.get_height() / 2,  # Y position (middle of the bar)
                f"{bar.get_height():.2f}%",  # Label text
                ha='center', va='center', fontsize=15, color="black"  # Center alignment and white color for contrast
            )
    plt.tight_layout()
    plt.savefig(img, format="png")
    img.seek(0)
    plt.close()
    return base64.b64encode(img.getvalue()).decode("utf-8")

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

    

    # Query 2: Physical Activity Percentage
    physical_activity_percentage, age_group_data = query_physical_activity_percentage(gender_condition)
    physical_activity_percentage = round(physical_activity_percentage, 2) if physical_activity_percentage else "No data available"

    # Age group labels based on the new table
    age_labels = [
        "18-24", "25-29", "30-34", "35-39", "40-44", "45-49", "50-54", "55-59",
        "60-64", "65-69", "70-74", "75-79", "80+"
    ]

    # Generate bar plot for physical activity percentage by age group
    img_physical_activity = io.BytesIO()
    plt.figure(figsize=(8, 4))
    if age_group_data is not None and not age_group_data.empty:
        bars = plt.bar(age_labels, age_group_data["PhysActivityPercentage"], color="#76C7C0")
        plt.xticks(rotation=45, ha='right', fontsize=12)
        plt.xlabel("Age Group", fontsize=15)
        plt.ylabel("Physical Activity Percentage", fontsize=15)
        plt.title("Physical Activity Percentage by Age Group", fontsize=12)
        
        # Add numbers inside each bar
        for bar, value in zip(bars, age_group_data["PhysActivityPercentage"]):
            plt.text(
                bar.get_x() + bar.get_width() / 2,  # X position (center of the bar)
                bar.get_height() / 2,  # Y position (middle of the bar)
                f"{value:.1f}%",  # Label text
                ha='center', va='center', rotation=90, fontsize=15, color="black"  # Center alignment and white color for contrast
            )
        
        plt.tight_layout()
    else:
        plt.text(0.5, 0.5, "No data available", horizontalalignment='center', verticalalignment='center', transform=plt.gca().transAxes)
    plt.savefig(img_physical_activity, format="png")
    img_physical_activity.seek(0)
    physical_activity_chart_url = base64.b64encode(img_physical_activity.getvalue()).decode("utf-8")
    plt.close()



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
            "education_level": int(education_level),
            "non_smoker_count": int(row[0]),
            "smoker_count": int(row[1]),
        })


    # Query 4: Income vs Healthcare Access
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
    bars = plt.bar(income_healthcare_data["Income"], income_healthcare_data["Avg_No_Doctor"], color="coral")
    for bar in bars:
        plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() - 0.02, f"{bar.get_height():.2f}", ha="center")
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
    bars = plt.bar(age_labels, mental_health_data["Avg_Mental_Health_Score"], color="#5DADE2")
    plt.xlabel("Age Group", fontsize=15)
    plt.ylabel("Days",fontsize=15)
    plt.xticks(rotation=45, ha='right', fontsize=12)
    for bar in bars:
        plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() - 0.5, f"{bar.get_height():.2f}", ha="center")
    plt.title("Average Mental Health Scores by Age")
    plt.tight_layout()
    plt.savefig(img_mental, format="png")
    img_mental.seek(0)
    mental_chart_url = base64.b64encode(img_mental.getvalue()).decode("utf-8")
    plt.close()

    # Query 6: Physical Activity Percentage vs Diabetes Status
    physical_activity_query = """
    SELECT Diabetes_Status.Status AS DiabetesStatus,
           (SUM(CASE WHEN Lifestyle.PhysActivity = 1 THEN 1 ELSE 0 END) / COUNT(*)) * 100 AS PhysActivityPercentage
    FROM Lifestyle
    JOIN Diabetes_Status ON Lifestyle.Diabetes_ID = Diabetes_Status.Diabetes_ID
    WHERE 1=1 {gender_condition}
    GROUP BY Diabetes_Status.Status;
    """
    physical_activity_data = fetch_filtered_data(physical_activity_query, gender_condition)
    physical_activity_chart = generate_bar_plot(
        physical_activity_data, "DiabetesStatus", "PhysActivityPercentage",
        "Physical Activity Percentage vs Diabetes Status", "Diabetes Status", "Physical Activity Percentage", "#76C7C0"
    )

    # Query 7: Healthcare Access vs Diabetes Status
    healthcare_access_query = """
    SELECT Diabetes_Status.Status AS DiabetesStatus,
           AVG(Medical_and_Wellbeing.NoDoctor) AS AvgNoDoctorAccess
    FROM Medical_and_Wellbeing
    JOIN Diabetes_Status ON Medical_and_Wellbeing.Diabetes_ID = Diabetes_Status.Diabetes_ID
    WHERE 1=1 {gender_condition}
    GROUP BY Diabetes_Status.Status;
    """
    healthcare_access_data = fetch_filtered_data(healthcare_access_query, gender_condition)
    healthcare_access_chart = generate_bar_plot(
        healthcare_access_data, "DiabetesStatus", "AvgNoDoctorAccess",
        "Healthcare Access vs Diabetes Status", "Diabetes Status", "Average Unable to See Doctor", "#FFA07A",
        multiply_y_by_100 = True 
    )

    # Query 8: Mental Health vs Diabetes Status
    mental_health_query = """
    SELECT Diabetes_Status.Status AS DiabetesStatus,
           AVG(Medical_and_Wellbeing.MentHlth) AS AvgMentalHealthDays
    FROM Medical_and_Wellbeing
    JOIN Diabetes_Status ON Medical_and_Wellbeing.Diabetes_ID = Diabetes_Status.Diabetes_ID
    WHERE 1=1 {gender_condition}
    GROUP BY Diabetes_Status.Status;
    """
    mental_health_data = fetch_filtered_data(mental_health_query, gender_condition)
    mental_health_chart = generate_bar_plot(
        mental_health_data, "DiabetesStatus", "AvgMentalHealthDays",
        "Mental Health vs Diabetes Status", "Diabetes Status", "Average Mental Health Days", "#87CEEB"
    )

    # Query 9: Smokers vs Diabetes Status
    smokers_vs_diabetes_query = """
    SELECT Diabetes_Status.Status AS DiabetesStatus,
           (SUM(CASE WHEN Lifestyle.Smoker = 1 THEN 1 ELSE 0 END) / COUNT(*)) * 100 AS SmokingPercentage
    FROM Lifestyle
    JOIN Diabetes_Status ON Lifestyle.Diabetes_ID = Diabetes_Status.Diabetes_ID
    WHERE 1=1 {gender_condition}
    GROUP BY Diabetes_Status.Status;
    """
    smokers_vs_diabetes_data = fetch_filtered_data(smokers_vs_diabetes_query, gender_condition)
    smokers_vs_diabetes_chart = generate_bar_plot(
        smokers_vs_diabetes_data, "DiabetesStatus", "SmokingPercentage",
        "Smoking Percentage vs Diabetes Status", "Diabetes Status", "Smoking Percentage", "#FF4500"
    )

    return render_template(
        "graphs.html",
        average_bmi=average_bmi,
        physical_activity_percentage=physical_activity_percentage,
        charts=charts,
        counts=counts,
        income_chart_url=income_chart_url,
        mental_chart_url=mental_chart_url,
        physical_activity_chart_url=physical_activity_chart_url,
        zip=zip,
        # added queries
        physical_activity_chart=physical_activity_chart,
        healthcare_access_chart=healthcare_access_chart,
        mental_health_chart=mental_health_chart,
        smokers_vs_diabetes_chart=smokers_vs_diabetes_chart,
        sex_filter=sex_filter

    )

@app.route("/")
def dashboard():
    return render_template("dashboard.html")


@app.route("/predict", methods=["GET", "POST"])
def predict():
    # Define the form fields and their labels
    form_fields = {
        "HighBP": "Do You Have High Blood Pressure? (0 = No, 1 = Yes)",
        "HighChol": "Do You Have High Cholesterol? (0 = No, 1 = Yes)",
        "CholCheck": "Have You Had a Cholesterol Check in the Past 5 Years? (0 = No, 1 = Yes)",
        "BMI": "What is Your Body Mass Index? (e.g., 25.5)",
        "Smoker": "Are You a Smoker? (0 = No, 1 = Yes)",
        "Stroke": "Have You Had a Stroke? (0 = No, 1 = Yes)",
        "HeartDiseaseorAttack": "Have You Had Heart Disease or Attack? (0 = No, 1 = Yes)",
        "PhysActivity": "Have You Been Physically Active in the Past 30 Days? (0 = No, 1 = Yes)",
        "Fruits": "Do You Consume Fruits Regularly (1 or more times a day)? (0 = No, 1 = Yes)",
        "Veggies": "Do You Consume Vegetables Regularly (1 or more times a day)? (0 = No, 1 = Yes)",
        "HvyAlcoholConsump": "Heavy Alcohol Consumption? (Heavy drinkers are men having more than 14 drinks per week and women having more than 7 drinks per week. 0 = No, 1 = Yes)",
        "NoDocbcCost": "Have You Not Been Able to See a Doctor in the Past 12 Months Due to Cost? (0 = No, 1 = Yes)",
        "GenHlth": "How Would You Rate Your General Health? (1 = Excellent to 5 = Poor)",
        "MentHlth": "How Many Days in the Past 30 Days Was Your Mental Health Not Good (0-30)",
        "PhysHlth": "How Many Days in the Past 30 Days Was Your Physical Health Not Good (0-30)",
        "DiffWalk": "Do You Have Difficulty Walking? (0 = No, 1 = Yes)",
        "Sex": "What is Your Sex? (0 = Female, 1 = Male)",
        "Age": "What is Your Age? (enter your age in years, please enter age >= 18)",
        "Education": "What is Your Highest Education Level? (1 = No Schooling, 2 = Grades 1-8, 3 = Some High School, 4 = High School Graduate, 5 = Some College, 6 = College Graduate)",
        "Income": "What is Your Income Level? (1 = <10K, 2 = 10K-15K, 3 = 15K-20K, 4 = 20K-25K, 5 = 25K-35K, 6 = 35K-50K, 7 = 50K-75K, 8 = 75K+)",
    }

    prediction = None
    if request.method == "POST":
        # Collect user input from the form
        user_input = {field: float(request.form[field]) for field in form_fields}

        # Map the actual age to age category
        user_input["Age"] = map_age_to_category(user_input["Age"])

        # Make prediction
        prediction = predict_diabetes(user_input)

    return render_template("predict.html", form_fields=form_fields, prediction=prediction)


if __name__ == "__main__":
    app.run(debug=True)