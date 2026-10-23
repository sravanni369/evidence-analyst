"""Build a source-controlled Power BI report using Microsoft's public PBIR format."""
import json
import hashlib
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1] / 'powerbi/project'
REPORT = ROOT / 'EvidenceDashboard.Report'
MODEL = ROOT / 'EvidenceAnalyst.SemanticModel'
DEF = REPORT / 'definition'

def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding='utf-8')

def schema(kind):
    return f'https://developer.microsoft.com/json-schemas/fabric/item/report/definition/{kind}/1.0.0/schema.json'

save(ROOT/'EvidenceAnalyst.pbip', {'version':'1.0','artifacts':[{'report':{'path':'EvidenceDashboard.Report'}}],'settings':{'enableAutoRecovery':True}})
save(REPORT/'definition.pbir',{'$schema':'https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/1.0.0/schema.json','version':'4.0','datasetReference':{'byPath':{'path':'../EvidenceAnalyst.SemanticModel'}}})
save(MODEL/'definition.pbism',{'version':'1.0','settings':{}})

orders = pd.read_csv(ROOT.parent/'data/cleaned.csv').fillna({'region':'Unknown'})
cols = [('order_id','string'),('order_date','dateTime'),('region','string'),('units','int64'),('unit_price','double'),('discount','double'),('revenue','double')]
csv = orders.to_csv(index=False).replace('"','""').splitlines()
# Embedded synthetic sample keeps refresh portable without an absolute local path.
m = 'let\n    Source = Csv.Document(Text.ToBinary("' + '\n'.join(csv) + '"), [Delimiter=",", Columns=7, Encoding=65001, QuoteStyle=QuoteStyle.Csv]),\n    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),\n    Types = Table.TransformColumnTypes(Headers, {{"order_id", type text}, {"order_date", type date}, {"region", type text}, {"units", Int64.Type}, {"unit_price", type number}, {"discount", type number}, {"revenue", type number}}, "en-US")\nin\n    Types'
measures = [('Total Revenue','SUM(Orders[revenue])','$#,0.00'),('Order Count','DISTINCTCOUNT(Orders[order_id])','#,0'),('Average Order Value','DIVIDE([Total Revenue], [Order Count])','$#,0.00'),('Units Sold','SUM(Orders[units])','#,0'),('Missing Regions','CALCULATE(COUNTROWS(Orders), Orders[region] = "Unknown")','0')]
table={'name':'Orders','columns':[{'name':n,'dataType':t,'sourceColumn':n,'summarizeBy':'none' if t in ['string','dateTime'] else 'sum',**({'formatString':'yyyy-MM-dd'} if t=='dateTime' else {})} for n,t in cols], 'partitions':[{'name':'Orders','mode':'import','source':{'type':'m','expression':m.splitlines()}}], 'measures':[{'name':n,'expression':e,'formatString':fmt} for n,e,fmt in measures]}
save(MODEL/'model.bim',{'name':'EvidenceAnalyst','compatibilityLevel':1567,'model':{'culture':'en-US','defaultPowerBIDataSourceVersion':'powerBI_V3','tables':[table],'annotations':[{'name':'PBI_QueryOrder','value':'["Orders"]'}]}})
save(DEF/'version.json',{'$schema':schema('versionMetadata'),'version':'2.0.0'})
save(DEF/'report.json',{'$schema':schema('report'),'layoutOptimization':'None','themeCollection':{'baseTheme':{'name':'CY24SU06','reportVersionAtImport':'5.55','type':'SharedResources'}}})
save(DEF/'pages/pages.json',{'$schema':schema('pagesMetadata'),'pageOrder':['0123456789abcdef0123'],'activePageName':'0123456789abcdef0123'})
save(DEF/'pages/0123456789abcdef0123/page.json',{'$schema':schema('page'),'name':'0123456789abcdef0123','displayName':'Retail overview | Synthetic demo','displayOption':'FitToPage','width':1280,'height':720})

def lit(value):
    return {'expr':{'Literal':{'Value':str(value).lower() if isinstance(value,bool) else "'"+str(value).replace("'","''")+"'"}}}

def field(name, measure=False):
    return {('Measure' if measure else 'Column'):{'Expression':{'SourceRef':{'Entity':'Orders'}},'Property':name}}

def projection(name, measure=False):
    return {'field':field(name,measure),'queryRef':'Orders.'+name,'nativeQueryRef':name}

def visual(name,kind,x,y,w,h,roles,title):
    name=hashlib.sha256(name.encode()).hexdigest()[:20]
    save(DEF/f'pages/0123456789abcdef0123/visuals/{name}/visual.json',{'$schema':schema('visualContainer'),'name':name,'position':{'x':x,'y':y,'width':w,'height':h,'z':0,'tabOrder':0},'visual':{'visualType':kind,'query':{'queryState':{role:{'projections':[projection(n,ismeasure) for n,ismeasure in fields]} for role,fields in roles.items()}},'visualContainerObjects':{'title':[{'properties':{'show':lit(True),'text':lit(title),'fontSize':{'expr':{'Literal':{'Value':'14D'}}}}}]},'drillFilterOtherVisuals':True}})

visual('Revenue','card',24,20,290,120,{'Values':[('Total Revenue',True)]},'Total revenue | Synthetic retail demo')
visual('Orders','card',338,20,280,120,{'Values':[('Order Count',True)]},'Distinct orders')
visual('AOV','card',642,20,290,120,{'Values':[('Average Order Value',True)]},'Average order value')
visual('RegionFilter','slicer',956,20,300,260,{'Values':[('region',False)]},'Filter by region')
visual('RegionRevenue','clusteredBarChart',24,160,594,245,{'Category':[('region',False)],'Y':[('Total Revenue',True)]},'Revenue by region')
visual('DailyRevenue','lineChart',24,425,908,270,{'Category':[('order_date',False)],'Y':[('Total Revenue',True)]},'Daily revenue | September 2026')
visual('RegionTable','tableEx',642,160,290,245,{'Values':[('region',False),('Order Count',True),('Total Revenue',True)]},'Reconciliation by region')
visual('Quality','card',956,425,300,120,{'Values':[('Missing Regions',True)]},'Missing region rows | Shown as Unknown')
visual('Units','card',956,565,300,130,{'Values':[('Units Sold',True)]},'Units sold')
save(ROOT/'reconciliation.json',{'orders':int(len(orders)),'revenue':float(orders.revenue.sum()),'units':int(orders.units.sum()),'aov':float(orders.revenue.sum()/orders.order_id.nunique()),'missing_regions':int(orders.region.eq('Unknown').sum()),'region_revenue':orders.groupby('region').revenue.sum().to_dict(),'note':'Synthetic data. Unknown replaces null region only in dashboard presentation.'})
print('Built native Power BI project and nine visuals at', ROOT)
