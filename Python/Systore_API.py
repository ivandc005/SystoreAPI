from flask import Flask, jsonify, request, render_template
from sqlalchemy import create_engine, text
import xml.dom.minidom

app = Flask(__name__)

# Setup connessione al DB (SQL Server)
connection_string = "mssql+pyodbc://SYSTEM_ITALI:SYS123@localhost/WSHAVI?driver=ODBC+Driver+17+for+SQL+Server"
engine = create_engine(connection_string)

#menu generale per visualizzare il tutto
@app.route('/')
def index():
    return render_template('menu.html')

#creazione funzione per formattare xml
def prettify_xml(xml_string):
    try:
        dom = xml.dom.minidom.parseString(xml_string)
        return dom.toprettyxml(indent="  ")
    except Exception:
        return xml_string
    
@app.route('/tabella_report_dry')
def tabella_report_dry():
    with engine.connect() as conn:
        result = conn.execute(text("set dateformat ymd "
                                    "declare @databeg nvarchar(20) = (select (FORMAT(DATEADD(DAY, 0, GETDATE()), 'yyyy-MM-dd'))), @dataend nvarchar(20) = (select (FORMAT(DATEADD(DAY, 1, GETDATE()), 'yyyy-MM-dd')))"
                                    " exec ws_CUSTOM_L2_FlowCheck_Dry @databeg, @dataend, 24, 60"))
        rows2 = [dict(zip(result.keys(), row)) for row in result]
    colonne2 = result.keys()
    return render_template('tabella.html', dati=rows2, colonne=colonne2)

@app.route('/tabella_report_frozen')
def tabella_report_frozen():
    with engine.connect() as conn:
        result = conn.execute(text("set dateformat ymd "
                                    "declare @databeg nvarchar(20) = (select (FORMAT(DATEADD(DAY, 0, GETDATE()), 'yyyy-MM-dd'))), @dataend nvarchar(20) = (select (FORMAT(DATEADD(DAY, 1, GETDATE()), 'yyyy-MM-dd')))"
                                    " exec ws_CUSTOM_L2_FlowCheck_Frozen @databeg, @dataend, 24, 60"))
        rows3 = [dict(zip(result.keys(), row)) for row in result]
    colonne3 = result.keys()
    return render_template('tabella.html', dati=rows3, colonne=colonne3)

#restituisco tabella di import    
@app.route('/tabella_import')
def tabella_import():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT top 100 * FROM HOST_IMPORT order by IMP_TIME desc"))
        rows = [dict(zip(result.keys(), row)) for row in result]
        # Formattare i campi XML
        for riga in rows:
            if 'IMP_DATA' in riga and riga['IMP_DATA']:
                riga['IMP_DATA'] = prettify_xml(riga['IMP_DATA'])
            if 'IMP_DATA_XML' in riga and riga['IMP_DATA_XML']:
                riga['IMP_DATA_XML'] = prettify_xml(riga['IMP_DATA_XML'])
    colonne = result.keys()  
    return render_template('tabelle_imp_exp.html', dati=rows, colonne=colonne)

@app.route('/tabella_export')
def tabella_export():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT top 100 * FROM HOST_EXPORT order by EXP_TIME desc"))
        rows3 = [dict(zip(result.keys(), row)) for row in result]
        # Formattare i campi XML
        for riga in rows3:
            if 'EXP_DATA' in riga and riga['EXP_DATA']:
                riga['EXP_DATA'] = prettify_xml(riga['EXP_DATA'])
            if 'EXP_DATA_XML' in riga and riga['EXP_DATA_XML']:
                riga['EXP_DATA_XML'] = prettify_xml(riga['EXP_DATA_XML'])
    colonne3 = result.keys()  
    return render_template('tabelle_imp_exp.html', dati=rows3, colonne=colonne3)



if __name__ == '__main__':
    app.run(debug=True)
