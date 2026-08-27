(function(root,factory){
  const core=root&&root.ValtrenDashboardCore?root.ValtrenDashboardCore:(typeof require==='function'?require('./crm_dashboard_core.js'):null);
  const api=factory(core);
  if(typeof module==='object'&&module.exports)module.exports=api;
  if(root)root.ValtrenDashboardParticipationCore=api;
  if(core&&typeof core.buildDashboard==='function'&&!core.__participationIntegrityWrapped){
    const originalBuildDashboard=core.buildDashboard;
    core.buildDashboard=function(input={}){
      const snapshot=originalBuildDashboard(input);
      snapshot.participations=api.buildParticipationSummary(input.participations||[],input.payoutObligations||[],snapshot.units||[]);
      return snapshot;
    };
    core.__participationIntegrityWrapped=true;
  }
})(typeof globalThis!=='undefined'?globalThis:this,function(Core){
  'use strict';
  if(!Core)throw new Error('ValtrenDashboardCore indisponível para integridade de Participações');
  const num=(value)=>{const n=Number(value);return Number.isFinite(n)?n:0;};
  const roundMoney=(value)=>Core.roundMoney(value);
  const sum=(rows,selector)=>roundMoney((rows||[]).reduce((total,row)=>total+num(selector(row)),0));

  function participationUnitKey(row={}){
    if(row.productId)return `product:${row.productId}`;
    if(row.serviceId)return `service:${row.serviceId}`;
    if(row.businessUnitId)return `business_unit:${row.businessUnitId}`;
    return 'unassigned:unassigned';
  }

  function buildParticipationSummary(participations=[],payoutObligations=[],units=[]){
    const eligible=(participations||[]).filter((row)=>row&&!row.isDemo);
    const participatingKeys=new Set(eligible.map(participationUnitKey));
    const participatingUnits=(units||[]).filter((unit)=>participatingKeys.has(unit.key));
    const totalResult=sum(participatingUnits,(unit)=>unit.operatingResult);
    const thirdParty=sum(eligible,(row)=>Math.max(0,num(row.participationAmount??row.amountDue)));
    const valtren=sum(participatingUnits,(unit)=>unit.valtrenResult);
    const obligations=(payoutObligations||[]).filter((row)=>row&&!row.isDemo);
    const repassed=sum(obligations,(row)=>row.amountPaid);
    const pending=sum(obligations.filter((row)=>!['paid','cancelled','superseded'].includes(row.status)),(row)=>row.openBalance);
    const overdue=sum(obligations.filter((row)=>row.status==='overdue'),(row)=>row.openBalance);
    const scheduled=sum(obligations.filter((row)=>row.status==='open'&&row.dueDate),(row)=>row.openBalance);
    return {totalResult,valtren,thirdParty,repassed,pending,scheduled,overdue,participatingUnitCount:participatingUnits.length,obligations:Core.clone(obligations)};
  }

  return {participationUnitKey,buildParticipationSummary};
});
