import asyncio, os, re
from playwright.async_api import async_playwright
base=open('test.html',encoding='utf8').read()
names=['MotorsPanel','LivePanel','FlyPanel','Charts','PFD','Popover','Input','Rig','Trail','Fullscreen','DroneModel','Exam','Camera','SensorPanel','EstChart','HoverRef']
def strip(name):
    i=base.index(f'// ---------- [{name}]')
    j=min(k for k in [base.find('\n// ----------',i+10), base.find('\n// =====',i+10)] if k>0)
    return base[:i]+base[j+1:]
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        for nm in names:
            open('del.html','w',encoding='utf8').write(strip(nm))
            pg=await b.new_page(viewport={'width':1440,'height':1000}); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
            await pg.goto('file://'+os.path.abspath('del.html')); await pg.wait_for_timeout(300)
            for v in ['att3','fly','hover','roll']:
                await pg.click(f'#segAxis button[data-v="{v}"]'); await pg.wait_for_timeout(250)
                if v=='fly': await pg.click('#btnRefly') if await pg.is_visible('#btnRefly') else None
            print(nm, 'OK' if not errs else errs[:2]); await pg.close()
        await b.close()
asyncio.run(main())
