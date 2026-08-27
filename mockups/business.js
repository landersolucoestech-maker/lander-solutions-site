const CRM_MOCK_BUSINESS={
  units:[
    {id:'mock_bu_platform',code:'BU-PLATFORM',name:'Plataforma Digital e Sistemas',description:'Unidade principal responsável pelos produtos SaaS e automações de operação.',status:'active'},
    {id:'mock_bu_services',code:'BU-SERVICES',name:'Serviços Profissionais e Consultoria Especializada',description:'Unidade com nome propositalmente longo para validar wrapping e truncation em tabelas preenchidas.',status:'active'},
    {id:'mock_bu_corporate',code:'BU-CORP',name:'Operações Corporativas',description:'Estrutura de suporte e governança.',status:'active'}
  ],
  products:[
    {id:'mock_product_alpha',code:'PROD-ALPHA',name:'Valtren Flow Suite',category:'Software SaaS',revenueModel:'subscription',billingFrequency:'monthly',referencePrice:8900,currency:'BRL',status:'active',businessUnitId:'mock_bu_platform'},
    {id:'mock_product_beta',code:'PROD-BETA',name:'Valtren Intelligence Operations Hub Enterprise',category:'Plataforma de inteligência operacional de alta complexidade',revenueModel:'subscription',billingFrequency:'annual',referencePrice:72000,currency:'BRL',status:'active',businessUnitId:'mock_bu_platform'},
    {id:'mock_product_gamma',code:'PROD-GAMMA',name:'Valtren Portal',category:'Portal digital',revenueModel:'license',billingFrequency:'annual',referencePrice:24000,currency:'BRL',status:'active',businessUnitId:'mock_bu_platform'}
  ],
  services:[
    {id:'mock_service_strategy',code:'SVC-STRATEGY',name:'Consultoria Estratégica',category:'Consultoria',pricingModel:'project',referencePrice:35000,currency:'BRL',status:'active',businessUnitId:'mock_bu_services'},
    {id:'mock_service_impl',code:'SVC-IMPL',name:'Implementação e Integração de Operações Digitais',category:'Implementação técnica especializada',pricingModel:'project',referencePrice:48000,currency:'BRL',status:'active',businessUnitId:'mock_bu_services'},
    {id:'mock_service_support',code:'SVC-SUPPORT',name:'Suporte Operacional',category:'Suporte',pricingModel:'retainer',referencePrice:12000,currency:'BRL',status:'active',businessUnitId:'mock_bu_services'}
  ]
};
function crmMockSeedBusiness(ctx){
  const stateData=ValtrenBusinessCore.createState({now:ctx.dates.now});
  const service=ValtrenBusinessCore.createService(stateData,{now:ctx.dates.now,idFactory:crmMockIds('business'),actorProvider:()=>null});
  CRM_MOCK_BUSINESS.units.forEach(x=>service.createBusinessUnit({...x,isDemo:false}));
  CRM_MOCK_BUSINESS.products.forEach(x=>service.createProduct({...x,isDemo:false}));
  CRM_MOCK_BUSINESS.services.forEach(x=>service.createService({...x,isDemo:false}));
  state.crmBusinessCatalog=stateData;state.__crmBusinessService=service;
  return service;
}
