"""通过 agent-browser 保存两侧稳定截图和布局测量，不注入生产响应。"""
import json, subprocess, sys
from pathlib import Path

out = Path(__file__).resolve().parent

def browser(session, *args):
    result = subprocess.run(['agent-browser', '--session', session, '--json', *args], text=True, capture_output=True, check=True)
    data = json.loads(result.stdout)
    if not data['success']:
        raise RuntimeError(data)
    return data['data']

def evaluate(session, source):
    return browser(session, 'eval', source)['result']

def capture(session, name):
    evaluate(session, '(async()=>{await document.fonts.ready;await Promise.all([...document.images].map(i=>i.decode().catch(()=>{})));await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));return true})()')
    browser(session, 'mouse', 'move', '0', '0')
    browser(session, 'screenshot', str(out / (name + '.png')))
    result = evaluate(session, '''(()=>{
      const selectors=['header','main','.welcome','.welcome h1','.welcome-body','.horizon','.flow-steps','.page-heading','.workbench','.aside-identity','.profile-form','.avatar-field','.review-profile','.review-profile .identifier','.form-footer','.back-button','.identity-profile','.identity-identifiers','.identity-stage','.identity-sculpture','.identity-plate','.center-state','footer'];
      return {url:location.href,viewport:[innerWidth,innerHeight],scroll:[scrollX,scrollY],overflow:document.documentElement.scrollWidth>innerWidth,regions:Object.fromEntries(selectors.map(s=>{const e=document.querySelector(s);if(!e)return [s,null]; const r=e.getBoundingClientRect(),c=getComputedStyle(e);return [s,{x:r.x,y:r.y,width:r.width,height:r.height,font:c.font,gap:c.gap,padding:c.padding}]}))};
    })()''')
    (out / (name + '.json')).write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    assert not result['overflow'], name + ': 页面横向溢出'
    return result

if __name__ == '__main__':
    if sys.argv[1] == 'capture':
        capture(sys.argv[2], sys.argv[3])
        print(sys.argv[3] + ': 截图、测量与无横向溢出检查通过')
    else:
        name, ref_session, app_session = sys.argv[1:4]
        ref = capture(ref_session, 'prototype-'+name)
        app = capture(app_session, 'after-'+name)
        assert ref['viewport'] == app['viewport']
        differences = {}
        for key, actual in app['regions'].items():
            expected = ref['regions'].get(key)
            if actual and expected:
                diff = {prop:round(actual[prop]-expected[prop],3) for prop in ['x','y','width','height'] if abs(actual[prop]-expected[prop]) > .1}
                if diff: differences[key]=diff
        (out / (name+'-comparison.json')).write_text(json.dumps(differences,ensure_ascii=False,indent=2)+'\n')
        print(name, json.dumps(differences,ensure_ascii=False))
