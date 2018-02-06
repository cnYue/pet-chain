# -*- coding:utf-8 -*-
import requests
import time
import thread
#import threadpool
import json
import sys
import base64
import ConfigParser
try:
    from selenium import webdriver
except ImportError,e:
    webdriver_model = None


class PetChain():
    def __init__(self):
        self.degree_map = {
            0:"common",
            1:"rare",
            2:"excellence",
            3:"epic",
            4:"mythical",
        }
        self.degree_conf = {}
        self.interval = 1

        self.cookies = ''
        self.username = ''
        self.password = ''
        self.headers = {}
        self.get_headers()
        self.get_config()

    def get_config(self):
        config = ConfigParser.ConfigParser()
        config.read("config.ini")

        for i in range(5):
            try:
                amount = config.getfloat("Pet-Chain", self.degree_map.get(i))
            except Exception,e:
                amount = 100
            self.degree_conf[i] = amount

        self.interval = config.getfloat("Pet-Chain", "interval")

        self.username = config.get("Login", "username")
        self.password = config.get("Login", "password")

    def get_headers(self):
        with open("data/headers.txt") as f:
            lines = f.readlines()
            headers = dict()
            for line in lines:
                splited = line.strip().split(":")
                key = splited[0].strip()
                value = ":".join(splited[1:]).strip()
                self.headers[key] = value

    def get_market(self):
        try:
            data = {
                "appId":1,
                "lastAmount":0,
                "lastRareDegree":0,
                "pageNo":1,
                "pageSize":10,
                "petIds":[],
                "querySortType":"AMOUNT_ASC",
                "requestId":int(time.time() * 1000),
                "tpl":"",
            }
            page = requests.post("https://pet-chain.baidu.com/data/market/queryPetsOnSale", headers=self.headers, data=json.dumps(data))
            if page.json().get(u"errorMsg") == u"success":
                print "[->] purchase"
                pets = page.json().get(u"data").get("petsOnSale")

                for pet in pets:
                    if not self.purchase(pet):
                        break

                """
                pool = threadpool.ThreadPool(10)
                req = threadpool.makeRequests(self.purchase, pets)
                for queue in req:
                    pool.putRequest(queue)
                pool.wait()
                """
        except Exception,e:
            print(e)
            pass
            
    def get_captcha(self):
        result = ("", 0)
        data = {
            "appId":1,
            "requestId": int(time.time() * 1000),
            "tpl":""
        }
        page = requests.post("https://pet-chain.baidu.com/data/captcha/gen", headers=self.headers, data=json.dumps(data), timeout=2)
        if page.status_code == 200:
            ret = page.json()
            with open('captcha.jpg', 'wb') as fp:
                fp.write(base64.b64decode(ret.get('data', {}).get('img')))
                fp.close()
            captcha = raw_input("enter captcha:")
            return (captcha, ret.get('data', {}).get('seed'))
        return result

    def purchase(self, pet):
        try:
            pet_id = pet.get(u"petId")
            pet_amount = pet.get(u"amount")
            pet_validCode = pet.get(u"validCode")
            pet_degree = pet.get(u"rareDegree")
            data = {
                "appId":1,
                "petId":pet_id,
                "captcha": "",
                "seed": 0,
                "requestId": int(time.time() * 1000),
                "tpl":"",
                "amount":"{}".format(pet_amount),
                "validCode": pet_validCode
            }

            print pet_id, pet.get(u"desc"), pet_amount, "<=", self.degree_conf.get(pet_degree), float(pet_amount) <= self.degree_conf.get(pet_degree), "\n"
            
            if float(pet_amount) <= self.degree_conf.get(pet_degree):
                data['captcha'], data['seed'] = self.get_captcha()
                page = requests.post("https://pet-chain.baidu.com/data/txn/create", headers=self.headers, data=json.dumps(data), timeout=2)
                print json.dumps(page.json(),ensure_ascii=False)
                return True
        except Exception,e:
            pass
        return False

    def login(self):
        assert self.username and self.password, ValueError("请在配置文件中配置用户名和密码")
        web = webdriver.Chrome()
        web.get("https://wappass.baidu.com/passport/login?adapter=3&u=https%3A%2F%2Fpet-chain.baidu.com%2Fchain%2Fpersonal%3Ft%3D1517824991316")
        
        username_el = web.find_element_by_name("username")
        username_el.send_keys(self.username)

        password_el = web.find_element_by_name("password")
        password_el.send_keys(self.password)

        
        if_yzm = web.find_element_by_id("login-verifyWrapper").value_of_css_property("display")
        if if_yzm != "none":
            yzm = raw_input("请输入验证码: ")
            web.find_element_by_name("verifycode").send_keys(yzm)

        web.find_element_by_id("login-submit").click()
        time.sleep(5)
        cookies = web.get_cookies()
        self.format_cookie(cookies)
        web.quit()
        self.run()

    def format_cookie(self, cookies):
        self.cookies = ''
        for cookie in cookies:
            self.cookies += cookie.get(u"name") + u"=" + cookie.get(u"value") + ";"
        self.headers = {
            'Accept':'application/json',
            'Accept-Encoding':'gzip, deflate, br',
            'Accept-Language':'en-US,en;q=0.9',
            'Connection':'keep-alive',
            'Content-Type':'application/json',
            'Cookie':self.cookies,
            'Host':'pet-chain.baidu.com',
            'Origin':'https://pet-chain.baidu.com',
            'Referer':'https://pet-chain.baidu.com/chain/dogMarket?t=1517829948427',
            'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36',
        }

    def run(self):
        while True:
            pc.get_market()
            time.sleep(self.interval)

if __name__ == "__main__":
    pc = PetChain()
    if len(sys.argv) >= 2 and sys.argv[1] == "run":
        pc.run()
    elif len(sys.argv) >= 2 and sys.argv[1] == "login":
        pc.login()
    else:
        pc.run()
