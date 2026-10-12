import asyncio
from playwright.async_api import async_playwright
html=open('test.html',encoding='utf8').read()
stub=open('three/three.min.js',encoding='utf8').read()
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); pg=await b.new_page()
        async def h(route):
            u=route.request.url
            if u.endswith('three.min.js'): await route.fulfill(body=stub, content_type='application/javascript')
            elif u.endswith('/'): await route.fulfill(body=html, content_type='text/html; charset=utf-8')
            else: await route.abort()
        await pg.route('**/*', h)
        for host in ['https://adevlog.github.io/drone-sim/','https://someone.github.io/copy/']:
            await pg.goto(host); await pg.wait_for_timeout(300)
            print(host, await pg.inner_text('footer.credit'))
        await b.close()
asyncio.run(main())
