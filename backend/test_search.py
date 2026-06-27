import urllib.request
import json

data = urllib.parse.urlencode({'query': '高压包'}).encode('utf-8')
req = urllib.request.Request('http://localhost:8000/api/search/text', data=data, method='POST')
try:
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode())
        # 只打印前两个结果中的图片信息
        for i, r in enumerate(data.get('results', [])[:2]):
            print(f"\n=== Result {i} ===")
            print(f"Type: {r.get('type')}")
            print(f"Title: {r.get('title')}")
            print(f"Image URL: {r.get('image_url')}")
            print(f"Strong images: {json.dumps(r.get('strong_images', [])[:1], ensure_ascii=False)}")
except Exception as e:
    print(f"Error: {e}")
