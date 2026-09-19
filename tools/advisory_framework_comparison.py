"""Matched all-six-PR F2′ threshold comparison with fixed bug truth and identities.

Run after policy deduplication and verified_gold_defect_metrics.py. The .80
baseline filters the SAME validated .70 groups, isolating the threshold change.
"""
from collections import defaultdict
import json
from pathlib import Path
from tools.report_quality import advisory_f2
from tools.advisory_scoring_policy import digest

FRAMEWORKS=('vanilla-engineered','metareview-realistic','compound-realistic')


def advisory_counts(groups):
    accepted=[g for g in groups if g['decision']=='accepted']
    return sum(any(s['confidence']>=.8 for s in g['sources']) for g in accepted),len(accepted)


def summarize(cells,evidence,selected):
    eligible={k:v for k,v in cells.items() if v['n_pr']==6 and v['advisory_measured']}
    shared=set.intersection(*[{(k.split('|')[0],k.split('|')[2]) for k in eligible if k.split('|')[1]==fw} for fw in FRAMEWORKS])
    if not shared:raise ValueError('No complete matched model/effort cohorts')
    lookup={(r['model'],r['framework'],r['effort'],r['url']):r['run_id'] for r in selected}
    result={'matched_model_effort_combinations':len(shared),'frameworks':{},'cells':{}}
    for fw in FRAMEWORKS:
        totals=defaultdict(int);scores80=[];scores70=[]
        for model,effort in sorted(shared):
            key='|'.join((model,fw,effort));cell=eligible[key]
            T=D=A80=A70=H=0
            if len(cell['per_pr'])!=6 or len({r['url'] for r in cell['per_pr']})!=6:
                raise ValueError('Incomplete six-PR cell')
            for pr in cell['per_pr']:
                rid=lookup[(model,fw,effort,pr['url'])]
                a80,a70=advisory_counts(evidence[rid]['records'])
                counts=pr['counts']
                if a70!=counts[4]:raise ValueError('Policy evidence and scored advisory counts differ')
                T+=counts[0];D+=counts[1];A80+=a80;A70+=a70;H+=counts[5]
            score80=float(advisory_f2(T,D,A80,H));score70=float(advisory_f2(T,D,A70,H))
            if score70+1e-12<score80:raise ValueError('Threshold comparison unexpectedly reduced fixed-identity credit')
            row={'TP':T,'den':D,'A80':A80,'A70':A70,'H80':H,'F2p_A80':score80,'F2p_A70':score70,'delta':score70-score80}
            result['cells'][key]=row
            for name in ('TP','den','A80','A70','H80'):totals[name]+=row[name]
            scores80.append(score80);scores70.append(score70)
        result['frameworks'][fw]={**totals,'reviews':6*len(shared),'cells':len(shared),
            'mean_F2p_A80':sum(scores80)/len(shared),'mean_F2p_A70':sum(scores70)/len(shared),
            'mean_delta':sum(b-a for a,b in zip(scores80,scores70))/len(shared)}
    return result


def main():
    root=Path(__file__).resolve().parents[1];vg=root/'analysis/verified_gold'
    base=vg/'advisory_readjudication'
    pointer=json.loads((base/'active_scoring_policy.json').read_text())
    out=base/pointer['directory'];policy=json.loads((out/'policy.json').read_text())
    if digest(policy)!=pointer['policy_sha256']:raise ValueError('Policy hash changed')
    data=json.loads((root/'analysis/final_report_dataset.json').read_text())
    metrics=json.loads((vg/'DEFECT_METRICS.json').read_text())['verified']
    evidence=json.loads((vg/'ADVISORY_EVIDENCE.json').read_text())['runs']
    if len(evidence)!=403 or any(not e['measured'] or e.get('acceptance_policy_sha256')!=pointer['policy_sha256'] for e in evidence.values()):
        raise ValueError('All 403 reviews must be scored under the selected policy')
    result=summarize(metrics['cells'],evidence,data['selected_runs'])
    result.update(policy_sha256=pointer['policy_sha256'],status='complete',
                  definition='Arithmetic mean of six-PR pooled cell F2prime over identical model/effort cohorts. A80 and A70 use the same .70 validated semantic identities; H>=.80 and T/D fixed. Baseline is not the earlier grouping or historical classifier score.')
    (out/'framework_comparison.json').write_text(json.dumps(result,indent=2)+'\n')
    lines=['# Six-PR matched F2′ threshold comparison','',result['definition'],'',
           '| Framework | Reviews | A ≥.80 | A ≥.70 | H ≥.80 | Mean F2′, A ≥.80 | Mean F2′, A ≥.70 | Change |',
           '|---|---:|---:|---:|---:|---:|---:|---:|']
    for fw,r in result['frameworks'].items():
        lines.append(f"| {fw} | {r['reviews']} | {r['A80']} | {r['A70']} | {r['H80']} | {r['mean_F2p_A80']:.4f} | {r['mean_F2p_A70']:.4f} | {r['mean_delta']:+.4f} |")
    lines+=['','Descriptive point estimates only; no claim of statistical significance or measured developer utility.']
    (out/'FRAMEWORK_COMPARISON.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps(result['frameworks'],indent=2))

if __name__=='__main__':main()
