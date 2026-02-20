import requests
import xml.etree.ElementTree as ET

# User provided key for this API
API_KEY = "OsOXb4zvRB-Dl2-M78QfKw"
YEAR = "2016"
URL = f"https://apihub.kma.go.kr/api/typ02/openApi/SfcYearlyInfoService/getYearSumry?pageNo=1&numOfRows=1&dataType=XML&year={YEAR}&authKey={API_KEY}"

def check_yearly_api_deep():
    print(f"Fetching: {URL}")
    try:
        response = requests.get(URL, timeout=15)
        root = ET.fromstring(response.text)
        
        # Find first item -> temp -> info
        # Structure seems to be: <response><body><items><item><temp><info>...
        
        infos = root.findall(".//info")
        print(f"Found {len(infos)} info blocks.")
        
        if len(infos) > 0:
            first_info = infos[0]
            print("\nFields in first <info> block:")
            for child in first_info:
                print(f"{child.tag}: {child.text}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_yearly_api_deep()
