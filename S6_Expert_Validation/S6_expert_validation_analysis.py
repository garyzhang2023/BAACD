# -*- coding: utf-8 -*-
"""Analyze the expert-validation workbook without fabricating or imputing ratings."""
from pathlib import Path
import argparse, math
import numpy as np
import pandas as pd
from math import comb

def mannwhitneyu(x,y):
    x=np.asarray(x,float); y=np.asarray(y,float); n1=len(x); n2=len(y)
    pooled=np.r_[x,y]; ranks=pd.Series(pooled).rank(method='average').to_numpy(); u1=ranks[:n1].sum()-n1*(n1+1)/2
    _,counts=np.unique(pooled,return_counts=True); n=n1+n2
    tie=sum(c**3-c for c in counts); var=n1*n2/12*((n+1)-tie/(n*(n-1))) if n>1 else np.nan
    z=(abs(u1-n1*n2/2)-0.5)/math.sqrt(var) if var and var>0 else 0.0
    p=math.erfc(abs(z)/math.sqrt(2)); return u1,p

def cliffs_delta(x,y):
    x=np.asarray(x); y=np.asarray(y)
    return (sum(a>b for a in x for b in y)-sum(a<b for a in x for b in y))/(len(x)*len(y)) if len(x) and len(y) else np.nan
def holm(pvals):
    p=np.asarray(pvals,float); order=np.argsort(p); out=np.empty(len(p)); running=0
    for rank,idx in enumerate(order):
        val=min(1.0,(len(p)-rank)*p[idx]); running=max(running,val); out[idx]=running
    return out
def q1(s): return s.quantile(.25)
def q3(s): return s.quantile(.75)
def decision(n,a,med,iqr,policy):
    if n<12: return '数据不完整'
    if a>=10 and med>=3 and iqr<=1: return '保留'
    if a==9 or iqr>1: return '修订进入R2'
    return '政策例外审议/R2' if policy=='是' else '删除或合并候选'
def main(path):
    path=Path(path); out=path.with_name(path.stem+'_分析结果.xlsx')
    data=pd.read_excel(path,sheet_name='第一轮录入'); code=pd.read_excel(path,sheet_name='条目编码本'); ant=pd.read_excel(path,sheet_name='前瞻判断'); r2=pd.read_excel(path,sheet_name='第二轮录入')
    ratings=['D1 内容相关性','D2','D3','D4','D5']
    problems=[]
    for col in ratings:
        bad=data[col].dropna()[~data[col].dropna().isin([1,2,3,4])]
        if len(bad): problems.append(f'{col}存在{len(bad)}个非1–4值')
    expected=set([f'E{i:02d}' for i in range(1,7)]+[f'V{i:02d}' for i in range(1,7)])
    found=set(data['专家编号'].dropna().astype(str));
    if found!=expected: problems.append(f'专家编号集合异常：{sorted(found)}')
    merged=data.merge(code[['条目编号','条目名称','政策明确/风险关键']],on='条目编号',how='left')
    rows=[]
    for item,g in merged.groupby('条目编号',sort=False):
        s=g['D1 内容相关性'].dropna(); n=len(s); a=int((s>=3).sum()); icvi=a/n if n else np.nan; pc=comb(n,a)*(.5**n) if n else np.nan; k=(icvi-pc)/(1-pc) if n and pc<1 else np.nan
        med=s.median() if n else np.nan; iqr=(q3(s)-q1(s)) if n else np.nan
        base=g.iloc[0]; row={'条目编号':item,'条目名称':base['条目名称'],'有效N':n,'同意数':a,'I-CVI':icvi,'Pc':pc,'修正Kappa':k,'D1中位数':med,'D1 IQR':iqr}
        for col in ratings[1:]:
            z=g[col].dropna(); row[col+'中位数']=z.median() if len(z) else np.nan; row[col+' IQR']=(q3(z)-q1(z)) if len(z) else np.nan
        row['初步决策']=decision(n,a,med,iqr,base['政策明确/风险关键']); rows.append(row)
    itemres=pd.DataFrame(rows)
    scale=pd.DataFrame([{'范围':'全部条目','S-CVI/Ave':itemres['I-CVI'].mean(),'完整条目数':int((itemres['有效N']==12).sum()),'条目总数':len(itemres)}])
    comps=[]
    for item,g in merged.groupby('条目编号',sort=False):
        for col in ratings:
            x=g.loc[g['专家组']=='企业专家',col].dropna(); y=g.loc[g['专家组']=='高职教师',col].dropna()
            if len(x)>=3 and len(y)>=3:
                u,p=mannwhitneyu(x,y); comps.append({'条目编号':item,'维度':col,'企业n':len(x),'教师n':len(y),'U':u,'p':p,'Cliff_delta':cliffs_delta(x,y)})
    comps=pd.DataFrame(comps)
    if len(comps): comps['p_Holm']=holm(comps['p'].values)
    ants=[]
    for codeid,g in ant.groupby('陈述编号',sort=False):
        s=g['评分1–4'].dropna(); ants.append({'陈述编号':codeid,'有效N':len(s),'中位数':s.median() if len(s) else np.nan,'IQR':q3(s)-q1(s) if len(s) else np.nan,'同意比例':(s>=3).mean() if len(s) else np.nan})
    qa=pd.DataFrame({'数据质量问题':problems or ['未发现编号或评分范围错误；仍需人工核对知情同意、纳入标准和文字意见。']})
    # ---- 第二轮(R2)统计：仅对纳入 R2 的修订条目 ----
    r2res=pd.DataFrame(); r2scale=pd.DataFrame(); r2comp=pd.DataFrame()
    if 'R2相关性1–4' in r2.columns and r2['R2相关性1–4'].notna().any():
        r2rows=[]
        for item,g in r2.groupby('条目编号',sort=False):
            s=pd.to_numeric(g['R2相关性1–4'],errors='coerce').dropna(); n=len(s); a=int((s>=3).sum())
            icvi=a/n if n else np.nan; pc=comb(n,a)*(.5**n) if n else np.nan; k=(icvi-pc)/(1-pc) if n and pc<1 else np.nan
            med=s.median() if n else np.nan; iqr=(q3(s)-q1(s)) if n else np.nan
            ap=g['是否赞成修订'].astype(str).str.strip()=='是'; apn=int(ap.sum()); apr=apn/n if n else np.nan
            dec='修订确认' if (apr>=.8 and icvi>=.78) else '维持原文'
            r2rows.append({'条目编号':item,'有效N':n,'同意数':a,'R2 I-CVI':icvi,'修正Kappa':k,'中位数':med,'IQR':iqr,'赞成修订数':apn,'赞成比例':apr,'最终决策':dec})
        r2res=pd.DataFrame(r2rows)
        r2scale=pd.DataFrame([{'范围':'R2修订条目','S-CVI/Ave':r2res['R2 I-CVI'].mean(),'完整条目数':int((r2res['有效N']==12).sum()),'条目总数':len(r2res)}])
        m=r2res.merge(itemres[['条目编号','I-CVI','D1中位数','D1 IQR']],on='条目编号',how='left').rename(columns={'I-CVI':'R1 I-CVI','D1中位数':'R1中位数','D1 IQR':'R1 IQR'})
        r2comp=m[['条目编号','R1 I-CVI','R2 I-CVI','R1中位数','中位数','R1 IQR','IQR','赞成比例','最终决策']]
    with pd.ExcelWriter(out,engine='openpyxl') as w:
        itemres.to_excel(w,sheet_name='ItemResults',index=False); scale.to_excel(w,sheet_name='ScaleResults',index=False); comps.to_excel(w,sheet_name='GroupComparisons',index=False); pd.DataFrame(ants).to_excel(w,sheet_name='BoundedAnticipation',index=False); qa.to_excel(w,sheet_name='DataQuality',index=False)
        if len(r2res):
            r2res.to_excel(w,sheet_name='Round2Results',index=False); r2scale.to_excel(w,sheet_name='Round2Scale',index=False); r2comp.to_excel(w,sheet_name='R1R2Comparison',index=False); r2.to_excel(w,sheet_name='Round2Raw',index=False)
    print(out)
if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('workbook',nargs='?',default='AI应用服务课程专家验证数据与分析.xlsx'); main(ap.parse_args().workbook)
