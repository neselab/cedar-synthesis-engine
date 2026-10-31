"""Closed typed gold compiler. No prose, model output, or AutoCedar dependency."""
from __future__ import annotations
import copy
import hashlib
import json
import re
from pathlib import Path

CONTRACT = 'complete-spec-v4'
IDENT = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')
def canonical(x): return json.dumps(x, sort_keys=True, separators=(',', ':'), ensure_ascii=True)
def digest(x): return hashlib.sha256(canonical(x).encode()).hexdigest()
def n(op, *args): return {'op': op, 'args': list(args)}
def f(path): return {'op': 'field', 'path': path}
def lit(x): return {'op': 'literal', 'value': x}
def ent(kind, value): return {'op': 'entity', 'type': kind, 'id': value}
def param(name): return {'op': 'parameter', 'name': name}
def instantiate(t, p):
    if isinstance(t, list): return [instantiate(a,p) for a in t]
    if not isinstance(t,dict): return t
    if t.get('op') == 'parameter': return lit(p[t['name']])
    return {k:instantiate(v,p) for k,v in t.items()}

def resolve(path, r, a):
    bits = path.split('.')
    root = bits.pop(0)
    kind = {'principal':'User','resource':a['resource_type'],'context':'@context'}.get(root)
    if kind is None: raise ValueError('Unknown root: '+path)
    guards=[]; prefix=root
    for bit in bits:
        attrs = r['context'] if kind == '@context' else r['entities'][kind]['attributes']
        if bit not in attrs: raise ValueError('Unknown field: '+path)
        field = attrs[bit]
        if field.get('optional'): guards.append({'op':'has','path':prefix,'attribute':bit})
        kind=field['type']; prefix += '.'+bit
    return kind,guards

def type_of(t,r,a):
    if not isinstance(t,dict): raise ValueError('AST node must be an object')
    op=t.get('op')
    if op=='literal':
        if set(t)!={'op','value'}: raise ValueError('Malformed literal')
        x=t['value']
        if type(x) is bool:return 'Bool'
        if type(x) is int and -(2**63)<=x<2**63:return 'Long'
        if type(x) is str:return 'String'
        raise ValueError('Invalid literal')
    if op=='field':
        if set(t)!={'op','path'}: raise ValueError('Malformed field')
        return resolve(t['path'],r,a)[0]
    if op=='entity':
        if set(t)!={'op','type','id'}: raise ValueError('Malformed entity')
        d=r['entities'][t['type']]
        if type(t['id']) is not str or ('enum' in d and t['id'] not in d['enum']):raise ValueError('Invalid entity')
        return t['type']
    if op=='has':
        if set(t)!={'op','path','attribute'}:raise ValueError('Malformed has')
        resolve(t['path']+'.'+t['attribute'],r,a);return 'Bool'
    if set(t)!={'op','args'} or not isinstance(t['args'],list):raise ValueError('Malformed operation')
    args=t['args']; kinds=[type_of(x,r,a) for x in args]
    if op in ('all','any') and all(k=='Bool' for k in kinds):return 'Bool'
    if op=='not' and kinds==['Bool']:return 'Bool'
    if op in ('eq','ne') and len(kinds)==2 and kinds[0]==kinds[1]:return 'Bool'
    if op in ('lt','le','gt','ge') and kinds==['Long','Long']:return 'Bool'
    if op in ('add','sub','mul') and kinds==['Long','Long']:return 'Long'
    if op=='contains' and len(kinds)==2 and kinds[0]=='Set<'+kinds[1]+'>':return 'Bool'
    if op in ('contains_all','contains_any') and len(kinds)==2 and kinds[0]==kinds[1] and kinds[0].startswith('Set<'):return 'Bool'
    if op=='in' and len(kinds)==2 and kinds[1] in r['entities'].get(kinds[0],{}).get('member_of',[]):return 'Bool'
    if op=='like' and kinds==['String','String'] and args[1]['op']=='literal':return 'Bool'
    if op in ('datetime','ip') and kinds==['String'] and args[0]['op']=='literal':return {'datetime':'datetime','ip':'ipaddr'}[op]
    if op in ('time_lt','time_le') and kinds==['datetime','datetime']:return 'Bool'
    if op=='time_diff' and kinds==['datetime','datetime']:return 'Long'
    if op=='utc_time_ms' and kinds==['datetime']:return 'Long'
    if op=='ip_in' and kinds==['ipaddr','ipaddr']:return 'Bool'
    raise ValueError(f'Unsupported or ill-typed operation {op}: {kinds}')

def walk(t):
    yield t
    for arg in t.get('args',[]):yield from walk(arg)

def guard(t,r,a):
    """Missing optional values make this predicate false, including inequality."""
    guards=[]
    for x in walk(t):
        if x['op']=='field':
            for g in resolve(x['path'],r,a)[1]:
                if g not in guards:guards.append(g)
    return n('all',*guards,t) if guards else t

def emit(t):
    op=t['op']
    if op=='literal':return canonical(t['value'])
    if op=='field':return t['path']
    if op=='entity':return t['type']+'::'+canonical(t['id'])
    if op=='has':return '('+t['path']+' has '+t['attribute']+')'
    args=[emit(x) for x in t['args']]
    if op in ('all','any'):return '('+(' && ' if op=='all' else ' || ').join(args)+')' if args else ('true' if op=='all' else 'false')
    if op=='not':return '!('+args[0]+')'
    binary={'eq':'==','ne':'!=','lt':'<','le':'<=','gt':'>','ge':'>=','add':'+','sub':'-','mul':'*','like':'like','in':'in','time_lt':'<','time_le':'<='}
    if op in binary:return '('+args[0]+' '+binary[op]+' '+args[1]+')'
    methods={'contains':'contains','contains_all':'containsAll','contains_any':'containsAny','time_lt':'lessThan','time_le':'lessThanOrEqual','ip_in':'isInRange'}
    if op in methods:return args[0]+'.'+methods[op]+'('+args[1]+')'
    if op in ('datetime','ip'):return ('ip' if op=='ip' else 'datetime')+'('+args[0]+')'
    if op=='utc_time_ms':return args[0]+'.toTime().toMilliseconds()'
    if op=='time_diff':return args[0]+'.durationSince('+args[1]+').toMilliseconds()'
    raise ValueError('Unsupported AST operation '+op)

def parameter_names(t):return {x['name'] for x in walk(t) if x['op']=='parameter'}

def validate_registry(r):
    if r['contract']!=CONTRACT:raise ValueError('Unsupported registry contract')
    for name,d in r['entities'].items():
        if not IDENT.fullmatch(name):raise ValueError('Invalid entity name')
        for k,v in d.get('attributes',{}).items():
            if not IDENT.fullmatch(k):raise ValueError('Invalid attribute')
            typ=v['type']; elem=typ[4:-1] if typ.startswith('Set<') and typ.endswith('>') else typ
            if elem not in ('Bool','Long','String','datetime','ipaddr') and elem not in r['entities']:raise ValueError('Unknown type '+typ)
    for name,a in r['anchors'].items():
        if not IDENT.fullmatch(name):raise ValueError('Invalid action')
        for sec in ('bases','atoms','overrides'):
            for k,d in a[sec].items():
                if sec=='atoms':
                    if not d['parameter_sets']:raise ValueError('Empty catalog')
                    if set(d['parameter_schema'])!=parameter_names(d['predicate']):raise ValueError('Incomplete parameter schema')
                    for p in d['parameter_sets']:
                        if set(p)!=parameter_names(d['predicate']):raise ValueError('Incomplete parameter catalog')
                        for name,value in p.items():
                            definition=d['parameter_schema'][name]
                            if type_of(lit(value),r,a)!=definition['type'] or canonical(value) not in map(canonical,definition['values']):raise ValueError('Parameter schema mismatch')
                        if type_of(guard(instantiate(d['predicate'],p),r,a),r,a)!='Bool':raise ValueError('Nonboolean atom')
                        if 'requirement' in d:
                            if not parameter_names(d['requirement'])<=set(p):raise ValueError('Incomplete obligation parameters')
                            if type_of(guard(instantiate(d['requirement'],p),r,a),r,a)!='Bool':raise ValueError('Nonboolean obligation')
                    semantics=d['business_semantics'];kind=semantics['kind'];target=semantics['target']
                    if type(d['sampling_enabled']) is not bool or d['sampling_enabled']!=semantics['enabled']:raise ValueError('Invalid sampling eligibility')
                    if kind not in ('require','prohibit','applicability','obligation','exception'):raise ValueError('Unknown business composition')
                    if d['allowed_forms']!=[kind] or d['allowed_targets']!=[target]:raise ValueError('Catalog contradicts authored business semantics')
                    if kind in ('require','prohibit','obligation') and target!='@action':raise ValueError('Action requirement needs action target')
                    if kind=='applicability' and target not in a['bases']:raise ValueError('Applicability needs a base target')
                    if kind=='obligation' and 'requirement' not in d:raise ValueError('Missing obligation')
                    if kind!='obligation' and 'requirement' in d:raise ValueError('Unexpected obligation')
                    if kind=='exception':
                        if target not in a['bases'] and (target not in a['atoms'] or a['atoms'][target]['business_semantics']['kind']!='require'):raise ValueError('Exception must name a base or mandatory predicate')
                elif type_of(guard(d['predicate'],r,a),r,a)!='Bool':raise ValueError('Nonboolean rule')
                if sec=='overrides' and not set(d['targets'])<=a['bases'].keys():raise ValueError('Unknown override target')
        for k in ('eligibility','domain_gate'):
            if type_of(a[k],r,a)!='Bool':raise ValueError('Nonboolean gate')
    return r

def load_registry(path):return validate_registry(json.loads(Path(path).read_text()))

def normalize_part(p,r):
    if set(p)!={'anchor','bases','conditions','overrides'}:raise ValueError('Incomplete anchor selection')
    a=r['anchors'][p['anchor']];bs=p['bases']
    if not isinstance(bs,list) or not bs or len(set(bs))!=len(bs) or not set(bs)<=a['bases'].keys():raise ValueError('Invalid base selection')
    if not isinstance(p['conditions'],list) or not isinstance(p['overrides'],list):raise ValueError('Selections must be lists')
    if len(bs)+len(p['conditions'])+len(p['overrides'])>5:raise ValueError('Depth exceeds five')
    seen=set();sig={a['bases'][b]['signature'] for b in bs}
    for c in p['conditions']:
        if set(c)!={'atom','form','target','parameters'}:raise ValueError('Incomplete condition')
        k=c['atom'];d=a['atoms'][k]
        if k in seen or k in sig:raise ValueError('Duplicate or signature-excluded atom')
        seen.add(k)
        if not d['sampling_enabled']:raise ValueError('Condition disabled as redundant: '+k)
        if c['form'] not in d['allowed_forms']:raise ValueError('Form contradicts business meaning')
        if c['target'] not in d['allowed_targets']:raise ValueError('Invalid target')
        if c['form']=='applicability' and c['target'] not in bs:raise ValueError('Missing applicability base')
        if c['form']=='exception' and c['target'] not in bs and not any(x['atom']==c['target'] and x['form']=='require' for x in p['conditions']):raise ValueError('Missing exception target')
        if canonical(c['parameters']) not in {canonical(x) for x in d['parameter_sets']}:raise ValueError('Parameters outside declared catalog')
    seen=set()
    for o in p['overrides']:
        if set(o)!={'id','targets'}:raise ValueError('Incomplete override')
        k=o['id'];d=a['overrides'][k]
        if k in seen or sorted(o['targets'])!=sorted(d['targets']) or not set(o['targets'])<=set(bs):raise ValueError('Invalid override')
        seen.add(k)
    p=copy.deepcopy(p)
    for k in ('bases','conditions','overrides'):p[k]=sorted(p[k],key=canonical)
    return p

def make_spec(r,parts,provenance=None):
    return {'format_version':CONTRACT,'registry_sha256':digest(r),'source_sha256':r['source_sha256'],
            'domain':r['domain'],'grouping':{'requirements':'all','applicability_triggers':'any','exception':'any'},
            'parts':parts,'provenance':provenance or {'kind':'engineering fixture'}}

def compile_spec(s,r):
    if set(s)!=set(make_spec(r,[])):raise ValueError('Incomplete specification')
    for k,v in make_spec(r,[]).items():
        if k not in ('parts','provenance') and canonical(s[k])!=canonical(v):raise ValueError('Mismatch '+k)
    if not isinstance(s['parts'],list) or not s['parts']:raise ValueError('Empty parts')
    if not isinstance(s['provenance'],dict):raise ValueError('Provenance must be an object')
    s=copy.deepcopy(s);s['parts']=sorted([normalize_part(p,r) for p in s['parts']],key=lambda p:p['anchor'])
    if len({p['anchor'] for p in s['parts']})!=len(s['parts']):raise ValueError('Duplicate anchor')
    trees={}; policies=[]
    for p in s['parts']:
        name=p['anchor'];a=r['anchors'][name];eligible=a['eligibility']
        extra=[a['overrides'][o['id']]['eligibility_extension'] for o in p['overrides'] if 'eligibility_extension' in a['overrides'][o['id']]]
        gates=[a['domain_gate'],n('any',eligible,*extra)]
        for b in p['bases']:
            restrictions=[];waivers=[]
            for c in p['conditions']:
                if c['target']==b:
                    pred=guard(instantiate(a['atoms'][c['atom']]['predicate'],c['parameters']),r,a)
                    if c['form']=='applicability':restrictions.append(pred)
                    elif c['form']=='exception':waivers.append(pred)
            waivers.extend(guard(a['overrides'][o['id']]['predicate'],r,a) for o in p['overrides'] if b in o['targets'])
            active=n('any',*restrictions) if restrictions else lit(True)
            gates.append(n('any',n('not',active),guard(a['bases'][b]['predicate'],r,a),*waivers))
        for condition in p['conditions']:
            definition=a['atoms'][condition['atom']]
            form=condition['form']
            if form=='obligation':
                gates.append(guard(instantiate(definition['requirement'],condition['parameters']),r,a))
            elif form in ('require','prohibit'):
                pred=guard(instantiate(definition['predicate'],condition['parameters']),r,a)
                if form=='prohibit':pred=n('not',pred)
                waivers=[guard(instantiate(a['atoms'][x['atom']]['predicate'],x['parameters']),r,a) for x in p['conditions'] if x['form']=='exception' and x['target']==condition['atom']]
                gates.append(n('any',pred,*waivers))
        tree=n('all',*gates);assert type_of(tree,r,a)=='Bool';trees[name]=tree
        policies.append(f'permit (principal is User, action == Action::{canonical(name)}, resource is {a["resource_type"]})\nwhen {{ {emit(tree)} }};')
    policy='\n\n'.join(policies)+'\n';schema=render_schema(r,s['parts'])
    return {'spec':s,'spec_sha256':digest({k:v for k,v in s.items() if k!='provenance'}),'predicate_ast':trees,'policy':policy,'schema':schema,'policy_sha256':hashlib.sha256(policy.encode()).hexdigest()}

def render_schema(r,parts):
    lines=[]
    for name,d in sorted(r['entities'].items()):
        if 'enum' in d:lines.append(f'entity {name} enum ['+', '.join(canonical(x) for x in d['enum'])+'];');continue
        inh=' in ['+', '.join(d['member_of'])+']' if d.get('member_of') else ''
        attrs=', '.join(k+('?' if v.get('optional') else '')+': '+v['type'] for k,v in sorted(d['attributes'].items()))
        lines.append(f'entity {name}{inh} {{ {attrs} }};')
    context=',\n    '.join(k+('?' if v.get('optional') else '')+': '+v['type'] for k,v in sorted(r['context'].items()))
    for p in sorted(parts,key=lambda p:p['anchor']):
        k=p['anchor'];lines.append(f'action {k} appliesTo {{ principal: [User], resource: [{r["anchors"][k]["resource_type"]}], context: {{\n    {context},\n  }},\n}};')
    return '\n'.join(lines)+'\n'

def describe(t):
    op=t['op']
    if op=='field':return t['path'].replace('principal','requester',1)
    if op=='literal':return canonical(t['value'])
    if op=='entity':return t['type']+' '+canonical(t['id'])
    if op=='has':return t['path']+' has a recorded '+t['attribute']
    a=[describe(x) for x in t['args']]
    if op in ('all','any'):return '('+(' AND ' if op=='all' else ' OR ').join(a)+')' if a else ('true' if op=='all' else 'false')
    if op=='not':return 'NOT ('+a[0]+')'
    words={'eq':'equals','ne':'differs from','lt':'is less than','le':'is at most','gt':'exceeds','ge':'is at least','add':'plus','sub':'minus','mul':'times','like':'matches Cedar wildcard pattern','in':'is the same hierarchy node as or descends from','contains':'contains','contains_all':'contains every member of','time_lt':'is earlier than','time_le':'is no later than','ip_in':'is within IP range','time_diff':'minus (elapsed milliseconds)'}
    words['contains_any']='has at least one member in common with'
    if op in words:return '('+a[0]+' '+words[op]+' '+a[1]+')'
    if op=='utc_time_ms':return 'UTC milliseconds since midnight of '+a[0]
    if op in ('datetime','ip'):return op+' '+a[0]
    raise ValueError('No description for '+op)

def render_spec(s,r):
    c=compile_spec(s,r);s=c['spec'];lines=['# Complete authorization specification','',f'Contract: {CONTRACT}. Domain: {r["domain"]}. Registry SHA-256: {digest(r)}.',
        'Within each selected action scope, access is allowed if and only if all listed requirements, normalized bases, eligibility routes, domain bounds, and conditional obligations hold. Otherwise access is denied. No additional grant or requirement may be inferred.',
        'Deny by default. Only the selected actions can be allowed. Each action is evaluated on the current entity snapshot; no state transition is performed.',
        'Roles may overlap. Mandatory requirements must all hold. Prohibited predicates must be false. Each applicability trigger independently activates its named base; ANY such trigger activates that base. A selected base with no trigger applies unconditionally. An exception waives only its named selected rule; an override waives only its named base. All remaining rules, conditional obligations, eligibility, and domain bounds must hold.',
        'Missing optional fields make the individual predicate that reads them false. Time values use UTC; recurring time-of-day constraints apply every day. All monetary values are integer minor units of one experiment currency (USD cents).',
        'Request context contains trusted host-supplied facts; authorization does not independently attest them.',
        'The complete schema and field dictionaries below are part of this specification; no implied workflow, role exclusivity, deadline, or cross-field invariant is added.','']
    for p in s['parts']:
        a=r['anchors'][p['anchor']];lines+=['## '+p['anchor'],'Resource type: '+a['resource_type'], 'Eligible requester: '+describe(a['eligibility'])]
        for o in p['overrides']:
            d=a['overrides'][o['id']]
            if 'eligibility_extension' in d:lines.append('Additional eligibility route, enabled by '+o['id']+': '+describe(d['eligibility_extension']))
        lines.append('Unconditional domain bounds: '+describe(a['domain_gate']))
        for b in p['bases']:lines.append('Base '+b+': '+describe(guard(a['bases'][b]['predicate'],r,a)))
        for x in p['conditions']:
            d=a['atoms'][x['atom']];form=x['form']
            if form=='obligation':lines.append(x['atom']+' mandatory conditional obligation (no base exception or override waives it): '+describe(guard(instantiate(d['requirement'],x['parameters']),r,a)))
            else:
                labels={'require':'mandatory access requirement: ','prohibit':'access is prohibited when: ','applicability':'independently activates '+x['target']+' when: ','exception':'waives only '+x['target']+' when: '}
                lines.append(x['atom']+' '+labels[form]+describe(guard(instantiate(d['predicate'],x['parameters']),r,a)))
            # Exact instantiated formulas above are authoritative. Do not send
            # historical source shorthand or generic parameter placeholders to LLMs.
            lines.extend('Definition: '+note for note in d.get('revision_notes',[]) if note not in (d['business_semantics']['statement'],'Composition rationale: '+d['business_semantics']['rationale']))
        for o in p['overrides']:lines.append(o['id']+' waives only '+', '.join(o['targets'])+' when: '+describe(guard(a['overrides'][o['id']]['predicate'],r,a)))
    lines+=['','## Field dictionaries',json.dumps(r['entities'],indent=2,sort_keys=True),'Context:',json.dumps(r['context'],indent=2,sort_keys=True)]
    return '\n'.join(lines)+'\n'
