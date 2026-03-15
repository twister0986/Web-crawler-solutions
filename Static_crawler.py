import requests

def get_response(url):

    try:

        htmlfile=requests.get(url)
        #如果請求狀態不是200，就會拋出異常
        htmlfile.raise_for_status()
        #設定編碼
        htmlfile.encoding = 'utf-8'

        return htmlfile 
    
    except requests.exceptions.RequestException as e:

        #捕捉所有相關錯誤
        print(f'網頁內容取得失敗:{e}')

        return None
