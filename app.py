from flask import Flask, render_template, request, jsonify, send_file
import requests
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor
import time

app = Flask(__name__)
executor = ThreadPoolExecutor(max_workers=10)

async def async_request(session, method, url, headers, data):
    async with getattr(session, method.lower())(url, headers=headers, data=data) as response:
        return {
            'status_code': response.status,
            'headers': dict(response.headers),
            'content': await response.text()
        }

def perform_request(method, url, headers, body):
    start_time = time.time()
    try:
        response = requests.request(method, url, headers=headers, data=body)
        end_time = time.time()
        return {
            'status_code': response.status_code,
            'headers': dict(response.headers),
            'content': response.text,
            'time': end_time - start_time
        }
    except requests.RequestException as e:
        end_time = time.time()
        return {'error': str(e), 'time': end_time - start_time}

@app.route('/')
def index():
    return send_file('index.html')

@app.route('/test-request', methods=['POST'])
def test_request():
    data = request.json
    url = data.get('url')
    method = data.get('method')
    headers = data.get('headers', {})
    body = data.get('body', '')

    future = executor.submit(perform_request, method, url, headers, body)
    return jsonify(future.result())

@app.route('/test-multiple', methods=['POST'])
def test_multiple():
    data = request.json
    requests_data = data.get('requests', [])

    async def run_requests():
        async with aiohttp.ClientSession() as session:
            tasks = [async_request(session, req['method'], req['url'], req['headers'], req['body']) for req in requests_data]
            return await asyncio.gather(*tasks)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    results = loop.run_until_complete(run_requests())
    
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)

