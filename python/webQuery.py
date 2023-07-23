import json
import urllib.request

def webQuery(url,key):
    x = urllib.request.urlopen(url+'&key='+key)
    raw_data = x.read()
    encoding = x.info().get_content_charset('utf8')  # JSON default
    #print(raw_data)   #this is data in string format
    data = json.loads(raw_data.decode(encoding))
    return data

def main():
    event = webQuery('https://clevelandcenter.org/api/data/bot/event/?event_id=185','2552674032qiogjioarhio98550468311756938450abc')
    print(event)
if __name__=='__main__':
    main()