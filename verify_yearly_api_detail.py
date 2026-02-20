import requests
import xml.etree.ElementTree as ET

# User provided key for this API
API_KEY = "OsOXb4zvRB-Dl2-M78QfKw"
YEAR = "2016"
URL = f"https://apihub.kma.go.kr/api/typ02/openApi/SfcYearlyInfoService/getYearSumry?pageNo=1&numOfRows=1&dataType=XML&year={YEAR}&authKey={API_KEY}"

def check_yearly_api_detail():
    print(f"Fetching: {URL}")
    try:
        response = requests.get(URL, timeout=15)
        
        # Try Parsing XML
        root = ET.fromstring(response.text)
        
        # Iterate all items to see if there is metadata or just data
        items = root.find(".//items")
        if items is not None:
             for item in items:
                 # Print all tags and values to see if we can infer meanings
                 for child in item:
                     # Some APIs return <info> tag wrapping fields, or flat fields
                     if child.tag == "temp": # The previous output showed <temp>...
                         print("Found <temp> tag, exploring children...")
                         for subchild in child:
                             print(f"{subchild.tag}: {subchild.text}")
                     else:       
                        print(f"{child.tag}: {child.text}")
        else:
            print("No <items> found.")
            print(response.text[:1000])

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_yearly_api_detail()
