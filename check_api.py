import requests

url = "https://apihub.kma.go.kr/api/typ01/url/stn_inf.php?inf=SFC&stn=&help=1&authKey=HXJNgeR_QWyyTYHkf0Fs6Q"
try:
    response = requests.get(url, timeout=10)
    # The API might return EUC-KR (common for KMA), but let's try to detect or fallback
    # If standard utf-8 fails, try euc-kr
    if response.encoding.lower() == 'iso-8859-1':
         response.encoding = 'euc-kr' 
    
    with open("api_sample.txt", "w", encoding="utf-8") as f:
        f.write(response.text)
    
    print("Successfully saved to api_sample.txt")

except Exception as e:
    print(f"Error: {e}")
