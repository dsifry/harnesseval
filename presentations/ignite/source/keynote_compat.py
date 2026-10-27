import copy
import zipfile
from pathlib import Path
from lxml import etree as E

root=Path(__file__).parent
ns={'c':'http://schemas.openxmlformats.org/drawingml/2006/chart', 'a':'http://schemas.openxmlformats.org/drawingml/2006/main','p':'http://schemas.openxmlformats.org/presentationml/2006/main'}
count=0
with zipfile.ZipFile(root/'candidate.pptx') as src, zipfile.ZipFile(root/'keynote-candidate.pptx','w',zipfile.ZIP_DEFLATED) as dst:
    for item in src.infolist():
        data=src.read(item.filename)
        if '/charts/' in item.filename and item.filename.endswith('.xml'):
            doc=E.fromstring(data)
            for series in doc.findall('.//c:scatterChart/c:ser',ns):
                marker=series.find('c:marker',ns)
                fill=series.find('c:spPr/a:solidFill',ns)
                assert marker is not None and fill is not None
                props=marker.find('c:spPr',ns)
                if props is None: props=E.SubElement(marker, '{'+ns['c']+'}spPr')
                for old in list(props): props.remove(old)
                props.append(copy.deepcopy(fill))
                series_name=series.find('.//c:tx//c:v',ns)
                hollow=series_name is not None and series_name.text=='Missed by highest recall configuration'
                ln=E.SubElement(props,'{'+ns['a']+'}ln',w='0')
                if hollow:
                    ln.set('w','28575')
                    solid=E.SubElement(ln,'{'+ns['a']+'}solidFill')
                    E.SubElement(solid,'{'+ns['a']+'}srgbClr',val='F17A43')
                    series_line=series.find('c:spPr/a:ln',ns)
                    if series_line is not None:
                        for child in list(series_line): series_line.remove(child)
                        E.SubElement(series_line,'{'+ns['a']+'}noFill')
                else: E.SubElement(ln,'{'+ns['a']+'}noFill')
                count+=1
            data=E.tostring(doc,xml_declaration=True,encoding='UTF-8',standalone=True)
        if item.filename.startswith('ppt/slides/slide') and item.filename.endswith('.xml'):
            doc=E.fromstring(data)
            trans=doc.find('p:transition',ns)
            if trans is None:
                trans=E.Element('{'+ns['p']+'}transition')
                timing=doc.find('p:timing',ns)
                ext=doc.find('p:extLst',ns)
                if timing is not None: doc.insert(list(doc).index(timing),trans)
                elif ext is not None: doc.insert(list(doc).index(ext),trans)
                else: doc.append(trans)
            trans.set('advClick','0');trans.set('advTm','15000')
            data=E.tostring(doc,xml_declaration=True,encoding='UTF-8',standalone=True)
        if item.filename.startswith('ppt/notesSlides/notesSlide') and item.filename.endswith('.xml'):
            doc=E.fromstring(data)
            body=doc.xpath('.//p:sp[p:nvSpPr/p:nvPr/p:ph[@type="body"]]/p:txBody',namespaces=ns)[0]
            for i,para in enumerate(body.findall('a:p',ns)):
                for run in para.findall('a:r',ns):
                    props=run.find('a:rPr',ns)
                    if props is None:
                        props=E.Element('{'+ns['a']+'}rPr');run.insert(0,props)
                    props.set('sz','3600' if i==0 else '2400' if i==2 else '1200')
                    props.set('b','1' if i==0 else '0')
                    E.SubElement(props,'{'+ns['a']+'}latin',typeface='Helvetica Neue')
            data=E.tostring(doc,xml_declaration=True,encoding='UTF-8',standalone=True)
        dst.writestr(item,data)
assert count==7,count
print('Explicit fills repaired for 7 scatter series including hollow misses; 20 static 15-second advances added.')
