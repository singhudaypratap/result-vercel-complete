# api/result.py - defensive normalized responder
import os, json, traceback
from urllib.parse import parse_qs

def _make_response(obj, status=200):
    return (json.dumps(obj, ensure_ascii=False), status, {'Content-Type':'application/json'})

def handler(request):
    try:
        if hasattr(request, 'args'):
            params = {k: v for k, v in request.args.items()}
        else:
            qs = request.environ.get('QUERY_STRING','')
            params = {k: v[0] for k, v in parse_qs(qs).items()}
        reg = params.get('reg','').strip()
        branch = params.get('branch','').strip()
        if not reg:
            return _make_response({'error':'reg is required'}, 400)
        if not branch:
            return _make_response({'error':'branch is required'}, 400)
        data_file = os.path.join(os.getcwd(), 'data', f"{branch}.json")
        if not os.path.exists(data_file):
            return _make_response({'error':'Incorrect entries or branch selection. Please try again.'}, 400)
        with open(data_file, 'r', encoding='utf-8') as fh:
            rows = json.load(fh)
        # Normalize keys: ensure each row has canonical keys where possible
        normalized = []
        reg_norm = reg.strip().lower()
        for r in rows:
            # ensure all keys are strings
            r = {str(k): (v if v is not None else '') for k,v in r.items()}
            # match by Reg field preferentially
            possible_reg_keys = [k for k in r.keys() if k.lower() in ('reg','reg. no','registration','regno')]
            matched = False
            if possible_reg_keys:
                for rk in possible_reg_keys:
                    if isinstance(r.get(rk,''), str) and r.get(rk,'').strip().lower() == reg_norm:
                        matched = True
                        break
            if not matched:
                # try any value exact match
                for v in r.values():
                    if isinstance(v, str) and v.strip().lower() == reg_norm:
                        matched = True
                        break
            if not matched:
                # contains match fallback
                for v in r.values():
                    if isinstance(v, str) and reg_norm in v.strip().lower():
                        matched = True
                        break
            if not matched:
                continue
            # Build canonical row
            out = {}
            # pick common keys
            def find_key(cands):
                for c in r.keys():
                    lc = c.lower()
                    for cand in cands:
                        if cand in lc or lc in cand:
                            return c
                return None
            out['Reg'] = r.get(find_key(['reg','registration']) or next(iter(r.keys())), '')
            out['Name'] = r.get(find_key(['name']) or '', '')
            out['Uni-Roll No'] = r.get(find_key(['uni-roll','uni roll','university roll']) or '', '')
            out['Col Roll No'] = r.get(find_key(['col roll','college roll','section']) or '', '')
            # subjects: any remaining keys that are not core or trailing
            core_and_trailing = set([k for k in [find_key(['reg','registration']), find_key(['name']), find_key(['uni-roll','uni roll']), find_key(['col roll','college roll']), find_key(['total back','back','totalback']), find_key(['result']), find_key(['sgpa','gpa'])] if k])
            for k in r.keys():
                if k in core_and_trailing: continue
                lk = k.lower()
                if any(x in lk for x in ['total','back','result','sgpa','gpa']): continue
                # subject heuristics: has letters and digits or common codes
                if (any(ch.isdigit() for ch in k) and any(ch.isalpha() for ch in k)) or any(x in lk for x in ['fec','4cs','cs','ee','ma']):
                    out[k] = r.get(k,'')
            # trailing fields
            out['Total Back'] = r.get(find_key(['total back','back','totalback']) or 'Total Back','')
            # compute if missing
            if not out['Total Back']:
                backc = 0
                for v in out.values():
                    if isinstance(v,str) and (v.strip().upper()=='F' or 'FAIL' in v.upper()):
                        backc += 1
                out['Total Back'] = str(backc)
            out['Result'] = r.get(find_key(['result','status']) or 'Result','')
            out['SGPA'] = r.get(find_key(['sgpa','gpa','cgpa']) or 'SGPA','')
            normalized.append(out)
        return _make_response({'result': normalized}, 200)
    except Exception as e:
        tb = traceback.format_exc()
        print('ERROR in api/result:', str(e))
        print(tb)
        return _make_response({'error':'Internal server error','detail':str(e)}, 500)
