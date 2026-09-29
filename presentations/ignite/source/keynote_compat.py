import copy
import zipfile
from pathlib import Path
from lxml import etree as E

root=Path(__file__).parent
ns={'c':'http://schemas.openxmlformats.org/drawingml/2006/chart', 'a':'http://schemas.openxmlformats.org/drawingml/2006/main','p':'http://schemas.openxmlformats.org/presentationml/2006/main'}
count=0
with zipfile.ZipFile(root/'candidate-v9.pptx') as src, zipfile.ZipFile(root/'keynote-candidate-v9.pptx','w',zipfile.ZIP_DEFLATED) as dst:
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
                ln=E.SubElement(props,'{'+ns['a']+'}ln',w='0')
                E.SubElement(ln,'{'+ns['a']+'}noFill')
                count+=1
            # Keynote drops rich-text chart label overrides. Keep labels linked
            # to their numeric values, with explicit number formats instead.
            if item.filename.endswith(('chart7.xml','chart8.xml')):
                is_cost=item.filename.endswith('chart7.xml')
                for group in doc.findall('.//c:dLbls',ns):
                    value=group.find('c:showVal',ns)
                    if value is not None: value.set('val','1')
                    fmt=E.Element('{'+ns['c']+'}numFmt',formatCode='$0.000' if is_cost else '0"s"',sourceLinked='0')
                    group.insert(0,fmt)
                    for label in group.findall('c:dLbl',ns):
                        tx=label.find('c:tx',ns)
                        if tx is not None: label.remove(tx)
                        label.find('c:showVal',ns).set('val','1')
                        idx=int(label.find('c:idx',ns).get('val'))
                        fmt=E.Element('{'+ns['c']+'}numFmt',formatCode=('$0.00' if idx==0 else '$0.000') if is_cost else '0"s"',sourceLinked='0')
                        label.insert(1,fmt)
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
        dst.writestr(item,data)
assert count==9,count
print('Explicit fills repaired for 9 scatter series; 20 static 15-second advances added.')
