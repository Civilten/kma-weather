import requests

API_KEY = "HXJNgeR_QWyyTYHkf0Fs6Q"
STN_ID = "108" # Seoul
URL = f"https://apihub.kma.go.kr/api/typ01/url/kma_sfctm2.php?tm=202211300900&stn={STN_ID}&help=1&authKey={API_KEY}"
# Actually, let's try without TM to get current?
# Documentation usually says TM is optional for "current" or "latest"? 
# Or maybe I need to find the "current" endpoint. 
# Let's try `kma_sfctm2.php?stn=108...` (without TM)
URL_CURRENT = f"https://apihub.kma.go.kr/api/typ01/url/kma_sfctm2.php?stn={STN_ID}&authKey={API_KEY}"

try:
    print(f"Testing URL: {URL_CURRENT}")
    response = requests.get(URL_CURRENT, timeout=10)
    response.encoding = 'euc-kr' 
    print(f"Status Code: {response.status_code}")
    print("First 500 characters:")
    print(response.text[:500])
except Exception as e:
    print(f"Error: {e}")
