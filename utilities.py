import json

def dict_to_json(d):
    for k, v in d.items():
        if "'" in k:
            val = d.pop(k)
            k.replace("'", "")
            d[k] = val
        if isinstance(v, str):
            if "'" in v:
                d[k] = v.replace("'","")
        elif isinstance(v, list):
            for i in v:
                j = 0
                if isinstance(i, str):
                    v[j] = i.replace("'","")
                j += 1
            d[k] = v
        elif isinstance(v, dict):
            d[k] = dict_to_json(v)
    return json.dumps(d)