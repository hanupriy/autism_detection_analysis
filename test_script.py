import urllib.request
import urllib.parse

print("Testing the /predict endpoint...")
data = {
    "patient_name": "Jane Doe",
    "age": "4",
    "gender": "Female",
    "eye_contact": "8",
    "communication": "7",
    "behavior": "9",
    "social": "6"
}

data_encoded = urllib.parse.urlencode(data).encode('utf-8')

try:
    req = urllib.request.Request("http://127.0.0.1:5000/predict", data=data_encoded)
    response = urllib.request.urlopen(req)
    print(f"Status Code: {response.status}")
    
    html = response.read().decode('utf-8')
    if "Assessment Results" in html:
        print("SUCCESS: Result page loaded.")
    else:
        print("FAILED: Result page not found in response.")
        
    if "accuracy_graph.png" in html:
        print("SUCCESS: Graph references are present.")
        
    # Check if download route is referenced
    if "/download/Report_Jane_Doe" in html:
        print("SUCCESS: PDF download link is present.")
except Exception as e:
    print(f"Error connecting: {e}")
