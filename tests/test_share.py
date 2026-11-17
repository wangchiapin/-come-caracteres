# 吃字小籠包：分享成績鈕＋ ?ref=share 記號測試（假 Firebase 記錄 visits／plays 寫入）
# 用法：python3 tests/test_share.py
import sys, json
from playwright.sync_api import sync_playwright
import common
from common import *

R = Runner()
URL = 'https://wangchiapin.github.io/-come-caracteres/?ref=share'

def stubs(share='ok', clip='ok'):
    s = "window.__shared=[];window.__copied=[];"
    if share == 'none': s += "try{Object.defineProperty(navigator,'share',{value:undefined,configurable:true});}catch(e){}"
    else:
        body = "window.__shared.push(d);"
        if share == 'abort': body += "const e=new Error('x');e.name='AbortError';throw e;"
        if share == 'hang': body += "await new Promise(r=>setTimeout(r,600));"
        s += "navigator.share=async d=>{%s};" % body
    s += "document.execCommand=()=>%s;" % ('false' if clip == 'fail' else 'true')
    s += "try{Object.defineProperty(navigator,'clipboard',{value:{writeText:async t=>{%s}},configurable:true});}catch(e){}" % ("throw new Error('no')" if clip == 'fail' else "window.__copied.push(t)")
    return s

def page(p, settings=None, name='Ana', query='', share='ok', clip='ok', wait=1500):
    init = stubs(share, clip)
    if name is not None: init += "localStorage.setItem('cc_name',%s);" % json.dumps(json.dumps(name))
    return open_page(p, query=query, settings=settings, wait=wait, extra_init=init)

def over(pg, score=300, noname=False):
    pg.click('#go'); pg.wait_for_timeout(300)
    if noname: pg.evaluate("localStorage.removeItem('cc_name'); memName=''")   # 沒暱稱才不會自動上傳、不會跳到排行榜
    pg.evaluate("state='test'")
    pg.evaluate("G.score=%d; G.lives=1; hitPlayer();" % score); pg.wait_for_timeout(500)

def ids(pg): return pg.evaluate("[...document.querySelectorAll('#ov button')].map(b=>b.id)")
def txt(pg, sel): return ' '.join(pg.inner_text(sel).split())
def ops(pg): return pg.evaluate("window.__ops||[]")

base = {'v': 1, 'script': 'trad', 'lang': 'es', 'phon': 'pinyin', 'rate': 'normal'}
with sync_playwright() as p:
    print('結算畫面的分享鈕')
    b, pg, errs = page(p, settings=base)
    over(pg, 300)
    order = ids(pg)
    R.check(order.index('shareBtn') > order.index('again') and order.index('shareBtn') < order.index('menu'), '分享鈕在「再玩一次」之後、「主選單」之前 %s' % order)
    t = txt(pg, '#shareBtn')
    R.check('分享成績' in t and 'Compartir resultado' in t, '文字：分享成績＋Compartir resultado：%s' % t)
    st = pg.evaluate("(()=>{const c=getComputedStyle(document.getElementById('shareBtn'));return [c.backgroundColor,parseFloat(c.borderTopWidth),document.getElementById('shareBtn').className]})()")
    R.check(st[0] == 'rgb(255, 255, 255)' and st[1] >= 1, '空心外框樣式（白底有框）%s' % st)
    R.check('btn-restart' not in st[2], '沒有用 .btn-restart')
    pg.click('#shareBtn'); pg.wait_for_timeout(200)
    sh = pg.evaluate("window.__shared")
    R.check(len(sh) == 1, '呼叫系統分享選單一次')
    R.check(sh and sh[0]['url'] == URL, '連結＝公開頁＋?ref=share：%s' % (sh and sh[0]['url']))
    R.check(sh and 'Ana' in sh[0]['text'] and '300' in sh[0]['text'] and 'Come Caracteres' in sh[0]['text'], '西文句子含暱稱、分數、遊戲名：%s' % (sh and sh[0]['text']))
    R.check(not errs, '沒有網頁錯誤 %s' % errs)
    b.close()

    print('語言／字體跟著設定')
    b, pg, errs = page(p, settings=dict(base, script='simp', lang='zh'), name=None)
    pg.fill('#nmMenu', 'Bo'); over(pg, 200)
    R.check(txt(pg, '#shareBtn') == '分享成绩', '简体＋純中文：只有「分享成绩」：%s' % txt(pg, '#shareBtn'))
    pg.evaluate("localStorage.removeItem('cc_name'); memName=''"); pg.click('#shareBtn'); pg.wait_for_timeout(200)
    sh = pg.evaluate("window.__shared")
    R.check(sh and sh[0]['text'].startswith('我在「吃字小笼包」拿了') and '超越我吗' in sh[0]['text'], '简体句子，沒暱稱用「我」：%s' % (sh and sh[0]['text']))
    b.close()
    b, pg, errs = page(p, settings=dict(base, lang='en'), name='Bo')
    over(pg, 200)
    R.check('Share result' in txt(pg, '#shareBtn'), '英文介面：Share result')
    pg.click('#shareBtn'); pg.wait_for_timeout(200)
    sh = pg.evaluate("window.__shared")
    R.check(sh and sh[0]['text'].startswith('Bo scored ') and 'Can you beat me' in sh[0]['text'], '英文句子帶暱稱：%s' % (sh and sh[0]['text']))
    b.close()

    print('分享選單的各種結果')
    b, pg, errs = page(p, settings=base, share='abort')
    over(pg); before = pg.inner_text('#shareBtn')
    pg.click('#shareBtn'); pg.wait_for_timeout(200)
    R.check(pg.inner_text('#shareBtn') == before and pg.evaluate("window.__copied") == [], '玩家關掉選單：文字不變、不複製')
    b.close()
    # 沒填暱稱就不會自動上傳（上傳成功後遊戲會自己切到排行榜，按鈕就不在了），才看得到文字恢復
    b, pg, errs = page(p, settings=base, share='none', name=None)
    pg.fill('#nmMenu', 'Ana')
    over(pg, noname=True); pg.click('#shareBtn'); pg.wait_for_timeout(250)
    cp = pg.evaluate("window.__copied")
    R.check(len(cp) == 1 and cp[0].endswith('\n' + URL), '不支援分享選單：複製「句子＋連結」')
    R.check('已複製' in pg.inner_text('#shareBtn') and 'Copiado' in pg.inner_text('#shareBtn'), '按鈕顯示已複製')
    pg.wait_for_timeout(2500)
    R.check('分享成績' in pg.inner_text('#shareBtn'), '約 2 秒後文字恢復')
    b.close()
    b, pg, errs = page(p, settings=base, share='none', clip='fail')
    over(pg); pg.click('#shareBtn'); pg.wait_for_timeout(250)
    R.check('複製失敗' in pg.inner_text('#shareBtn') and 'No se pudo' in pg.inner_text('#shareBtn'), '連複製也失敗：顯示複製失敗')
    b.close()
    b, pg, errs = page(p, settings=base, share='hang')
    over(pg)
    pg.evaluate("document.getElementById('shareBtn').click();document.getElementById('shareBtn').click()"); pg.wait_for_timeout(900)
    R.check(pg.evaluate("window.__shared.length") == 1, '連點兩下只分享一次')
    b.close()

    print('排行榜畫面的分享鈕（有暱稱會自動上傳並跳到排行榜）')
    b, pg, errs = page(p, settings=base)
    over(pg, 300); pg.wait_for_timeout(2500)
    check_ids = ids(pg)
    R.check(pg.evaluate("document.querySelector('#ov h1') && document.querySelector('#ov h1').textContent.includes('🏆')") and 'lbBack' in check_ids, '自動上傳後跳到排行榜：%s' % check_ids)
    R.check('shareBtn' in check_ids and check_ids.index('shareBtn') < check_ids.index('lbBack'), '排行榜畫面有分享鈕，在「返回」上方：%s' % check_ids)
    bt = txt(pg, '#shareBtn')
    R.check('分享成績' in bt and 'Compartir resultado' in bt, '排行榜上的鈕文字：%s' % bt)
    R.check(pg.evaluate("(()=>{const c=getComputedStyle(document.getElementById('shareBtn'));return c.backgroundColor==='rgb(255, 255, 255)'&&parseFloat(c.borderTopWidth)===2&&!document.getElementById('shareBtn').classList.contains('btn-restart')})()"), '空心外框 2px、白底、不是 btn-restart')
    pg.click('#shareBtn'); pg.wait_for_timeout(300)
    sh = pg.evaluate("window.__shared")
    R.check(len(sh) == 1 and '300' in sh[0]['text'] and sh[0]['url'].endswith('?ref=share'), '排行榜上按分享：帶本局分數與 ?ref=share：%s' % sh)
    pg.evaluate("document.getElementById('shareBtn').click();document.getElementById('shareBtn').click()"); pg.wait_for_timeout(900)
    R.check(pg.evaluate("window.__shared.length") <= 3, '排行榜上連點不會爆量 %d' % pg.evaluate("window.__shared.length"))
    pg.click('#lbBack'); pg.wait_for_timeout(300)
    R.check('again' in ids(pg) and 'shareBtn' in ids(pg), '按返回回到結算畫面（再玩一次、分享鈕都在）：%s' % ids(pg))
    pg.click('#lb'); pg.wait_for_timeout(500)
    R.check('shareBtn' in ids(pg), '手動點🏆排行榜也有分享鈕：%s' % ids(pg))
    b.close()

    print('排行榜：不是從結算進來就沒有分享鈕')
    b, pg, errs = page(p, settings=base)
    pg.click('#lb'); pg.wait_for_timeout(500)
    R.check('lbBack' in ids(pg) and 'shareBtn' not in ids(pg), '主頁開排行榜：沒有分享鈕 %s' % ids(pg))
    b.close()
    b, pg, errs = page(p, settings=base)
    over(pg, 0); pg.wait_for_timeout(300)
    pg.click('#lb'); pg.wait_for_timeout(500)
    R.check('lbBack' in ids(pg) and 'shareBtn' not in ids(pg), '0 分進排行榜：沒有分享鈕 %s' % ids(pg))
    R.check(not errs, '沒有網頁錯誤 %s' % errs)
    b.close()

    print('0 分不顯示')
    b, pg, errs = page(p, settings=base)
    pg.click('#go'); pg.wait_for_timeout(300); pg.evaluate("state='test'")
    pg.evaluate("G.score=0; G.lives=1; hitPlayer();"); pg.wait_for_timeout(400)
    R.check('shareBtn' not in ids(pg), '0 分沒有分享鈕 %s' % ids(pg))
    b.close()

    print('?ref=share 記號')
    def refcase(query, label, expect):
        b, pg, errs = page(p, settings=base, query=query, wait=3200)
        pg.click('#go'); pg.wait_for_timeout(500)
        o = [x for x in ops(pg) if x['p'].startswith('visits/') or x['k'] == 'add']
        R.check(len(o) >= 2 and all((x['d'].get('ref') == expect) if expect else ('ref' not in x['d']) for x in o), '%s %s' % (label, o))
        if expect: R.check(pg.evaluate("sessionStorage.getItem('hg.ref')") == expect, '記號暫存在 sessionStorage')
        b.close()
    refcase('?ref=share', '訪客與開始紀錄都帶 ref=share', 'share')
    refcase('', '沒有 ref：紀錄不帶 ref 欄位', None)
    refcase('?ref=BAD%20x!', '不合法的 ref 被忽略', None)
    refcase('?ref=Share', '大寫 ref 轉成小寫', 'share')

print('FAILS', R.fails); sys.exit(1 if R.fails else 0)
