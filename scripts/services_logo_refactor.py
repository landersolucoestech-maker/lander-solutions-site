from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / 'content.js'
APP = ROOT / 'app.js'
CSS = ROOT / 'assets' / 'valtren-brand.css'

SERVICES_PT = [
    {
        'id':'s1','slug':'sistemas-de-gestao-e-erp','title':'Sistemas de Gestão e ERP','category':'Tecnologia',
        'shortDescription':'Sistemas sob medida para centralizar processos, dados e rotinas operacionais em uma única plataforma.',
        'description':'Projetamos e desenvolvemos sistemas de gestão e ERPs personalizados de acordo com a operação real da empresa, conectando áreas administrativas, comerciais, financeiras e operacionais com arquitetura preparada para evolução.',
        'bullets':['Mapeamento de processos e regras de negócio','Módulos administrativos, comerciais, financeiros e operacionais','Gestão de usuários, perfis, empresas e permissões','Dashboards, indicadores e relatórios gerenciais','Fluxos, aprovações, notificações e rotinas automatizadas','IA, automações, integrações e APIs incorporadas quando aplicáveis'],
        'visible':True,
    },
    {
        'id':'s2','slug':'saas-e-mvp','title':'SaaS e MVP','category':'Tecnologia',
        'shortDescription':'Produtos digitais estruturados para validar, lançar e evoluir modelos de negócio baseados em software.',
        'description':'Transformamos ideias e operações em produtos SaaS e MVPs funcionais, com definição de escopo, experiência do usuário, arquitetura, desenvolvimento e base técnica preparada para crescimento após a validação.',
        'bullets':['Descoberta, definição de escopo e priorização do MVP','Arquitetura SaaS e estruturas multi-tenant','Cadastro, autenticação, perfis e controle de acesso','Planos, assinaturas, pagamentos e regras comerciais','Métricas, painéis e recursos administrativos','IA, automações e integrações incorporadas à evolução do produto'],
        'visible':True,
    },
    {
        'id':'s3','slug':'crm-personalizado','title':'CRM Personalizado','category':'Tecnologia',
        'shortDescription':'CRMs desenvolvidos em torno do processo comercial real da empresa, sem obrigar a operação a se adaptar a uma ferramenta genérica.',
        'description':'Criamos CRMs personalizados para organizar leads, oportunidades, clientes, propostas, tarefas e relacionamento comercial, com fluxos, dados e automações definidos conforme o modelo de vendas e atendimento do negócio.',
        'bullets':['Captação e qualificação de leads','Funis, etapas, oportunidades e previsão comercial','Clientes, contatos, propostas, atividades e tarefas','Regras de distribuição, follow-up e notificações','Dashboards e indicadores comerciais','Integrações, automações e recursos de IA incorporados ao fluxo'],
        'visible':True,
    },
    {
        'id':'s4','slug':'portais-web-e-plataformas-ead','title':'Portais Web e Plataformas EAD','category':'Tecnologia',
        'shortDescription':'Ambientes digitais autenticados para clientes, equipes, comunidades, alunos e operações de conteúdo.',
        'description':'Desenvolvemos portais web, áreas do cliente, intranets e plataformas EAD com experiências autenticadas, gestão de usuários, conteúdos, permissões e recursos operacionais adaptados ao público e ao modelo de negócio.',
        'bullets':['Portais corporativos, áreas do cliente e intranets','Plataformas EAD, cursos, trilhas e bibliotecas de conteúdo','Gestão de alunos, usuários, perfis e permissões','Aulas, materiais, progresso, avaliações e certificados','Assinaturas, pagamentos e áreas exclusivas quando necessários','Integrações, automações e IA incorporadas conforme o projeto'],
        'visible':True,
    },
    {
        'id':'s5','slug':'sites-institucionais-e-plataformas-web','title':'Sites Institucionais e Plataformas Web','category':'Tecnologia',
        'shortDescription':'Presença digital profissional conectada aos objetivos comerciais, institucionais e operacionais da empresa.',
        'description':'Criamos sites institucionais e plataformas web responsivas, rápidas e escaláveis, com conteúdo estruturado, experiência de usuário, SEO técnico e conexão com os sistemas e canais necessários ao negócio.',
        'bullets':['Sites institucionais, corporativos e comerciais','Catálogos, páginas dinâmicas e áreas restritas','CMS e gestão de conteúdo quando necessário','SEO técnico, acessibilidade, desempenho e responsividade','Conexão com CRM, ERP, WhatsApp, analytics e serviços externos','Automações e recursos inteligentes integrados quando agregam valor'],
        'visible':True,
    },
    {
        'id':'s6','slug':'landing-pages-e-paginas-de-conversao','title':'Landing Pages e Páginas de Conversão','category':'Tecnologia',
        'shortDescription':'Páginas focadas em campanhas, captação de leads, lançamentos e geração de oportunidades comerciais.',
        'description':'Desenvolvemos landing pages e páginas de conversão com foco em velocidade, clareza da oferta, experiência mobile e mensuração, conectando os leads diretamente aos fluxos comerciais e ferramentas utilizadas pela empresa.',
        'bullets':['Landing pages para campanhas, serviços, produtos e lançamentos','Formulários e captação estruturada de leads','Integração direta com CRM e fluxos comerciais','Analytics, pixels, eventos e acompanhamento de conversão','SEO, desempenho, responsividade e boas práticas técnicas','Automação de respostas, distribuição e qualificação quando aplicável'],
        'visible':True,
    },
    {
        'id':'s7','slug':'modernizacao-e-evolucao-de-sistemas','title':'Modernização e Evolução de Sistemas','category':'Tecnologia',
        'shortDescription':'Evolução de softwares existentes para melhorar arquitetura, experiência, desempenho, segurança e capacidade de crescimento.',
        'description':'Atuamos sobre sistemas e plataformas já existentes para corrigir limitações técnicas, modernizar interfaces, reorganizar arquitetura e adicionar novas capacidades sem exigir que toda a operação seja reconstruída do zero.',
        'bullets':['Diagnóstico técnico e funcional do sistema atual','Refatoração e modernização de arquitetura','Redesign de interface e melhoria da experiência do usuário','Desempenho, estabilidade, segurança e qualidade','Migração tecnológica e evolução de módulos existentes','Novas integrações, automações e recursos de IA quando fizerem sentido'],
        'visible':True,
    },
]

SERVICES_EN = {
's1':{'title':'Management Systems and ERP','shortDescription':'Custom systems that centralize processes, data and operational routines in a single platform.','description':'We design and build management systems and custom ERPs around the company’s real operation, connecting administrative, commercial, financial and operational areas with an architecture prepared to evolve.','bullets':['Process and business-rule mapping','Administrative, commercial, financial and operational modules','Users, roles, companies and permissions','Dashboards, indicators and management reports','Workflows, approvals, notifications and automated routines','AI, automation, integrations and APIs embedded when applicable']},
's2':{'title':'SaaS and MVP','shortDescription':'Digital products structured to validate, launch and evolve software-based business models.','description':'We turn ideas and operations into functional SaaS products and MVPs, covering scope, user experience, architecture, development and a technical foundation prepared for growth after validation.','bullets':['Discovery, scope definition and MVP prioritization','SaaS architecture and multi-tenant structures','Registration, authentication, roles and access control','Plans, subscriptions, payments and commercial rules','Metrics, dashboards and administrative features','AI, automation and integrations embedded into product evolution']},
's3':{'title':'Custom CRM','shortDescription':'CRMs built around the company’s real sales process instead of forcing the operation into a generic tool.','description':'We create custom CRMs to organize leads, opportunities, customers, proposals, tasks and commercial relationships, with workflows, data and automation defined around the company’s sales and service model.','bullets':['Lead capture and qualification','Pipelines, stages, opportunities and sales forecasting','Customers, contacts, proposals, activities and tasks','Distribution rules, follow-up and notifications','Sales dashboards and indicators','Integrations, automation and AI capabilities embedded into the workflow']},
's4':{'title':'Web Portals and E-learning Platforms','shortDescription':'Authenticated digital environments for customers, teams, communities, students and content operations.','description':'We develop web portals, customer areas, intranets and e-learning platforms with authenticated experiences, user management, content, permissions and operational features adapted to the audience and business model.','bullets':['Corporate portals, customer areas and intranets','E-learning platforms, courses, learning paths and content libraries','Students, users, roles and permissions','Classes, materials, progress, assessments and certificates','Subscriptions, payments and exclusive areas when needed','Integrations, automation and AI embedded according to the project']},
's5':{'title':'Corporate Websites and Web Platforms','shortDescription':'Professional digital presence connected to the company’s commercial, institutional and operational goals.','description':'We create responsive, fast and scalable corporate websites and web platforms with structured content, user experience, technical SEO and connections to the systems and channels required by the business.','bullets':['Corporate, institutional and commercial websites','Catalogs, dynamic pages and restricted areas','CMS and content management when required','Technical SEO, accessibility, performance and responsiveness','Connections to CRM, ERP, WhatsApp, analytics and external services','Automation and intelligent features integrated when they add value']},
's6':{'title':'Landing Pages and Conversion Pages','shortDescription':'Pages focused on campaigns, lead generation, launches and commercial opportunities.','description':'We develop landing and conversion pages focused on speed, offer clarity, mobile experience and measurement, connecting leads directly to the company’s commercial workflows and tools.','bullets':['Landing pages for campaigns, services, products and launches','Forms and structured lead capture','Direct integration with CRM and sales workflows','Analytics, pixels, events and conversion tracking','SEO, performance, responsiveness and technical best practices','Automated responses, distribution and qualification when applicable']},
's7':{'title':'System Modernization and Evolution','shortDescription':'Evolution of existing software to improve architecture, experience, performance, security and scalability.','description':'We work on existing systems and platforms to remove technical limitations, modernize interfaces, reorganize architecture and add new capabilities without requiring the entire operation to be rebuilt from scratch.','bullets':['Technical and functional assessment of the current system','Architecture refactoring and modernization','Interface redesign and user-experience improvement','Performance, stability, security and quality','Technology migration and evolution of existing modules','New integrations, automation and AI capabilities when useful']},
}

SERVICES_ES = {
's1':{'title':'Sistemas de Gestión y ERP','shortDescription':'Sistemas personalizados para centralizar procesos, datos y rutinas operativas en una sola plataforma.','description':'Diseñamos y desarrollamos sistemas de gestión y ERPs personalizados según la operación real de la empresa, conectando áreas administrativas, comerciales, financieras y operativas con una arquitectura preparada para evolucionar.','bullets':['Mapeo de procesos y reglas de negocio','Módulos administrativos, comerciales, financieros y operativos','Usuarios, perfiles, empresas y permisos','Dashboards, indicadores e informes de gestión','Flujos, aprobaciones, notificaciones y rutinas automatizadas','IA, automatización, integraciones y APIs incorporadas cuando corresponda']},
's2':{'title':'SaaS y MVP','shortDescription':'Productos digitales estructurados para validar, lanzar y evolucionar modelos de negocio basados en software.','description':'Convertimos ideas y operaciones en productos SaaS y MVPs funcionales, cubriendo alcance, experiencia de usuario, arquitectura, desarrollo y una base técnica preparada para crecer después de la validación.','bullets':['Descubrimiento, definición de alcance y priorización del MVP','Arquitectura SaaS y estructuras multi-tenant','Registro, autenticación, perfiles y control de acceso','Planes, suscripciones, pagos y reglas comerciales','Métricas, paneles y recursos administrativos','IA, automatización e integraciones incorporadas a la evolución del producto']},
's3':{'title':'CRM Personalizado','shortDescription':'CRMs desarrollados alrededor del proceso comercial real de la empresa, sin obligar la operación a adaptarse a una herramienta genérica.','description':'Creamos CRMs personalizados para organizar leads, oportunidades, clientes, propuestas, tareas y relaciones comerciales, con flujos, datos y automatizaciones definidos según el modelo de ventas y atención del negocio.','bullets':['Captación y calificación de leads','Embudos, etapas, oportunidades y previsión comercial','Clientes, contactos, propuestas, actividades y tareas','Reglas de distribución, seguimiento y notificaciones','Dashboards e indicadores comerciales','Integraciones, automatización y recursos de IA incorporados al flujo']},
's4':{'title':'Portales Web y Plataformas EAD','shortDescription':'Entornos digitales autenticados para clientes, equipos, comunidades, alumnos y operaciones de contenido.','description':'Desarrollamos portales web, áreas de cliente, intranets y plataformas EAD con experiencias autenticadas, gestión de usuarios, contenidos, permisos y recursos operativos adaptados al público y al modelo de negocio.','bullets':['Portales corporativos, áreas de cliente e intranets','Plataformas EAD, cursos, rutas y bibliotecas de contenido','Gestión de alumnos, usuarios, perfiles y permisos','Clases, materiales, progreso, evaluaciones y certificados','Suscripciones, pagos y áreas exclusivas cuando sean necesarios','Integraciones, automatización e IA incorporadas según el proyecto']},
's5':{'title':'Sitios Institucionales y Plataformas Web','shortDescription':'Presencia digital profesional conectada con los objetivos comerciales, institucionales y operativos de la empresa.','description':'Creamos sitios institucionales y plataformas web responsivas, rápidas y escalables, con contenido estructurado, experiencia de usuario, SEO técnico y conexión con los sistemas y canales necesarios para el negocio.','bullets':['Sitios institucionales, corporativos y comerciales','Catálogos, páginas dinámicas y áreas restringidas','CMS y gestión de contenido cuando sea necesario','SEO técnico, accesibilidad, rendimiento y responsividad','Conexión con CRM, ERP, WhatsApp, analytics y servicios externos','Automatizaciones y recursos inteligentes integrados cuando aporten valor']},
's6':{'title':'Landing Pages y Páginas de Conversión','shortDescription':'Páginas enfocadas en campañas, captación de leads, lanzamientos y generación de oportunidades comerciales.','description':'Desarrollamos landing pages y páginas de conversión con foco en velocidad, claridad de oferta, experiencia móvil y medición, conectando los leads directamente con los flujos comerciales y herramientas de la empresa.','bullets':['Landing pages para campañas, servicios, productos y lanzamientos','Formularios y captación estructurada de leads','Integración directa con CRM y flujos comerciales','Analytics, píxeles, eventos y seguimiento de conversión','SEO, rendimiento, responsividad y buenas prácticas técnicas','Automatización de respuestas, distribución y calificación cuando corresponda']},
's7':{'title':'Modernización y Evolución de Sistemas','shortDescription':'Evolución de software existente para mejorar arquitectura, experiencia, rendimiento, seguridad y capacidad de crecimiento.','description':'Trabajamos sobre sistemas y plataformas existentes para corregir limitaciones técnicas, modernizar interfaces, reorganizar la arquitectura y añadir nuevas capacidades sin exigir reconstruir toda la operación desde cero.','bullets':['Diagnóstico técnico y funcional del sistema actual','Refactorización y modernización de arquitectura','Rediseño de interfaz y mejora de la experiencia de usuario','Rendimiento, estabilidad, seguridad y calidad','Migración tecnológica y evolución de módulos existentes','Nuevas integraciones, automatizaciones y recursos de IA cuando sean útiles']},
}

def load_content():
    text = CONTENT.read_text(encoding='utf-8')
    prefix = 'window.VALTREN_DEFAULT_CONTENT = '
    if not text.startswith(prefix):
        raise RuntimeError('content.js format not recognized')
    raw = text[len(prefix):].strip()
    if raw.endswith(';'):
        raw = raw[:-1]
    return json.loads(raw)

def write_content(data):
    CONTENT.write_text('window.VALTREN_DEFAULT_CONTENT = ' + json.dumps(data, ensure_ascii=False, indent=2) + ';\n', encoding='utf-8')

def update_content():
    data = load_content()
    data['services'] = SERVICES_PT
    data['global']['description'] = 'Empresa de tecnologia especializada em sistemas de gestão e ERP, SaaS e MVP, CRM personalizado, portais web e EAD, sites e plataformas web, landing pages e modernização de sistemas, com atuação no Brasil e nos Estados Unidos.'
    data['home'].update({
        'heroEyebrow':'ERP · SAAS · CRM · PORTAIS · WEB · MODERNIZAÇÃO',
        'heroTitle':'Tecnologia sob medida para estruturar, integrar e evoluir operações digitais.',
        'heroText':'Desenvolvemos sistemas, produtos SaaS, CRMs, portais, plataformas web e experiências de conversão, incorporando IA, automação, integrações e APIs sempre que agregam valor ao projeto.',
        'aboutTitle':'Soluções digitais construídas em torno da operação real do negócio.',
        'aboutText':'A Valtren Solutions desenvolve sistemas e experiências digitais sob medida, conectando tecnologia, processos e objetivos comerciais. IA, automação, integrações e APIs fazem parte da arquitetura sempre que contribuem para eficiência, escala e resultado.',
        'technologyTitle':'Engenharia integrada do planejamento à evolução.',
        'technologyText':'Cada projeto é estruturado de ponta a ponta, combinando arquitetura, experiência do usuário, regras de negócio, dados, segurança, integrações, automação e recursos de IA conforme a necessidade da solução.'
    })
    data['mission'] = 'Desenvolver soluções tecnológicas sob medida que organizem processos, conectem operações e contribuam para o crescimento sustentável dos clientes e das empresas do Grupo Valtren.'
    data['vision'] = 'Ser reconhecida no Brasil e nos Estados Unidos pela qualidade no desenvolvimento e evolução de sistemas, produtos SaaS, CRMs, portais e plataformas digitais.'
    data['seo'] = {
        'title':'Valtren Solutions | ERP, SaaS, CRM, Portais e Plataformas Web',
        'description':'Sistemas de gestão e ERP, SaaS e MVP, CRM personalizado, portais web e EAD, sites, landing pages e modernização de sistemas.'
    }
    for lang, services, global_desc, seo, home in [
        ('en', SERVICES_EN,
         'A technology company specializing in management systems and ERP, SaaS and MVP, custom CRM, web portals and e-learning, corporate websites, conversion pages and system modernization, serving Brazil and the United States.',
         {'title':'Valtren Solutions | ERP, SaaS, CRM, Portals and Web Platforms','description':'Management systems and ERP, SaaS and MVP, custom CRM, web portals and e-learning, corporate websites, landing pages and system modernization.'},
         {'heroEyebrow':'ERP · SAAS · CRM · PORTALS · WEB · MODERNIZATION','heroTitle':'Custom technology to structure, connect and evolve digital operations.','heroText':'We build systems, SaaS products, CRMs, portals, web platforms and conversion experiences, embedding AI, automation, integrations and APIs whenever they add value to the project.','aboutTitle':'Digital solutions built around real business operations.','aboutText':'Valtren Solutions develops custom systems and digital experiences by connecting technology, processes and commercial goals. AI, automation, integrations and APIs are part of the architecture whenever they improve efficiency, scale and results.','technologyTitle':'Integrated engineering from planning to evolution.','technologyText':'Each project is structured end to end, combining architecture, user experience, business rules, data, security, integrations, automation and AI capabilities according to the solution’s needs.'}),
        ('es', SERVICES_ES,
         'Empresa de tecnología especializada en sistemas de gestión y ERP, SaaS y MVP, CRM personalizado, portales web y EAD, sitios institucionales, páginas de conversión y modernización de sistemas, con actuación en Brasil y Estados Unidos.',
         {'title':'Valtren Solutions | ERP, SaaS, CRM, Portales y Plataformas Web','description':'Sistemas de gestión y ERP, SaaS y MVP, CRM personalizado, portales web y EAD, sitios institucionales, landing pages y modernización de sistemas.'},
         {'heroEyebrow':'ERP · SAAS · CRM · PORTALES · WEB · MODERNIZACIÓN','heroTitle':'Tecnología a medida para estructurar, conectar y evolucionar operaciones digitales.','heroText':'Desarrollamos sistemas, productos SaaS, CRMs, portales, plataformas web y experiencias de conversión, incorporando IA, automatización, integraciones y APIs cuando aportan valor al proyecto.','aboutTitle':'Soluciones digitales construidas alrededor de la operación real del negocio.','aboutText':'Valtren Solutions desarrolla sistemas y experiencias digitales a medida conectando tecnología, procesos y objetivos comerciales. IA, automatización, integraciones y APIs forman parte de la arquitectura cuando mejoran la eficiencia, escala y resultados.','technologyTitle':'Ingeniería integrada desde la planificación hasta la evolución.','technologyText':'Cada proyecto se estructura de principio a fin combinando arquitectura, experiencia de usuario, reglas de negocio, datos, seguridad, integraciones, automatización y recursos de IA según la necesidad de la solución.'})
    ]:
        locale = data.setdefault('translations', {}).setdefault(lang, {})
        locale.setdefault('global', {})['description'] = global_desc
        locale.setdefault('home', {}).update(home)
        locale['services'] = services
        locale['seo'] = seo
    write_content(data)

def update_app():
    app = APP.read_text(encoding='utf-8')
    app = re.sub(r",\n\s*\{\n\s*name: 'Branding e Design',\n\s*eyebrow: 'MARCA, INTERFACES E IDENTIDADE VISUAL',\n\s*description: 'Competências complementares para estruturar marcas, interfaces e sistemas visuais alinhados aos produtos e objetivos do negócio\.'\n\s*\}", '', app, count=1)
    app = re.sub(r"const map = \{s1:'code',s2:'layers',s3:'briefcase',s4:'monitor',s5:'play',s6:'workflow',s7:'bot',s8:'database',s9:'search',s10:'zap',s11:'palette',s12:'video',s13:'briefcase',s14:'users',s15:'network',s16:'globe'\};",
                 "const map = {s1:'database',s2:'layers',s3:'users',s4:'video',s5:'globe',s6:'zap',s7:'refresh'};", app, count=1)
    app = app.replace('<a class="brand" href="#/" aria-label="Valtren Solutions">', '<a class="brand" href="#/" data-action="home-top" aria-label="Valtren Solutions — voltar ao início">', 1)
    old_footer = '<div class="footer-brand"><img src="assets/valtren-logo.svg?v=20260824-white-wordmark-v3" alt="Valtren Solutions"><p>'
    new_footer = '<div class="footer-brand"><a class="footer-logo-link" href="#/" data-action="home-top" aria-label="Valtren Solutions — voltar ao início"><img src="assets/valtren-logo.svg?v=20260824-white-wordmark-v3" alt="Valtren Solutions"></a><p>'
    if old_footer not in app:
        raise RuntimeError('footer logo target missing')
    app = app.replace(old_footer, new_footer, 1)
    old_saved = "      if (saved) return mergeDefaults(defaultContent, saved);"
    new_saved = """      if (saved) {\n        const migratedSaved = mergeDefaults(defaultContent, saved);\n        migratedSaved.services = clone(defaultContent.services);\n        migratedSaved.translations = migratedSaved.translations || {};\n        ['en','es'].forEach((language) => {\n          migratedSaved.translations[language] = migratedSaved.translations[language] || {};\n          migratedSaved.translations[language].services = clone(defaultContent.translations?.[language]?.services || {});\n        });\n        localStorage.setItem(CONTENT_KEY, JSON.stringify(migratedSaved));\n        return migratedSaved;\n      }"""
    if old_saved not in app:
        raise RuntimeError('saved content migration target missing')
    app = app.replace(old_saved, new_saved, 1)
    anchor = "    if (action === 'set-language')"
    insert = """    if (action === 'home-top') {\n      event.preventDefault();\n      state.mobileOpen = false;\n      state.servicesOpen = false;\n      if (routeInfo().path !== '/') location.hash = '#/';\n      else { renderCurrentWithoutReset(); window.scrollTo({top:0,left:0,behavior:'smooth'}); }\n      return;\n    }\n\n"""
    if anchor not in app:
        raise RuntimeError('click handler target missing')
    app = app.replace(anchor, insert + anchor, 1)
    APP.write_text(app, encoding='utf-8')

def update_css():
    css = CSS.read_text(encoding='utf-8')
    css = re.sub(r'\n?/\* VALTREN HOME LOGO LINKS \*/.*\Z', '', css, flags=re.S)
    css += """\n\n/* VALTREN HOME LOGO LINKS */\n.footer-logo-link{display:inline-block;line-height:0;cursor:pointer;text-decoration:none!important}\n.footer-logo-link img{display:block}\n.site-header .brand,.footer-logo-link{cursor:pointer}\n"""
    CSS.write_text(css, encoding='utf-8')

def main():
    update_content(); update_app(); update_css(); print('Serviços e links das logos atualizados.')

if __name__ == '__main__': main()
