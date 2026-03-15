from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium_stealth import stealth

def selenium_options():

    options=Options()

    # ---1. 基礎偽裝 (這一層是基本功)---
    # 使用新版無頭模式 (更難被偵測，且渲染效果更好)
    options.add_argument("--headless=new")
    # 隱藏 Selenium 的自動化特徵，以繞過網站的反爬蟲偵測。
    options.add_argument("--disable-blink-features=AutomationControlled")

    # 當手動開啟 Selenium 控制的瀏覽器時，上方會有一條黃色警告：「Chrome 正受到自動測試軟體控制」。
    # 這行指令把那個黃色警告條拿掉。
    options.add_experimental_option("excludeSwitches", ["enable-automation"])

    # Selenium 有時會嘗試載入自己的擴充功能來控制瀏覽器，禁用這個行為
    options.add_experimental_option('useAutomationExtension', False)
    
    # ---2. 視窗設定 (財經網站很在意視窗大小，太小會被當作手機或爬蟲)---
    # 響應式網頁 (RWD)：現在的財經網站（如鉅亨網、Yahoo 股市）都會根據視窗大小改變排版。
    # 如果不設 (預設視窗很小)：網頁可能會變成「手機版」，原本在表格裡的股價資訊可能會被隱藏。
    options.add_argument("--start-maximized")
    options.add_argument("--window-size=1920,1080") 

    # ---3. 穩定性設定---
    # 關閉瀏覽器的「通知提示」
    options.add_argument("--disable-notifications")
    # 禁用 GPU 硬體加速。
    options.add_argument("--disable-gpu")

    # ---4. 雲端部署時加入---
    # options.add_argument("--no-sandbox")
    # options.add_argument("--disable-dev-shm-usage")

    return options

def selenium_bulid():

    # 自動下載驅動

    # 如果用 webdriver.Chrome()，
    # 出事時：它可能只會回傳一句 SessionNotCreatedException 或 DriverNotFound。
    # 你的反應：??
    # 是 Google 伺服器掛了？
    # 是我的 Docker 權限不對？
    # 是它抓錯版本了？
    # 還是它把驅動下載到一個我找不到的地方？
    # 結果：你只能猜，或者把整個 Image 重包一遍碰運氣。

    # 所以選用 ChromeDriverManager().install()，因為此模組會把動作攤在陽光下。
    # 出事時：因為下載動作是由 Python 程式碼執行的，它會噴出很具體的 Python 錯誤。
    # 例如：
    # ConnectionError -> 喔，Cloud Run 連不上外網。
    # PermissionError: [Errno 13] Permission denied: '/root/.wdm/...' -> 喔，Docker 權限沒設好，無法寫入檔案。
    # ValueError: There is no such driver by url... -> 喔，這個版本的 Chrome 還沒出對應的驅動。
    # 結果：看一眼 Log，你馬上知道要修哪裡。

    service=Service(ChromeDriverManager().install())

    driver=webdriver.Chrome(service=service,options=selenium_options())


    # 抓取自動下載的驅動程式 UA
    original_ua = driver.execute_script("return navigator.userAgent").strip()
    #print(f"原始 UA: {original_ua}")

    # 轉為正常的 Chrome UA，不一定會有 "Headless" 關鍵字，但還是預防一下，
    clean_ua = original_ua.replace("Headless", "")
    #print(f"清洗後 UA: {clean_ua}")

    # 強制覆寫網路層 (給伺服器看的 Header)
    driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": clean_ua})

    # 如果 Selenium 是機器人，那 selenium_stealth 就是它的身分證偽造工具。
    # 作用是會在瀏覽器打開網頁、但還沒開始載入內容的那一瞬間（比網站的檢查程式更早），
    # 注入一段 JavaScript 腳本，把所有「我是機器人」的特徵全部抹掉。
    # 原地修改寫法，不用賦值，直接生效
    stealth(driver,

        # 瀏覽器有兩處會送出 User-Agent：一個是 HTTP Header（發送請求時），
        # 另一個是 JavaScript 變數 (navigator.userAgent)。
        # 很多反爬蟲機制會檢查這兩者是否相同。如果你的 Header 說是 Chrome 120，
        # 但 JS 讀出來是 Chrome 90 或預設的 Headless UA，網站就會判定你是機器人。
        user_agent=clean_ua, # 確保這裡跟 Header 一致

        # 真實用戶特徵：一般台灣用戶的瀏覽器通常會包含繁體中文、簡體中文、美式英文等優先順序。
        languages=["zh-TW", "zh", "en-US", "en"],

        # 覆蓋 navigator.vendor 屬性，Chrome 瀏覽器的 vendor 永遠是 "Google Inc."
        vendor="Google Inc.",

        # 這代表作業系統。即使你是 64 位元的 Windows，瀏覽器歷史遺留原因通常還是會回報 "Win32"
        platform="Win32",

        # 這裡偽裝成 "Intel Iris OpenGL Engine"，讓網站以為這是一台普通的筆記型電腦
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",

        # 設為 True 會注入額外的 CSS 或 JS 來修正這些渲染特徵，讓 Headless 看起來更像有頭模式
        fix_hairline=True,
    )

    return driver
