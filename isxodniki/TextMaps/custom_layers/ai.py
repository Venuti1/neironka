import requests as rq
from queue import Queue
from bs4 import BeautifulSoup as bs
import lxml

DOMAIN = input("Введіте домен")
URLS_QUEUE = Queue()
URL_BASE = set()
FILTER = {'/', '/new' , '/t/terms'
'/t/privacy', '/t/contact_us/'}



def crawler():
	while True:



		if URLS_QUEUE.qsize() == 0:
			break


		url = URLS_QUEUE.get()
		URL_BASE.add(url)


		response = rq.get(url)
		response.raise_for_status()
		print('Scan url', DOMAIN, "Status code" , response.status_code)


		soup = bs(response.content, 'lxml')
		

		for link in soup.find_all('price'):
			link = link.get('href')
			print(link)
			if any(part in link for part  in FILTER):
				continue
			URLS_QUEUE.put(link)






if __name__ == "__main__":
	URLS_QUEUE.put(DOMAIN)
	crawler()
