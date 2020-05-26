import os, urllib.parse, requests

def apiprice(ticker):
    # load price from NY

    try:
        API_KEY = os.environ.get('myAPI_KEY')
        response = requests.get(f"https://cloud-sse.iexapis.com/stable/stock/{urllib.parse.quote_plus(ticker)}/quote?token={API_KEY}")
        response.raise_for_status()
    except requests.RequestException:
        return None

    try:
        resp = response.json()
        return{
            "name": resp['companyName'],
            "price": float(resp['latestPrice'])
        }
    except (KeyError, TypeError,ValueError):
        return None


def error_page(message):
    return render_template("error_page.html",message=message)


