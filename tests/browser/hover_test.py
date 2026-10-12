# 第 4 批：懸停調參模式、馬達與感測器面板、姿態估測圖
import asyncio, os, json
from playwright.async_api import async_playwright
here = os.path.dirname(os.path.abspath(__file__))
results = []
def check(name, ok, info=''):
    results.append((name, bool(ok), info))
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); pg = await b.new_page(viewport={'width': 1440, 'height': 1000})
        errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('file://' + os.path.join(here, 'test.html')); await pg.wait_for_timeout(600)
        J = lambda js: pg.evaluate(js)
        vis = lambda i: J(f'!document.getElementById("{i}").hidden')
        await pg.click('#segAxis button[data-v="hover"]'); await pg.wait_for_timeout(1200)
        st = json.loads(await J('JSON.stringify([sim.axis, sim.armed, sim.landed, +(-sim.pos[2]).toFixed(2), sim.fmode, sim.profile, sim.sens.gyroNoise, sim.sens.gyroLpf])'))
        check('hover 起始：空中、已解鎖、2 m、Altitude、PX4、真機感測器', st == ['hover', True, False, 2.0, 'alt', 'px4', 3, 80], st)
        check('hover 面板：感測器卡、懸停指標顯示', await vis('sensorCard') and await vis('hoverStats'))
        check('hover 隱藏鏡頭切換、考照場地', not await vis('camRow') and not await vis('examRow') and not await vis('examHud'))
        check('懸停指標有數值', 'm' in await pg.inner_text('#hoverStatsGrid'))
        check('估測圖預設隱藏', not await vis('estCard'))
        # 馬達效率
        await J('const e=document.getElementById("eff0"); e.value=90; e.dispatchEvent(new Event("input"))'); await pg.wait_for_timeout(100)
        check('M1 效率 90%', await J('sim.env.motorEff[0]') == 0.9 and '90%' in await J('document.getElementById("quadSvg").innerHTML'))
        await J('["roll","pitch","yaw"].forEach(a=>{const P=sim.params[a]; P[Object.keys(P)[2]]=0;})'); await pg.wait_for_timeout(3000)
        off = await J('Math.hypot(sim.pos[0],sim.pos[1])')
        check('M1 90% + I=0 → 漂移', off > 0.5, off)
        # 估測
        await pg.click('#chkEst'); await pg.wait_for_timeout(300)
        check('估測開：估測圖與 Kalman 參數顯示', await vis('estCard') and await vis('estBox') and await vis('sensKf'))
        await pg.click('#chkUseAcc'); await pg.wait_for_timeout(100)
        check('只用陀螺儀：Kalman 參數隱藏', not await vis('sensKf') and await J('sim.sens.useAcc') is False)
        await pg.click('#chkUseGyro'); await pg.wait_for_timeout(100)
        check('不能兩個都取消', await J('sim.sens.useGyro') is True)
        await pg.wait_for_timeout(500)
        check('估測圖有資料', await J('sim.log.slice(-5).every(r=>Number.isFinite(r.e0)&&Number.isFinite(r.g0))'))
        bad = []
        for bid in ['bStick', 'bPos', 'bCmd', 'bOuter', 'bInner', 'bMix', 'bMot', 'bPlant']:
            if not await vis(bid): continue
            await pg.click('#' + bid); await pg.wait_for_timeout(60)
            t = await pg.inner_text('#popBody')
            if 'NaN' in t or 'undefined' in t or not t.strip(): bad.append(bid)
        await pg.keyboard.press('Escape')
        check('hover 彈出視窗沒有 NaN', not bad, bad)
        check('馬達彈出視窗顯示效率', '效率' in await J('Popover.blockDetail("bMot").html'))
        check('回授說明顯示感測器狀態', '陀螺儀量測值' in await pg.inner_text('#feedback'))
        # 重飛：回到 2 m，設定保留
        await pg.click('#btnRefly'); await pg.wait_for_timeout(300)
        st = json.loads(await J('JSON.stringify([sim.armed, +(-sim.pos[2]).toFixed(1), sim.env.motorEff[0], sim.sens.est])'))
        check('重飛：回到 2 m 已解鎖，感測器設定保留', st == [True, 2.0, 0.9, True], st)
        # 鍵盤
        await pg.keyboard.down('ArrowRight'); await pg.wait_for_timeout(1000); await pg.keyboard.up('ArrowRight')
        check('鍵盤可控制', await J('sim.pos[1]') > 0.3)
        # 按鈕
        await pg.click('#btnSensIdeal'); await pg.wait_for_timeout(100)
        check('全部理想', await J('sim.sensorsIdeal() && sim.env.motorEff.every(e=>e===1)') and not await vis('estCard'))
        await pg.click('#btnSensDefault'); await pg.wait_for_timeout(100)
        check('回到本模式預設', await J('sim.sens.gyroNoise') == 3)
        # 切換模式：感測器回到該模式預設
        await pg.click('#segAxis button[data-v="fly"]'); await pg.wait_for_timeout(300)
        check('自由飛行：感測器理想、面板顯示、鏡頭與考照顯示', await J('sim.sensorsIdeal()') and await vis('sensorCard') and await vis('camRow') and await vis('examRow') and not await vis('hoverStats'))
        await pg.click('#segAxis button[data-v="att3"]'); await pg.wait_for_timeout(300)
        check('三軸姿態：面板顯示、理想', await vis('sensorCard') and await J('sim.sensorsIdeal()'))
        await pg.click('#chkEst'); await pg.wait_for_timeout(600)
        check('三軸姿態也能開估測圖', await vis('estCard') and await J('Number.isFinite(sim.log[sim.log.length-1].t0)'))
        await pg.click('#segAxis button[data-v="roll"]'); await pg.wait_for_timeout(300)
        check('單軸：面板與估測圖隱藏', not await vis('sensorCard') and not await vis('estCard'))
        await pg.click('#segAxis button[data-v="hover"]'); await pg.wait_for_timeout(300)
        await pg.click('#segFmode button[data-v="stab"]'); await pg.wait_for_timeout(800)
        check('hover 切 Stabilized 仍維持高度（油門置中）', abs(await J('-sim.pos[2]') - 2) < 0.3, await J('-sim.pos[2]'))
        check('沒有頁面錯誤', not errs, errs[:3])
        await b.close()
    for n, ok, info in results: print(('PASS' if ok else 'FAIL'), n, info if not ok else '')
    print(f"{sum(o for _, o, _ in results)}/{len(results)} passed")
asyncio.run(main())
