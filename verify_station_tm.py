import requests

# User provided key for this API
API_KEY = "essYXrddTSaLGF63Xc0mAw"
TM = "202211300900"
URL = f"https://apihub.kma.go.kr/api/typ01/url/stn_inf.php?inf=SFC&stn=&tm={TM}&help=1&authKey={API_KEY}"

def check_station_tm():
    print(f"Fetching: {URL}")
    try:
        response = requests.get(URL, timeout=15)
        # KMA often uses EUC-KR for this specific endpoint family
        response.encoding = 'euc-kr'
        
        print(f"Status: {response.status_code}")
        print("First 500 chars:")
        print(response.text[:500])
        
        if "ERROR" in response.text or "Err" in response.text:
            print("API Error detected.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_station_tm()
