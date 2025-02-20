import random

host = "brd.superproxy.io"
port = 33335
username ="brd-customer-hl_5abbed84-zone-datacenter_proxy1"
password = "k54fqfrc20li"
session_id = random.random()
proxy_url=('http://{}-session-{}:{}@{}:{}'.format(username, session_id ,password,host, port))