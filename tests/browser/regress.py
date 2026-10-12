import asyncio, os, json
from playwright.async_api import async_playwright
FAKE = "window.__ax=[0,0,0,0]; navigator.getGamepads=()=>window.__gp?[{connected:true,id:'fake',axes:window.__ax,buttons:[]}]:[];"
results=[]
def check(name, ok, info=''):
    results.append((name, bool(ok), info))
async def popups(pg, ids, tag):
    bad=[]
    for bid in ids:
        vis = await pg.evaluate(f'!document.getElementById("{bid}").hidden')
        if not vis: continue
        await pg.click('#'+bid); await pg.wait_for_timeout(60)
        t = await pg.inner_text('#popBody')
        if 'NaN' in t or 'undefined' in t or not t.strip(): bad.append(bid)
    await pg.keyboard.press('Escape')
    return bad
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={'width':1440,'height':1000})
        errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.add_init_script(FAKE)
        await pg.goto('file://'+os.path.abspath('test.html')); await pg.wait_for_timeout(800)
        check('load no errors', not errs, errs[:2])
        B=['bCmd','bOuter','bInner','bMix','bMot','bPlant']
        for ax in ['roll','pitch','yaw','thr','att3']:
            await pg.click(f'#segAxis button[data-v="{ax}"]'); await pg.wait_for_timeout(500)
            st = await pg.evaluate('JSON.stringify([sim.axis, sim.focus, sim.profile, sim.log.length>10])')
            check(f'mode {ax} running', json.loads(st)[3], st)
            bad = await popups(pg, B, ax); check(f'popups {ax}', not bad, bad)
            for wv in ['step','sine','square']:
                await pg.click(f'#segWave button[data-v="{wv}"]'); await pg.wait_for_timeout(150)
            await pg.click('#segLoop button[data-v="inner"]'); await pg.wait_for_timeout(200)
            bad = await popups(pg, B, ax+'-inner'); check(f'popups {ax} inner', not bad, bad)
            await pg.click('#segLoop button[data-v="cascade"]'); await pg.wait_for_timeout(100)
        for wa in ['pitch','yaw','thr','none','roll']:
            await pg.click(f'#segWaveAxis button[data-v="{wa}"]'); await pg.wait_for_timeout(200)
            for fx in ['roll','thr']:
                await pg.click(f'#segFocus button[data-v="{fx}"]'); await pg.wait_for_timeout(60)
                bad = await popups(pg, ['bCmd','bInner','bPlant'], 'att3'); check(f'att3 wave {wa} focus {fx}', not bad, bad)
        await pg.click('#altHold'); await pg.wait_for_timeout(100); await pg.click('#altHold'); await pg.click('#tiltComp')
        # params reset by mode switch
        await pg.click('#segAxis button[data-v="roll"]'); await pg.wait_for_timeout(200)
        await pg.evaluate('sim.params.roll.MC_ROLL_P=12')
        await pg.click('#segAxis button[data-v="pitch"]'); await pg.wait_for_timeout(100)
        await pg.click('#segAxis button[data-v="roll"]'); await pg.wait_for_timeout(100)
        check('mode switch resets params', await pg.evaluate('sim.params.roll.MC_ROLL_P')==6.5)
        # kick / pause / speed
        await pg.click('#btnKick'); await pg.click('#btnPause'); t1=await pg.evaluate('sim.t'); await pg.wait_for_timeout(300); t2=await pg.evaluate('sim.t')
        check('pause stops time', t1==t2); await pg.click('#btnPause')
        await pg.click('#segSpeed button[data-v="0.25"]'); await pg.click('#segSpeed button[data-v="1"]')
        # fly
        await pg.click('#segAxis button[data-v="fly"]'); await pg.wait_for_timeout(300)
        st=json.loads(await pg.evaluate('JSON.stringify([sim.profile, sim.fmode, sim.armed, sim.landed])'))
        check('fly+pilot -> consumer pos', st[:2]==['consumer','pos'], st)
        check('refly button visible in fly', await pg.evaluate('!document.getElementById("btnRefly").hidden'))
        await pg.click('#segCam button[data-v="chase"]'); await pg.wait_for_timeout(100)
        check('chase -> px4', await pg.evaluate('sim.profile')=='px4')
        await pg.click('#segProfile button[data-v="consumer"]'); await pg.wait_for_timeout(100)
        check('manual consumer', await pg.evaluate('[sim.profile, sim.params.roll.MC_ROLL_P]')==['consumer',5])
        await pg.click('#segCam button[data-v="orbit"]'); await pg.wait_for_timeout(100)
        await pg.click('#segCam button[data-v="pilot"]'); await pg.wait_for_timeout(100)
        check('pilot -> consumer', await pg.evaluate('sim.profile')=='consumer')
        # keyboard arm
        await pg.click('body', position={'x':5,'y':5})
        await pg.keyboard.down('KeyS'); await pg.keyboard.down('KeyD'); await pg.wait_for_timeout(1300); await pg.keyboard.up('KeyD'); await pg.keyboard.up('KeyS')
        check('keyboard arm', await pg.evaluate('sim.armed'))
        await pg.keyboard.down('KeyW'); await pg.wait_for_timeout(700); await pg.keyboard.up('KeyW'); await pg.wait_for_timeout(6500)
        st=json.loads(await pg.evaluate('JSON.stringify([+(-sim.pos[2]).toFixed(2), app_debug.exam.done.H===true, sim.landed])'))
        check('exam hover H done', st[1] and not st[2], st)
        check('trail has points', await pg.evaluate('app_debug.trail.count()>0'))
        await pg.click('#chkTrail'); await pg.wait_for_timeout(100); check('trail hidden', await pg.evaluate('!app_debug.trail.line.visible')); await pg.click('#chkTrail')
        for fm in ['acro','stab','alt','pos']:
            await pg.click(f'#segFmode button[data-v="{fm}"]'); await pg.wait_for_timeout(150)
            for fx in ['roll','pitch','yaw','thr','pos']:
                await pg.click(f'#segFocus button[data-v="{fx}"]'); await pg.wait_for_timeout(40)
                bad = await popups(pg, ['bStick','bPos']+B, f'fly {fm} {fx}'); check(f'fly popups {fm} {fx}', not bad, bad)
        await pg.click('#segFmode button[data-v="pos"]'); await pg.wait_for_timeout(100)
        await pg.evaluate('sim.params.pos.MPC_XY_P=2.5')
        await pg.click('body', position={'x':5,'y':5})
        await pg.keyboard.down('ArrowLeft'); await pg.wait_for_timeout(1200); await pg.keyboard.up('ArrowLeft'); await pg.wait_for_timeout(300)
        check('moved left', await pg.evaluate('sim.pos[1] < -1'))
        await pg.click('#btnRefly'); await pg.wait_for_timeout(200)
        st=json.loads(await pg.evaluate('JSON.stringify([sim.armed, sim.landed, Math.abs(sim.pos[1])<1e-6, app_debug.trail.count(), Object.keys(app_debug.exam.done).length, Math.round(app_debug.pilotView.yaw*57.3), Math.round(app_debug.pilotView.pitch*57.3), sim.params.pos.MPC_XY_P, app_debug.input.thr])'))
        check('refly resets', st==[False,True,True,0,0,0,-32,2.5,-1], st)
        await pg.keyboard.press('KeyR'); await pg.wait_for_timeout(100)
        # fake gamepad diagonal arm
        await pg.evaluate('window.__gp=true; window.__ax.splice(0,4,0.7,0.7,0,0)'); await pg.wait_for_timeout(1400)
        check('gamepad diagonal arm', await pg.evaluate('sim.armed'))
        await pg.evaluate('window.__ax.splice(0,4,0,0,0,0)'); await pg.wait_for_timeout(200)
        check('status says connected', '手把已連線' in await pg.inner_text('#inputStatus'))
        await pg.evaluate('window.__gp=false')
        # crash restart
        await pg.evaluate('sim.crashed=true; sim.crashInfo="t"'); await pg.wait_for_timeout(200)
        check('crash banner', await pg.evaluate('!document.getElementById("crashBanner").hidden'))
        await pg.click('#btnCrashReset'); await pg.wait_for_timeout(200)
        check('crash restart', await pg.evaluate('!sim.crashed && !sim.armed'))
        # fullscreen
        await pg.click('#btnFull'); await pg.wait_for_timeout(300)
        check('fullscreen on', await pg.evaluate('!!document.fullscreenElement && document.getElementById("btnFull").textContent==="退出全螢幕"'))
        await pg.click('#btnFull'); await pg.wait_for_timeout(300)
        check('fullscreen off', await pg.evaluate('!document.fullscreenElement'))
        await pg.click('body', position={'x':5,'y':5}); await pg.keyboard.press('KeyF'); await pg.wait_for_timeout(300)
        check('F key', await pg.evaluate('document.getElementById("btnFull").textContent==="退出全螢幕"'))
        await pg.keyboard.press('KeyF'); await pg.wait_for_timeout(200)
        # exam toggle
        await pg.click('#chkExam'); await pg.wait_for_timeout(100)
        check('exam hidden', await pg.evaluate('document.getElementById("examHud").hidden')); await pg.click('#chkExam')
        # defaults button
        await pg.evaluate('sim.params.roll.MC_ROLL_P=1'); await pg.click('#btnDefaults')
        check('defaults button', await pg.evaluate('sim.params.roll.MC_ROLL_P')==5)
        # theme change
        await pg.emulate_media(color_scheme='dark'); await pg.wait_for_timeout(300)
        await pg.evaluate('document.documentElement.setAttribute("data-theme","light")'); await pg.wait_for_timeout(200)
        # back to roll
        await pg.click('#segAxis button[data-v="roll"]'); await pg.wait_for_timeout(300)
        check('back to roll px4', await pg.evaluate('[sim.profile, document.getElementById("btnRefly").hidden, document.getElementById("flyCard").hidden]')==['px4',True,True])
        check('no page errors', not errs, errs[:3])
        await b.close()
asyncio.run(main())
fails=[r for r in results if not r[1]]
for r in results: print(('PASS' if r[1] else 'FAIL'), r[0], '' if r[1] else r[2])
print(f'{len(results)-len(fails)}/{len(results)} passed')
