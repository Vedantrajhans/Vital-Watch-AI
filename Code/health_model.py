import pandas as pd
from sklearn.ensemble import RandomForestClassifier

# Load and preprocess training data once
train_data = pd.read_csv('Training.csv')

def preprocess(data):
    columns_to_drop = ['Unnamed: 5', 'Unnamed: 6', 'Unnamed: 7']
    data = data.drop(columns=[col for col in columns_to_drop if col in data.columns], errors='ignore')

    if 'Blood Pressure' in data.columns:
        bp_split = data['Blood Pressure'].str.split('/', expand=True)
        data['Systolic'] = pd.to_numeric(bp_split[0], errors='coerce')
        data['Diastolic'] = pd.to_numeric(bp_split[1], errors='coerce')
        data.drop(columns=['Blood Pressure'], inplace=True)

    if 'Target' not in data.columns:
        data['Target'] = ((data['Heart Rate'] > 100) |
                          (data['Systolic'] > 130) |
                          (data['Diastolic'] > 85) |
                          (data['Quality of Sleep'] < 5) |
                          (data['Sleep Duration'] < 6)).astype(int)

    return data

# Preprocess training data
train_data = preprocess(train_data)
features = ['Heart Rate', 'Systolic', 'Diastolic', 'Sleep Duration', 'Quality of Sleep', 'Daily Steps']
X_train = train_data[features]
y_train = train_data['Target']

# Train the model
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Health issue detection for one row
def detect_health_issues_row(row, index=0):
    prediction = model.predict([row[features].values])[0]
    recommendations = []

    if row['Heart Rate'] > 100:
        recommendations.append("Your heart rate is high. Consider seeing a cardiologist and reducing stress.")
    if row['Systolic'] > 130 or row['Diastolic'] > 85:
        recommendations.append("High blood pressure detected. Limit salt intake and monitor daily.")
    if row['Sleep Duration'] < 6 or row['Quality of Sleep'] < 2:
        recommendations.append("Your sleep quality/duration is low. Aim for 7-8 hours of restful sleep.")
    if row['Daily Steps'] < 5000:
        recommendations.append("Low physical activity. Try to walk more during the day.")

    return {
        "metrics": row[features].to_dict(),
        "prediction": prediction,
        "recommendations": recommendations
    }

# Analyze either from CSV or slider input
def analyze_latest_health(index=None, input_data=None):
    try:
        if input_data:
            # Manual input mode (from Streamlit sliders)
            input_df = pd.DataFrame([input_data])
            return detect_health_issues_row(input_df.iloc[0])

        # File-based mode
        test_data = pd.read_csv('health_data 1.csv')
        test_data = preprocess(test_data)
        if test_data.empty:
            return None

        # Wrap-around if index exceeds data length
        if index is None:
            index = len(test_data) - 1
        elif index >= len(test_data):
            index = 0

        return detect_health_issues_row(test_data.iloc[index], index)

    except Exception as e:
        print(f"Error in analyze_latest_health: {e}")
        return None
