from flask import Flask, jsonify, request, render_template, session, redirect, url_for
from sqlalchemy import create_engine, text
import xml.dom.minidom
from datetime import datetime

# Importa il sistema di traduzioni
from translations import translation_manager, inject_translations

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-in-production'  # IMPORTANTE: Cambia in produzione!

# Setup connessione al DB (SQL Server)
connection_string = "mssql+pyodbc://SYSTEM_ITALI:SYS123@localhost/WSHAVI?driver=ODBC+Driver+17+for+SQL+Server"
engine = create_engine(connection_string)


# ============================================================================
# CONTEXT PROCESSOR - Rende disponibili le traduzioni in TUTTI i template
# ============================================================================
@app.context_processor
def inject_translation_functions():
    """Inietta automaticamente le funzioni di traduzione in tutti i template"""
    return {
        't': translation_manager.get,  # Funzione di traduzione
        'current_lang': translation_manager.get_current_language(),
        'supported_langs': translation_manager.supported_languages,
        'year': datetime.now().year  # Per il copyright dinamico
    }


# ============================================================================
# ROUTE: Cambio lingua
# ============================================================================
@app.route('/set-language/<lang>')
def set_language(lang):
    """Endpoint per cambiare la lingua dell'interfaccia"""
    if translation_manager.set_language(lang):
        # Salva la lingua nella sessione
        return redirect(request.referrer or url_for('index'))
    else:
        return jsonify({'error': 'Language not supported'}), 400


# ============================================================================
# ROUTE: API per ottenere traduzioni (per JavaScript)
# ============================================================================
@app.route('/api/translations/<lang>')
def get_translations_api(lang):
    """API per recuperare tutte le traduzioni di una lingua (per uso JS)"""
    if lang in translation_manager.translations:
        return jsonify(translation_manager.translations[lang])
    return jsonify({'error': 'Language not found'}), 404


# ============================================================================
# FUNZIONI UTILITY
# ============================================================================
def prettify_xml(xml_string):
    """Formatta XML in modo leggibile"""
    try:
        dom = xml.dom.minidom.parseString(xml_string)
        return dom.toprettyxml(indent="  ")
    except Exception:
        return xml_string


# ============================================================================
# ROUTES - Homepage e Tabelle
# ============================================================================
@app.route('/')
def index():
    """Homepage con menu principale"""
    return render_template('homepage.html')


@app.route('/tabella_report_dry')
def tabella_report_dry():
    """Report DRY - Flow Check ultime 24h"""
    with engine.connect() as conn:
        result = conn.execute(text(
            "set dateformat ymd "
            "declare @databeg nvarchar(20) = (select (FORMAT(DATEADD(DAY, 0, GETDATE()), 'yyyy-MM-dd'))), "
            "@dataend nvarchar(20) = (select (FORMAT(DATEADD(DAY, 1, GETDATE()), 'yyyy-MM-dd'))) "
            "exec ws_CUSTOM_L2_FlowCheck_Dry @databeg, @dataend, 24, 60"
        ))
        rows = [dict(zip(result.keys(), row)) for row in result]
    
    colonne = result.keys()
    return render_template('tabelle.html', dati=rows, colonne=colonne)


@app.route('/tabella_report_frozen')
def tabella_report_frozen():
    """Report FROZEN - Flow Check ultime 24h"""
    with engine.connect() as conn:
        result = conn.execute(text(
            "set dateformat ymd "
            "declare @databeg nvarchar(20) = (select (FORMAT(DATEADD(DAY, 0, GETDATE()), 'yyyy-MM-dd'))), "
            "@dataend nvarchar(20) = (select (FORMAT(DATEADD(DAY, 1, GETDATE()), 'yyyy-MM-dd'))) "
            "exec ws_CUSTOM_L2_FlowCheck_Frozen @databeg, @dataend, 24, 60"
        ))
        rows = [dict(zip(result.keys(), row)) for row in result]
    
    colonne = result.keys()
    return render_template('tabelle.html', dati=rows, colonne=colonne)


@app.route('/tabella_import')
def tabella_import():
    """Tabella HOST_IMPORT - Ultimi 100 record"""
    with engine.connect() as conn:
        result = conn.execute(text("SELECT top 100 * FROM HOST_IMPORT order by IMP_TIME desc"))
        rows = [dict(zip(result.keys(), row)) for row in result]
        
        # Formattazione XML
        for riga in rows:
            if 'IMP_DATA' in riga and riga['IMP_DATA']:
                riga['IMP_DATA'] = prettify_xml(riga['IMP_DATA'])
            if 'IMP_DATA_XML' in riga and riga['IMP_DATA_XML']:
                riga['IMP_DATA_XML'] = prettify_xml(riga['IMP_DATA_XML'])
    
    colonne = result.keys()
    return render_template('tabelle_imp_exp.html', dati=rows, colonne=colonne)


@app.route('/tabella_export')
def tabella_export():
    """Tabella HOST_EXPORT - Ultimi 100 record"""
    with engine.connect() as conn:
        result = conn.execute(text("SELECT top 100 * FROM HOST_EXPORT order by EXP_TIME desc"))
        rows = [dict(zip(result.keys(), row)) for row in result]
        
        # Formattazione XML
        for riga in rows:
            if 'EXP_DATA' in riga and riga['EXP_DATA']:
                riga['EXP_DATA'] = prettify_xml(riga['EXP_DATA'])
            if 'EXP_DATA_XML' in riga and riga['EXP_DATA_XML']:
                riga['EXP_DATA_XML'] = prettify_xml(riga['EXP_DATA_XML'])
    
    colonne = result.keys()
    return render_template('tabelle_imp_exp.html', dati=rows, colonne=colonne)


@app.route('/avvisi_di_ingresso')
def avvisi_di_ingresso():
    """Avvisi di ingresso in attesa/esecuzione/incompleto"""
    with engine.connect() as conn:
        result = conn.execute(text(
            "SET DATEFORMAT YMD SET NOCOUNT ON "
            "declare @aree nvarchar(500) "
            "select @aree = MAS_ELEAREE from GESTORI_MASTER where MAS_MASTER = N'MAIN' "
            "declare @baia int = isnull(cast(N'' as int), 0) "
            "declare @scomparto int = isnull(cast(N'' as int), 0) "
            "declare @sco_articolo nvarchar(50), @sco_sub1 nvarchar(50), @sco_sub2 nvarchar(50), "
            "@sco_stamate nvarchar(5), @sco_tipoconf nvarchar(5) "
            "if @scomparto > 0 begin "
            "  select @sco_articolo = SCO_ARTICOLO, @sco_sub1 = SCO_SUB1, @sco_sub2 = SCO_SUB2, "
            "    @sco_stamate = SCO_STAMATE, @sco_tipoconf = SCO_TIPOCONF "
            "  from DAT_SCOMPART where SCO_SCOMPARTO = @scomparto "
            "end "
            "SET NOCOUNT OFF "
            "select top 100 "
            "  [RIG_ORDINE],[RIG_RIGA],[RIG_STARIORD],[RIG_PRIO],[RIG_ARTICOLO],"
            "  CASE WHEN ART_ARTICOLO <> '' THEN dbo.fn_td(ART_DES) ELSE '' END as [ART_DES],"
            "  [RIG_SUB1],[RIG_SUB2],[RIG_STAMATE],[RIG_TIPOCONF],[RIG_SSCC_SOURCE],[RIG_QTAR],"
            "  [RIG_QTAI],[RIG_QTAE],CASE WHEN ART_ARTICOLO <> '' THEN ART_UMI ELSE '' END as [ART_UMI],"
            "  [RIG_REQ_NOTE],[RIG_ERR],[RIG_DCREA],[RIG_DMOD],[RIG_DMOV],[RIG_PADRE_RIGA],"
            "  [RIG_HOSTINF],[RIG_HOSTCAUS],[RIG_HOSTRIF],[RIG_NESE],[RIG_NESE_SIM],[RIG_QTAI_SIM],"
            "  [RIG_HOST],[RIG_EXPORDINE],[ORD_TIPOOP],"
            "  CASE WHEN ORD_FIX = 1 THEN ORD_DES "
            "       WHEN ORD_PADRE_ORDINE <> '' THEN ORD_PADRE_ORDINE "
            "       ELSE ORD_ORDINE END as [ORD_ORDINE_SHOW],"
            "  [RIG_LOCNO],[RIG_DRY_CORR], "
            "  case when RIG_ERR = 1 then 16 else 0 end as STYLE, "
            "  RIG_HOST as [~READONLY] "
            "from DAT_ORDINI "
            "  inner join TIPI_ORDINI on TORD_ORDTYPE = ORD_ORDTYPE "
            "  inner join DAT_ORDINI_RIGHE on RIG_ORDINE = ORD_ORDINE "
            "  inner join DAT_ARTICOLI on ART_ARTICOLO = RIG_ARTICOLO "
            "where ORD_ORDINE <> '' and ORD_IMME = 0 and ORD_TIPOOP IN ('E', 'V') "
            "  and TORD_WITH_CHILDREN = 0 and ORD_EXPORDINE = '' "
            "  and dbo.fn_IntersInsiemi(@aree, ORD_ELEAREE, ',') <> ',' "
            "  and (@baia = 0 or ORD_ELEBAIE = '' or ORD_ELEBAIE like ('%,' + cast(@baia as nvarchar) + ',%')) "
            "  and RIG_RIGA <> 0 and RIG_EXPORDINE = '' and RIG_SPLIT_SIM = 0 "
            "  and (@scomparto = 0 or @sco_articolo = '' or ( "
            "    @sco_articolo = RIG_ARTICOLO and @sco_sub1 = RIG_SUB1 and @sco_sub2 = RIG_SUB2 "
            "    and @sco_stamate = RIG_STAMATE and @sco_tipoconf = RIG_TIPOCONF)) "
            "ORDER BY [RIG_PRIO],[RIG_RIGA]"
        ))
        rows = [dict(zip(result.keys(), row)) for row in result]
    
    colonne = result.keys()
    return render_template('tabelle.html', dati=rows, colonne=colonne)


@app.route('/lancio_ordini')
def lancio_ordini():
    """Ordini di uscita in attesa/esecuzione/incompleto"""
    with engine.connect() as conn:
        result = conn.execute(text(
            "set DATEFORMAT YMD "
            "SELECT [ORD_ORDINE],"
            "  CASE WHEN ORD_PADRE_ORDINE <> '' THEN ORD_PADRE_ORDINE ELSE ORD_ORDINE END as [ORD_ORDINE_SHOW],"
            "  [ORD_SPEDIZIONE],[ORD_DES],[ORD_FASEORD],[CALC_ORD_STATO],'' as [ORD_DISP],"
            "  [ORD_PRIOHOST],[ORD_EXEPRIOHOST],[ORD_EXEPRIO],"
            "  CAST(case when (isnull(count(RIG_RIGA),0) > 0) then 1 else 0 end AS bit) as [ORD_ERR],"
            "  [ORD_ELEAREE],[ORD_ELEBAIE],"
            "  CASE WHEN ORD_ELEBAIE = ',25,35,' THEN 'TD02_A' "
            "       WHEN ORD_ELEBAIE = ',1144,'  THEN 'TF02_A' "
            "       WHEN ORD_ELEBAIE = ',1205,'  THEN 'TF05_A' "
            "       ELSE BCO_COD END as [ORD_BAIAHOST],"
            "  [ORD_ALL],[ORD_TIPOOP],[ORD_TIPOSCHED],[ORD_SCHED_RESULT],[ORD_SCHED_RESULT_NOTE],"
            "  case when ORD_CSTYPE = 'RP' then 'REPLENISHMENT' "
            "       when ORD_CSTYPE = 'PW' then 'ROLLOUT_LU' "
            "       when ORD_CSTYPE = 'CL' then 'FPP_ORDER' end as [ORD_CSTYPE], "
            "  case when CALC_ORD_STATO like '%,I,%' then 16 "
            "       when CALC_ORD_STATO like '%,W,%' then 0 "
            "       when CALC_ORD_STATO like '%,E,%' then 12 "
            "       else 13 end AS STYLE "
            "FROM DAT_ORDINI "
            "  inner join TIPI_ORDINI on TORD_ORDTYPE = ORD_ORDTYPE "
            "  inner join dbo.fn_Calc_ORD_RIGHE_FIELDS() on (CALC_ORD_ORDINE = ORD_ORDINE) "
            "  INNER JOIN TIPI_OPERAZIONI on (TORD_TIPOOP = ORD_TIPOOP) "
            "  LEFT OUTER JOIN DAT_ORDINI_RIGHE ON (ORD_ORDINE = RIG_ORDINE AND RIG_ERR = 1) "
            "  INNER JOIN GESTORI_MASTER ON (MAS_MASTER = N'MAS_IDICEGLIE') "
            "  LEFT OUTER JOIN MAG_BAIE ON (ORD_ELEBAIE = ',' + convert(nvarchar(20), BCO_BAIA) + ',') "
            "WHERE ORD_ORDINE <> '' AND TORD_WITH_CHILDREN = 0 AND ORD_EXPORDINE = '' "
            "  AND ORD_IMME = 0 AND ORD_TIPOOP NOT IN ('E') "
            "  AND dbo.fn_IntersInsiemi(MAS_ELEAREE, ORD_ELEAREE, ',') <> ',' "
            "  AND CALC_ORD_RIGHESIM_SPLIT = 0 AND ORD_TIPOSCHED = 'A' "
            "GROUP BY [ORD_ORDINE],"
            "  CASE WHEN ORD_PADRE_ORDINE <> '' THEN ORD_PADRE_ORDINE ELSE ORD_ORDINE END,"
            "  [ORD_SPEDIZIONE],[ORD_DES],[ORD_FASEORD],[CALC_ORD_STATO],[ORD_PRIOHOST],"
            "  [ORD_EXEPRIOHOST],[ORD_EXEPRIO],[ORD_ELEAREE],[ORD_ELEBAIE],"
            "  CASE WHEN ORD_ELEBAIE = ',25,35,' THEN 'TD02_A' "
            "       WHEN ORD_ELEBAIE = ',1144,'  THEN 'TF02_A' "
            "       WHEN ORD_ELEBAIE = ',1205,'  THEN 'TF05_A' "
            "       ELSE BCO_COD END,[ORD_ALL],[ORD_TIPOOP],[ORD_TIPOSCHED],"
            "  [ORD_SCHED_RESULT],[ORD_SCHED_RESULT_NOTE],"
            "  case when ORD_CSTYPE = 'RP' then 'REPLENISHMENT' "
            "       when ORD_CSTYPE = 'PW' then 'ROLLOUT_LU' "
            "       when ORD_CSTYPE = 'CL' then 'FPP_ORDER' end "
            "ORDER BY ORD_EXEPRIOHOST, ORD_EXEPRIO, [ORD_ORDINE]"
        ))
        rows = [dict(zip(result.keys(), row)) for row in result]
    
    colonne = result.keys()
    return render_template('tabelle.html', dati=rows, colonne=colonne)


@app.route('/operazioni_da_eseguire')
def operazioni_da_eseguire():
    """Operazioni da eseguire generate dagli ordini"""
    with engine.connect() as conn:
        result = conn.execute(text(
            "declare @listabaie nvarchar(500), @riga int; "
            "select @listabaie = isnull(dbo.fn_IntersInsiemi(isnull(N'', ''), '', ','), ''); "
            "select @riga = case when isnumeric(N'') = 1 then cast(N'' as int) else 0 end; "
            "if (object_id('tempdb..#tblEseIdResult') IS NOT NULL) drop table #tblEseIdResult; "
            "CREATE TABLE #tblEseIdResult (FLD_ESEID int, FLD_ERROR nvarchar(max) collate database_default); "
            "SELECT TOP 10000 [ESE_ID],[ESE_TIME],[ESE_BAIA],[ESE_CAUSMISS],[ESE_UDC],[ESE_SCOMPARTO],"
            "  [RIG_ARTICOLO],CASE WHEN ART_ARTICOLO <> '' THEN dbo.fn_td(ART_DES) ELSE '' END as [ART_DES],"
            "  [RIG_SUB1],[RIG_SUB2],[RIG_SSCC_SOURCE],[UDC_SSCC],[RIG_STAMATE],[RIG_TIPOCONF],"
            "  [ESE_QTAR],CASE WHEN ART_ARTICOLO <> '' THEN ART_UMI ELSE '' END as [ART_UMI],"
            "  a.ORD_TIPOOP as [ORD_TIPOOP],ORDS.ORD_SPEDIZIONE as [Spedizione],"
            "  CASE WHEN UDC_ORDINE >'' then udc_ORDINE "
            "       WHEN a.ORD_FIX = 1 THEN '' ELSE a.ORD_PADRE_ORDINE END as [ORD_ORDINE_SHOW],"
            "  [ESE_RIGA],[UDC_CORRIDOIO],[UDC_CELLA],[UDC_POS],[UDC_DEP],[UDC_LEV],"
            "  case when MIS_FIN_BAIA > 0 then MIS_FIN_BAIA else isnull(MIS_D_BAIA, 0) end as [DESTINAZIONE],"
            "  [ESE_RICTIPO],[ESE_BPRIO],[ESE_PRIO],[ESE_SIMU],[ESE_SOSPESA],[FLD_ERROR],"
            "  CASE WHEN MIS_MISSIONE IS NULL THEN 0 "
            "       WHEN ESE_BAIA = case when MIS_FIN_BAIA > 0 then MIS_FIN_BAIA else MIS_D_BAIA end then 12 "
            "       ELSE 16 END AS STYLE "
            "FROM RUN_ESEGUI "
            "  INNER JOIN DAT_UDC WITH (INDEX(PK_DAT_UDC)) ON (UDC_UDC = ESE_UDC) "
            "  INNER JOIN TIPI_CAUSALI_MISSIONI ON (CAUM_CAUSMISS = ESE_CAUSMISS) "
            "  INNER JOIN DAT_ORDINI_RIGHE ON (RIG_RIGA = ESE_RIGA) "
            "  left outer join DAT_ARTICOLI on ART_ARTICOLO = RIG_ARTICOLO and ART_ARTICOLO <> '' "
            "  INNER JOIN DAT_ORDINI a ON (ORD_ORDINE = RIG_ORDINE) "
            "  INNER JOIN MAG_BAIE ON (BCO_BAIA = ESE_BAIA) "
            "  Left join dat_ORDini ORDS on ords.ord_ordine =udc_ORDINE "
            "  Inner join DAT_SPEDIZIONI ON SPE_SPEDIZIONE = ORDS.ORD_SPEDIZIONE "
            "  LEFT OUTER JOIN RUN_MISSIONI ON (MIS_UDC = ESE_UDC) "
            "  left outer join #tblEseIdResult on (FLD_ESEID = ESE_ID) "
            "WHERE ESE_BAIA <> 0 and ESE_CAUSMISS <> '' and CAUM_ENTRATA = 0 "
            "  and (0 = 0 OR (ESE_ID in (select BLK_ID from dbo.fn_tabRigheEseguiBloccate()))) "
            "  and (@listabaie = '' or @listabaie like '%,' + cast(ESE_BAIA as nvarchar) + ',%') "
            "  and @riga in (0, ESE_RIGA) "
            "ORDER BY [ESE_ID] OPTION (FORCE ORDER)"
        ))
        rows = [dict(zip(result.keys(), row)) for row in result]
    
    colonne = result.keys()
    return render_template('tabelle.html', dati=rows, colonne=colonne)


@app.route('/run_missioni')
def run_missioni():
    """Missioni in esecuzione"""
    with engine.connect() as conn:
        result = conn.execute(text(
            ";with MISSIONI as ( "
            "select *, MIS_MODULO as C_MODULO, MIS_GES_S_MODULO as C_MODULO_SORG, "
            "  MIS_GES_D_MODULO as C_MODULO_DEST, "
            "  dbo.fn_getDesStatoGestMiss(MIS_L2STA, MIS_L1STA, MIS_GES_STA, MIS_GES_GESTORE) as MIS_GESTORESTATO, "
            "  dbo.fn_getDesSorgDestMiss(MIS_S_BAIA, MIS_S_PIAZZOLA, MIS_S_CORRIDOIO, MIS_S_CELLA, MIS_S_POS, MIS_S_DEP, MIS_S_LEV) as C_SORGENTE, "
            "  case when MIS_D_CORRIDOIO <> 0 or (MIS_D_BAIA > 0 and (MIS_D_BAIA = MIS_FIN_BAIA or MIS_FIN_BAIA = 0)) "
            "       then dbo.fn_getDesSorgDestMiss(MIS_D_BAIA, MIS_D_PIAZZOLA, MIS_D_CORRIDOIO, MIS_D_CELLA, MIS_D_POS, MIS_D_DEP,MIS_D_LEV) "
            "       else dbo.fn_getDesSorgDestMiss(MIS_FIN_BAIA, 0, MIS_D_CORRIDOIO, MIS_D_CELLA, MIS_D_POS, MIS_D_DEP,MIS_D_LEV) "
            "  end as C_DESTINAZIONE, "
            "  case when MIS_TRANS_LGV_PITCH > 0 then CONCAT(dbo.fn_td(N'Baia'), N' ', MIS_TRANS_LGV_PITCH) "
            "       when (MIS_D_BAIA > 0 and (MIS_D_BAIA = MIS_FIN_BAIA or MIS_FIN_BAIA = 0)) or MIS_D_CORRIDOIO > 0 then ' - ' "
            "       else dbo.fn_getDesSorgDestMiss(MIS_D_BAIA, MIS_D_PIAZZOLA, MIS_D_CORRIDOIO, MIS_D_CELLA, MIS_D_POS, MIS_D_DEP,MIS_D_LEV) "
            "  end as C_TRANSITO, "
            "  case when BIN_CELLA > 0 then BIN_CELLA else MIS_D_CELLA end as D_CELLA, "
            "  case when BIN_CORRIDOIO > 0 then BIN_CORRIDOIO else MIS_D_CORRIDOIO end as D_CORRIDOIO, "
            "  case when BIN_CELLA > 0 then 0 else MIS_D_BAIA end as D_BAIA "
            "from RUN_MISSIONI "
            "  inner join DAT_UDC ON (MIS_UDC = UDC_UDC) "
            "  inner join DAT_ARTICOLI ON (UDC_ARTICOLO = ART_ARTICOLO) "
            "  left outer join MAG_BAIE_INTERNE on BIN_MODULO = MIS_GES_D_MODULO "
            "    and MIS_GES_STA in ('WA', 'EX') and BIN_CORRIDOIO > 0 and BIN_CELLA > 0 and MIS_D_BAIA > 0 "
            "where (MIS_MISSIONE <> 0) "
            ") "
            "select TOP 1000 * from MISSIONI order by [MIS_MISSIONE]"
        ))
        rows = [dict(zip(result.keys(), row)) for row in result]
    
    colonne = result.keys()
    return render_template('tabelle.html', dati=rows, colonne=colonne)


# ============================================================================
# AVVIO APPLICAZIONE
# ============================================================================
if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 Systore API Dashboard con Sistema i18n")
    print("="*60)
    print(f"✓ Lingue supportate: {', '.join(translation_manager.supported_languages)}")
    print(f"✓ Lingua di default: {translation_manager.default_language}")
    print("="*60 + "\n")
    app.run(debug=True)