"""Clearly SYNTHETIC catalog and route fixtures, never student/source evidence."""
from copy import deepcopy
from datetime import datetime, timezone

def snapshot():
    created = int(datetime.now(timezone.utc).timestamp()) - 86400
    a = dict(id='synthetic/alpha', canonical_slug='synthetic/shared', name='Synthetic Alpha',
             created=created, context_length=256000, top_provider={'max_completion_tokens':32000},
             architecture={'input_modalities':['text'],'output_modalities':['text']},
             pricing={'prompt':'0.000001','completion':'0.000002'},
             supported_parameters=['tools'], links={'details':'/api/v1/models/synthetic/alpha/endpoints'})
    b = deepcopy(a)
    b.update(id='synthetic/beta', name='Synthetic Beta', context_length=128000,
             pricing={'prompt':'-1','completion':'0.000004'},
             links={'details':'/api/v1/models/synthetic/beta/endpoints'})
    c = deepcopy(a)
    c.update(id='synthetic/gamma', canonical_slug='synthetic/gamma', name='Synthetic Image',
             architecture={'input_modalities':['text'],'output_modalities':['image']}, supported_parameters=[])
    d = deepcopy(a)
    d.update(id='synthetic/delta', canonical_slug='synthetic/delta', name=None,
             context_length=None, pricing=None, top_provider=None, supported_parameters=[])
    routes = []
    for mid, provider, tag in [('alpha','SyntheticOne','one'),('alpha','SyntheticTwo','two'),('beta','SyntheticOne','one')]:
        routes.append(dict(model_id='synthetic/'+mid, provider_name=provider, tag=tag,
                           name='Synthetic Route', service_tier=None, context_length=128000,
                           max_completion_tokens=16000, pricing={'prompt':'0.000002','completion':'0.000004'},
                           supported_parameters=['tools']))
    return dict(models=[a,b,c,d], endpoints=routes, observed=datetime.now(timezone.utc), complete=True)
