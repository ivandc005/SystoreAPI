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
    return render_template('homepage.html')

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
    return render_template('tabelle.html', dati=rows2, colonne=colonne2)

@app.route('/tabella_report_frozen')
def tabella_report_frozen():
    with engine.connect() as conn:
        result = conn.execute(text("set dateformat ymd "
                                    "declare @databeg nvarchar(20) = (select (FORMAT(DATEADD(DAY, 0, GETDATE()), 'yyyy-MM-dd'))), @dataend nvarchar(20) = (select (FORMAT(DATEADD(DAY, 1, GETDATE()), 'yyyy-MM-dd')))"
                                    " exec ws_CUSTOM_L2_FlowCheck_Frozen @databeg, @dataend, 24, 60"))
        rows3 = [dict(zip(result.keys(), row)) for row in result]
    colonne3 = result.keys()
    return render_template('tabelle.html', dati=rows3, colonne=colonne3)

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

@app.route('/avvisi_di_ingresso')
def avvisi_di_ingresso():
    with engine.connect() as conn:
        result = conn.execute(text("SET DATEFORMAT YMD "
                                    "SET NOCOUNT ON "
                                    "declare @aree nvarchar(500) "
                                    "select @aree = MAS_ELEAREE from GESTORI_MASTER where MAS_MASTER = N'MAIN' "

                                    "declare @baia int "
                                    "select @baia = isnull(cast(N'' as int), 0) "

                                    "declare @scomparto int "
                                    "select @scomparto = isnull(cast(N'' as int), 0) "

                                    "declare "
                                    "  @sco_articolo nvarchar(50), @sco_sub1 nvarchar(50), @sco_sub2 nvarchar(50), " 
                                    "  @sco_stamate nvarchar(5), @sco_tipoconf nvarchar(5) "
                                    "if @scomparto > 0 begin "
                                    "  select "
                                    "    @sco_articolo = SCO_ARTICOLO, @sco_sub1 = SCO_SUB1, @sco_sub2 = SCO_SUB2, "
                                    "    @sco_stamate = SCO_STAMATE, @sco_tipoconf = SCO_TIPOCONF "
                                    "  from DAT_SCOMPART "
                                    "  where SCO_SCOMPARTO = @scomparto "
                                    "end "


                                    "SET NOCOUNT OFF "
                                    "select top 100 "
                                    "  [RIG_ORDINE],[RIG_RIGA],[RIG_STARIORD],[RIG_PRIO],[RIG_ARTICOLO],CASE WHEN ART_ARTICOLO <> '' THEN dbo.fn_td(ART_DES) ELSE '' END as [ART_DES],[RIG_SUB1],[RIG_SUB2],[RIG_STAMATE],[RIG_TIPOCONF],[RIG_SSCC_SOURCE],[RIG_QTAR],[RIG_QTAI],[RIG_QTAE],CASE WHEN ART_ARTICOLO <> '' THEN ART_UMI ELSE '' END as [ART_UMI],[RIG_REQ_NOTE],[RIG_ERR],[RIG_DCREA],[RIG_DMOD],[RIG_DMOV],[RIG_PADRE_RIGA],[RIG_HOSTINF],[RIG_HOSTCAUS],[RIG_HOSTRIF],[RIG_NESE],[RIG_NESE_SIM],[RIG_QTAI_SIM],[RIG_HOST],[RIG_EXPORDINE],[ORD_TIPOOP],CASE WHEN ORD_FIX = 1 THEN ORD_DES "
                                    "          WHEN ORD_PADRE_ORDINE <> '' THEN ORD_PADRE_ORDINE "
                                    "          ELSE ORD_ORDINE "
                                    "          END as [ORD_ORDINE_SHOW],[RIG_LOCNO],[RIG_DRY_CORR], "
                                    "  case when RIG_ERR = 1 then 16 "
                                    "           else 0 "
                                    "  end as STYLE "
                                    ",RIG_HOST as [~READONLY] "
                                    "from DAT_ORDINI "
                                    "  inner join TIPI_ORDINI on TORD_ORDTYPE = ORD_ORDTYPE "
                                    "  inner join DAT_ORDINI_RIGHE on RIG_ORDINE = ORD_ORDINE "
                                    "  inner join DAT_ARTICOLI on ART_ARTICOLO = RIG_ARTICOLO "
                                    "where ORD_ORDINE <> '' "
                                    "  and ORD_IMME = 0 "
                                    "  and ORD_TIPOOP IN ('E', 'V') "
                                    "  and TORD_WITH_CHILDREN = 0 "
                                    "  and ORD_EXPORDINE = '' "
                                    "  and dbo.fn_IntersInsiemi(@aree, ORD_ELEAREE, ',') <> ',' "
                                    "  and (@baia = 0 or ORD_ELEBAIE = '' or ORD_ELEBAIE like ('%,' + cast(@baia as nvarchar) + ',%')) "

                                    "  and RIG_RIGA <> 0 "
                                    "  and RIG_EXPORDINE = '' "
                                    "  and RIG_SPLIT_SIM = 0 "
                                    "  and (@scomparto = 0 or @sco_articolo = '' or ( "
                                    "    @sco_articolo = RIG_ARTICOLO "
                                    "    and @sco_sub1 = RIG_SUB1 "
                                    "    and @sco_sub2 = RIG_SUB2 "
                                    "    and @sco_stamate = RIG_STAMATE "
                                    "    and @sco_tipoconf = RIG_TIPOCONF "
                                    "  ))"
                                    "  and (1=1) "
                                    "ORDER BY "
                                    "[RIG_PRIO],[RIG_RIGA] "))
        rows_avvisi = [dict(zip(result.keys(), row)) for row in result]
    colonne_avvisi = result.keys()
    return render_template('tabelle.html', dati=rows_avvisi, colonne=colonne_avvisi)


if __name__ == '__main__':
    app.run(debug=True)
