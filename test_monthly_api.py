import requests
import xml.etree.ElementTree as ET

API_KEY = "fFr5k0SuRyia-ZNErlcoHA"

def test_api(url, name):
    print(f"\n--- Testing {name} ---")
    try:
        response = requests.get(url, timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            root = ET.fromstring(response.text)
            infos = root.findall(".//info")
            print(f"Found {len(infos)} <info> tags.")
            if infos:
                print("First record keys:")
                for child in infos[0]:
                    print(f"  {child.tag}: {child.text}")
        else:
            print("Failed.")
    except Exception as e:
        print(f"Error: {e}")

url1 = f"https://apihub.kma.go.kr/api/typ02/openApi/SfcMtlyInfoService/getMmSumry?pageNo=1&numOfRows=10&dataType=XML&year=2016&month=09&authKey={API_KEY}"
test_api(url1, "getMmSumry")

url2 = f"https://apihub.kma.go.kr/api/typ02/openApi/SfcMtlyInfoService/getMmSumry2?pageNo=1&numOfRows=10&dataType=XML&year=2016&month=09&authKey={API_KEY}"
test_api(url2, "getMmSumry2")
