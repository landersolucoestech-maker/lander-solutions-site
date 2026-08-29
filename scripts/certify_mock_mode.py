#!/usr/bin/env python3
import argparse,json,time
from pathlib import Path
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait

EXPECTED={'grossRevenue':300000,'deductions':30000,'netRevenue':270000,'directCosts':90000,'operatingExpenses':60000,'operatingResult':120000,'thirdPartyParticipation':24000,'valtrenResult':96000}
def close(a,b): return abs(float(a)-float(b))<0.005
def browser_errors(driver):
 logs=driver.get_log('browser');return logs,[x for x in logs if x.get('level')=='SEVERE']
def js_safe(driver,script):
 try:return driver.execute_script(script)
 except Exception as e:return {'diagnosticError':f'{type(e).__name__}: {e}'}

def wait_mock(d,failures,evidence,label):
 try:WebDriverWait(d,20).until(lambda x:x.execute_script('return !!window.__VALTREN_MOCK_MODE__'))
 except TimeoutException:
  logs,errors=browser_errors(d);evidence[f'{label}Console']=logs;evidence[f'{label}ConsoleSevere']=errors;evidence[f'{label}CapturedErrors']=js_safe(d,'return window.__mockCapturedErrors||[]');evidence[f'{label}ReadyState']=d.execute_script('return document.readyState');evidence[f'{label}Url']=d.current_url;evidence[f'{label}BodyText']=d.find_element('tag name','body').text[:4000]
  failures.append(f'{label}: BOOTSTRAP_TIMEOUT')
  d.save_screenshot(str(Path(evidence['outputDir'])/f'{label}-mock-bootstrap-failure.png'))
  return False
 return True

def main():
 p=argparse.ArgumentParser();p.add_argument('--base-url',required=True);p.add_argument('--output-dir',required=True);a=p.parse_args();out=Path(a.output_dir);out.mkdir(parents=True,exist_ok=True)
 opts=Options();opts.add_argument('--headless=new');opts.add_argument('--no-sandbox');opts.add_argument('--disable-dev-shm-usage');opts.set_capability('goog:loggingPrefs',{'browser':'ALL'})
 d=webdriver.Chrome(options=opts);failures=[];evidence={'outputDir':str(out)}
 d.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument',{'source':"window.__mockCapturedErrors=[];window.addEventListener('error',e=>window.__mockCapturedErrors.push({type:'error',message:String(e.message||''),stack:String(e.error&&e.error.stack||''),source:String(e.filename||''),line:e.lineno||0,col:e.colno||0}));window.addEventListener('unhandledrejection',e=>window.__mockCapturedErrors.push({type:'rejection',message:String(e.reason&&e.reason.message||e.reason||''),stack:String(e.reason&&e.reason.stack||'')}));"})
 try:
  url=a.base_url.rstrip('/')+'/?mock=1#/crm/dashboard';d.set_window_size(1440,1200);d.get(url)
  if not wait_mock(d,failures,evidence,'initial'):raise RuntimeError('mock bootstrap flag ausente')
  time.sleep(1);version=d.execute_script('return window.__VALTREN_MOCK_MODE__.version');evidence['version']=version
  if version!=2:failures.append(f'Mock schema version {version} != 2')
  k=d.execute_script('return window.__VALTREN_MOCK_MODE__.kpis()') or {};evidence['kpis']=k
  for key,val in EXPECTED.items():
   if key not in k or not close(k[key],val):failures.append(f'KPI {key}: {k.get(key)} != {val}')
  calcs=d.execute_script('return window.__VALTREN_MOCK_MODE__.participations()') or [];evidence['participations']=calcs;by={x['id']:x for x in calcs}
  for cid,amount in [('mock_participation_a',14400),('mock_participation_b',9600)]:
   x=by.get(cid)
   if not x or not close(x.get('base',0),96000) or not close(x.get('amount',0),amount):failures.append(f'Participation {cid} inválida: {x}')
  if len(calcs)==2 and not close(sum(float(x.get('amount') or 0) for x in calcs),24000):failures.append('Participações não somam 24000')
  keys=d.execute_script('return Object.keys(localStorage)');evidence['storageKeys']=keys;bad=[x for x in keys if not x.startswith('valtren:mock:')]
  if bad:failures.append('Mock contaminou storage normal: '+','.join(bad))
  body=d.find_element('tag name','body').text;evidence['bodyHasEmptyFinancialState']='Nenhum dado financeiro disponível' in body
  if evidence['bodyHasEmptyFinancialState']:failures.append('Dashboard Mock permaneceu em empty state financeiro')
  if 'Dados de demonstração' not in body:failures.append('Mock mode bar ausente')
  # Regression: a same-version but structurally incomplete persisted snapshot must never brick the app.
  d.execute_script("localStorage.setItem('valtren:mock:runtime.v2',JSON.stringify({version:2,state:{}}));")
  d.get(url)
  if not wait_mock(d,failures,evidence,'recovery'):raise RuntimeError('mock recovery bootstrap flag ausente')
  time.sleep(1);recovered=d.execute_script('return window.__VALTREN_MOCK_MODE__.kpis()') or {};evidence['recoveredKpis']=recovered
  for key,val in EXPECTED.items():
   if key not in recovered or not close(recovered[key],val):failures.append(f'Recovery KPI {key}: {recovered.get(key)} != {val}')
  recovery_body=d.find_element('tag name','body').text;evidence['recoveryBodyLength']=len(recovery_body)
  if not recovery_body.strip():failures.append('Recovery resultou em página branca')
  if 'Dados de demonstração' not in recovery_body:failures.append('Recovery não restaurou Mock Mode bar')
  logs,errors=browser_errors(d);evidence['console']=logs;evidence['consoleSevere']=errors;evidence['capturedErrors']=js_safe(d,'return window.__mockCapturedErrors||[]')
  if errors:failures.append('Console SEVERE: '+json.dumps(errors,ensure_ascii=False)[:5000])
  d.save_screenshot(str(out/'dashboard-mock-1440.png'));evidence['url']=d.current_url
 except Exception as e:
  if not failures:failures.append(f'BOOTSTRAP: {type(e).__name__}: {e}')
 finally:d.quit()
 evidence.pop('outputDir',None);result={'status':'PASS' if not failures else 'FAIL','failures':failures,**evidence};(out/'mock-mode-result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result,ensure_ascii=False,indent=2))
 if failures:raise SystemExit(1)
if __name__=='__main__':main()
