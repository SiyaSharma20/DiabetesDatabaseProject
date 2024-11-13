from flask import Flask, render_template
import mysql.connector
import pandas as pd

app = Flask(__name__)

def get_lifestyle_data():
    # Connect to the MySQL database
    db = mysql.connector.connect(
        host="localhost",
        port=3306,
        user="root",
        password="Arjun123!",
        database="diabetes"
    )
    
    # Query to fetch the first 5 rows of the Lifestyle table
    query = "SELECT * FROM Lifestyle LIMIT 5;"
    
    # Use pandas to read the SQL query result into a DataFrame
    lifestyle_df = pd.read_sql(query, db)
    
    # Close the database connection
    db.close()
    
    # Convert DataFrame to a list of dictionaries for easier rendering in HTML
    data = lifestyle_df.to_dict(orient="records")
    return data

@app.route('/')
def display_lifestyle():
    # Fetch data from the database
    lifestyle_data = get_lifestyle_data()
    # Render the template with the fetched data
    return render_template('lifestyle.html', data=lifestyle_data)

if __name__ == '__main__':
    app.run(debug=True)
