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

def main():
 p=argparse.ArgumentParser();p.add_argument('--base-url',required=True);p.add_argument('--output-dir',required=True);a=p.parse_args();out=Path(a.output_dir);out.mkdir(parents=True,exist_ok=True)
 opts=Options();opts.add_argument('--headless=new');opts.add_argument('--no-sandbox');opts.add_argument('--disable-dev-shm-usage');opts.set_capability('goog:loggingPrefs',{'browser':'ALL'})
 d=webdriver.Chrome(options=opts);failures=[];evidence={}
 d.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument',{'source':"window.__mockCapturedErrors=[];window.addEventListener('error',e=>window.__mockCapturedErrors.push({type:'error',message:String(e.message||''),stack:String(e.error&&e.error.stack||''),source:String(e.filename||''),line:e.lineno||0,col:e.colno||0}));window.addEventListener('unhandledrejection',e=>window.__mockCapturedErrors.push({type:'rejection',message:String(e.reason&&e.reason.message||e.reason||''),stack:String(e.reason&&e.reason.stack||'')}));"})
 try:
  d.set_window_size(1440,1200);d.get(a.base_url.rstrip('/')+'/?mock=1#/crm/dashboard')
  try:WebDriverWait(d,20).until(lambda x:x.execute_script('return !!window.__VALTREN_MOCK_MODE__'))
  except TimeoutException:
   logs,errors=browser_errors(d);evidence['console']=logs;evidence['consoleSevere']=errors;evidence['capturedErrors']=js_safe(d,'return window.__mockCapturedErrors||[]');evidence['readyState']=d.execute_script('return document.readyState');evidence['url']=d.current_url;evidence['bodyText']=d.find_element('tag name','body').text[:4000]
   failures.append('BOOTSTRAP_TIMEOUT')
   if evidence['capturedErrors']:failures.append('Captured JS error: '+json.dumps(evidence['capturedErrors'],ensure_ascii=False)[:12000])
   elif errors:failures.append('Console SEVERE: '+json.dumps(errors,ensure_ascii=False)[:5000])
   d.save_screenshot(str(out/'dashboard-mock-bootstrap-failure.png'));raise RuntimeError('mock bootstrap flag ausente')
  time.sleep(1);k=d.execute_script('return window.__VALTREN_MOCK_MODE__.kpis()') or {};evidence['kpis']=k
  for key,val in EXPECTED.items():
   if key not in k or not close(k[key],val):failures.append(f'KPI {key}: {k.get(key)} != {val}')
  calcs=d.execute_script("return (window.state?.crmEconomicParticipations?.calculations||[]).filter(x=>x.id==='mock_participation_a'||x.id==='mock_participation_b').map(x=>({id:x.id,base:x.distributableBase,amount:x.participationAmount,status:x.calculationStatus,consistency:x.consistencyStatus,workflow:x.workflowStatus}))");evidence['participations']=calcs;by={x['id']:x for x in calcs}
  for cid,amount in [('mock_participation_a',14400),('mock_participation_b',9600)]:
   x=by.get(cid)
   if not x or not close(x.get('base',0),96000) or not close(x.get('amount',0),amount):failures.append(f'Participation {cid} inválida: {x}')
  if len(calcs)==2 and not close(sum(float(x.get('amount') or 0) for x in calcs),24000):failures.append('Participações não somam 24000')
  keys=d.execute_script('return Object.keys(localStorage)');evidence['storageKeys']=keys;bad=[x for x in keys if not x.startswith('valtren:mock:')]
  if bad:failures.append('Mock contaminou storage normal: '+','.join(bad))
  body=d.find_element('tag name','body').text;evidence['bodyHasEmptyFinancialState']='Nenhum dado financeiro disponível' in body
  if evidence['bodyHasEmptyFinancialState']:failures.append('Dashboard Mock permaneceu em empty state financeiro')
  if 'Dados de demonstração' not in body:failures.append('Mock mode bar ausente')
  logs,errors=browser_errors(d);evidence['console']=logs;evidence['consoleSevere']=errors;evidence['capturedErrors']=js_safe(d,'return window.__mockCapturedErrors||[]')
  if errors:failures.append('Console SEVERE: '+json.dumps(errors,ensure_ascii=False)[:5000])
  d.save_screenshot(str(out/'dashboard-mock-1440.png'));evidence['url']=d.current_url
 except Exception as e:
  if not failures:failures.append(f'BOOTSTRAP: {type(e).__name__}: {e}')
 finally:d.quit()
 result={'status':'PASS' if not failures else 'FAIL','failures':failures,**evidence};(out/'mock-mode-result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result,ensure_ascii=False,indent=2))
 if failures:raise SystemExit(1)
if __name__=='__main__':main()
