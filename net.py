import requests

def validate_token(token: str) -> bool:
    try:
        r = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=5) # validing
        return r.status_code == 200 and r.json().get("ok", False)
        print("Verificated apikey. Valid")
    except:
        return False
