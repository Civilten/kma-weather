import requests
import pandas as pd
import xml.etree.ElementTree as ET

# User provided key for this API
API_KEY = "OsOXb4zvRB-Dl2-M78QfKw"
YEAR = "2016"
URL = f"https://apihub.kma.go.kr/api/typ02/openApi/SfcYearlyInfoService/getYearSumry?pageNo=1&numOfRows=10&dataType=XML&year={YEAR}&authKey={API_KEY}"

def check_yearly_api():
    print(f"Fetching: {URL}")
    try:
        response = requests.get(URL, timeout=15)
        response.encoding = 'utf-8' # XML usually utf-8
        
        print(f"Status: {response.status_code}")
        print("First 500 chars:")
        print(response.text[:500])
        
        # Try Parsing XML
        root = ET.fromstring(response.text)
        
        # Find first item
        first_item = root.find(".//item")
        if first_item is not None:
            print("\nFields found in first item:")
            for child in first_item:
                print(f" - {child.tag}: {child.text}")
        else:
            print("No <item> found in XML.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_yearly_api()
