#!/usr/bin/env python
#@+leo-ver=5-thin
#@+node:ekr.20120309073748.9872: * @file bigdash.py
#@@first

''' Global search window

To use full text search, you need to install Whoosh library ('easy_install Whoosh').
The fts_max_hits setting controls the maximum hits returned.
'''
# By VMV.
#@+<< implementation notes >>
#@+node:ville.20120302233106.3583: ** << implementation notes >>
#@@nocolor-node
#@+at
# I (Terry) added an index of the oulines containing hits at the top of the
# output. Because the link handling is already handled by BigDash and not the
# WebView widget, I couldn't find a way to use the normal "#id" <href>/<a>
# index jumping, so I extended the link handling to re-run the search and
# render hits in the outline of interest at the top.
# 
# 
#@-<< implementation notes >>

import leo.core.leoGlobals as g
from leo.core.leoQt import QtCore,QtGui,QtWidgets,QtWebKitWidgets
try:
    import leo.plugins.leofts as leofts    
except ImportError:
    leofts = None
import sys

g = None

#@+others
#@+node:ville.20120225144051.3580: ** top-level functions
#@+node:ekr.20140919160020.17922: *3* add_anchor
def add_anchor(l,tgt, text):

    l.append('<a href="%s">%s</a>' % (tgt, text))    
#@+node:ekr.20140919160020.17918: *3* all_positions_global
def all_positions_global():

    for c in g.app.commanders():
        for p in c.all_unique_positions():
            yield (c,p)
#@+node:ville.20120302233106.3580: *3* init
def init ():
    '''Return True if the plugin has loaded successfully.'''
    set_leo(g)
    ok = g.app.gui.guiName() == "qt"
    g._global_search = None
    if ok:

        @g.command("global-search")
        def global_search_f(event):
            """ Do global search """
            c = event['c']
            if g._global_search:
                g._global_search.show()
            else:
                g._global_search = gs = GlobalSearch()
                set_leo(g)
                if leofts:
                    leofts.init()

        g.plugin_signon(__name__)
    return ok
#@+node:ekr.20140919160020.17921: *3* matchlines
def matchlines(b, miter):

    res = []
    for m in miter:
        st, en = g.getLine(b, m.start())
        li = b[st:en]
        ipre = b.rfind("\n", 0, st-2)
        ipost = b.find("\n", en +1 )
        spre = b[ipre +1 : st-1] + "\n"
        spost = b[en : ipost]
        
        res.append((li, (m.start()-st, m.end()-st ), (spre, spost)))
    return res
#@+node:ekr.20140919160020.17919: *3* open_unl
def open_unl(unl):

    parts = unl.split("#",1)
    c = g.openWithFileName(parts[0])
    if len(parts) > 1:
        segs = parts[1].split("-->")
        g.recursiveUNLSearch(segs, c)
#@+node:ekr.20140919160020.17917: *3* set_leo
def set_leo(gg):
    global g
    g = gg
#@+node:ekr.20140919160020.17909: ** class BigDash
class BigDash:
    #@+others
    #@+node:ekr.20140919160020.17916: *3* __init__
    def __init__(self):
        self.handlers = []
        self.link_handler = lambda x : 1
        self.create_ui()
    #@+node:ekr.20140919160020.17913: *3* _lnk_handler
    def _lnk_handler(self, url):
        self.link_handler(str(url.toString()))
    #@+node:ekr.20140919160020.17912: *3* add_cmd_handler
    def add_cmd_handler(self,f):
        self.handlers.append(f)
    #@+node:ekr.20140919160020.17915: *3* create_ui
    def create_ui(self):

        self.w = w = QtWidgets.QWidget()
        w.setWindowTitle("Leo search")
        lay = QtWidgets.QVBoxLayout()
        self.web = web = QtWebKitWidgets.QWebView(w)
        self.web.linkClicked.connect(self._lnk_handler)
        self.led = led = QtWidgets.QLineEdit(w)
        led.returnPressed.connect(self.docmd)
        lay.addWidget(led)
        lay.addWidget(web)
        self.lc = lc = LeoConnector()
        web.page().mainFrame().addToJavaScriptWindowObject("leo",lc)
        web.page().setLinkDelegationPolicy(QtWebKitWidgets.QWebPage.DelegateAllLinks)
        w.setLayout(lay)
        #web.load(QUrl("http://google.fi"))
        self.show_help()
        w.show()
        def help_handler(tgt,qs):
            if qs == "help":
                self.show_help()
                return True
            return False
        self.add_cmd_handler(help_handler)
        self.led.setFocus()
    #@+node:ekr.20140919160020.17910: *3* docmd
    def docmd(self):
        t = self.led.text()
        for h in self.handlers:
            r = h(self, t)
            if r:
                # handler that accepts the call should return True
                break
    #@+node:ekr.20140919160020.17911: *3* set_link_handler
    def set_link_handler(self,lh):
        self.link_handler = lh
    #@+node:ekr.20140919160020.17914: *3* show_help
    def show_help(self):
        
        self.web.setHtml("""\
            <h12>Dashboard</h2>
            <table cellspacing="10">
            <tr><td> <b>s</b> foobar</td><td>   <i>Simple string search for "foobar" in all open documents</i></td></tr>
            <tr><td> <b>fts init</b></td><td>   <i>Initialize full text search  (create index) for all open documents</i></td></tr>
            <tr><td> <b>fts add</b></td><td>   <i>Add currently open, still unindexed leo files to index</i></td></tr>                    
            <tr><td> <b>f</b> foo bar</td><td>   <i>Do full text search for node with terms 'foo' AND 'bar'</i></td></tr>
            <tr><td> <b>f</b> h:foo b:bar wild?ards*</td><td>   <i>Search for foo in heading and bar in body, test wildcards</i></td></tr>
            <tr><td> <b>help</b></td><td>   <i>Show this help</i></td></tr>
            <tr><td> <b>stats</b></td><td>   <i>List indexed files</i></td></tr>
            <tr><td> <b>fts refresh</b></td><td>   <i>re-index files</i></td></tr>
            </table>
            
            """)
        
    #@-others
#@+node:ekr.20140919160020.17897: ** class GlobalSearch
class GlobalSearch:
    #@+others
    #@+node:ekr.20140919160020.17898: *3* __init__
    def __init__(self):
        self.bd = BigDash()
        #self.bd.show()
        self.bd.add_cmd_handler(self.do_search)
        self.bd.add_cmd_handler(self.do_fts)
        self.bd.add_cmd_handler(self.do_stats)
        self.anchors = {}        
        
    #@+node:ekr.20140919160020.17899: *3* show
    def show(self):

        self.bd.w.show()
        
    #@+node:ekr.20140919160020.17900: *3* do_stats
    def do_stats(self, tgt, qs):

        if qs != "stats":
            return False
        s = self.get_fts().statistics()
        docs = s['documents']
        tgt.web.setHtml("<p>Indexed documents:</p><ul>" + "".join("<li>%s</li>" % doc for doc in docs) + "</ul>" )
            
    #@+node:ekr.20140919160020.17901: *3* get_fts
    def get_fts(self):

        return leofts.get_fts()

    #@+node:ekr.20140919160020.17902: *3* do_fts
    def do_fts(self, tgt, qs):

        ss = g.toUnicode(qs)
        q = None
        if ss.startswith("f "):
            q = ss[2:]
            
        if not (q or ss.startswith("fts ")):
            return False
        if not leofts:
            g.es("Whoosh not installed (easy_install whoosh)")
            return False
        print("Doing fts", qs)
        fts = self.get_fts()
        if ss.strip() == "fts init":
            print("init!")
            fts.create()
            for c2 in g.app.commanders():
                print("Scanning",c2)
                fts.index_nodes(c2)
        if ss.strip() == "fts add":
            print("Add new docs")
            docs = set(fts.statistics()["documents"])
            print("Have docs", docs )
            for c2 in g.app.commanders():
                fn = c2.mFileName
                if fn in docs:
                    continue
                print("Adding document to index:",fn)
                fts.index_nodes(c2)
        if ss.strip() == "fts refresh":
            for c2 in g.app.commanders():
                fn = c2.mFileName
                print("Refreshing", fn)
                fts.drop_document(fn)
                fts.index_nodes(c2)
            gc = g._gnxcache            
            gc.clear()
            gc.update_new_cs()
        if q:
            self.do_find(tgt, q)

    #@+node:ekr.20140919160020.17903: *3* do_search
    def do_search(self,tgt, qs):   
         
        ss = str(qs)
        hitparas = []
        def em(l):
            hitparas.append(l)
        if not ss.startswith("s "):
            return False
        s = ss[2:]
        for ndxc,c2 in enumerate(g.app.commanders()):
            hits = c2.find_b(s)                          
            for ndxh, h in enumerate(hits):
                b = h.b
                mlines = matchlines(b, h.matchiter)
                key = "c%dh%d" % (ndxc, ndxh)
                self.anchors[key] = (c2, h.copy())
                em('<p><a href="%s">%s</a></p>' % (key, h.h))
                for line, (st, en), (pre, post) in mlines:
                    em("<pre>")
                    em(pre)
                    em("%s<b>%s</b>%s" % (line[:st], line[st:en], line[en:]))
                    em(post)
                    em("</pre>")
                em("""<p><small><i>%s</i></small></p>""" % h.get_UNL()) 
        html = "".join(hitparas)
        tgt.web.setHtml(html)     
        self.bd.set_link_handler(self.do_link)

    #@+node:ekr.20140919160020.17904: *3* do_link
    def do_link(self,l):

        a = self.anchors[l]
        c, p = a
        c.selectPosition(p)
        c.bringToFront()

    #@+node:ekr.20140919160020.17905: *3* do_link_jump_gnx
    def do_link_jump_gnx(self, l):
        print ("jumping to", l)
        if l.startswith("about:blank#"):
            target_outline = l.split('#', 1)[1]
            self.do_find(self._old_tgt, self._old_q, target_outline=target_outline)
        if l.startswith("unl!"):
            l = l[4:]
            open_unl(l)
            return
        gc = g._gnxcache
        gc.update_new_cs()
        hit = gc.get_p(l)
        if hit:
            c,p = hit
            print("found!")
            c.selectPosition(p)
            c.bringToFront()
            return
        print("Not found in any open document")        
            
    #@+node:ekr.20140919160020.17906: *3* do_find
    def do_find(self, tgt, q, target_outline=None):
        self._old_tgt = tgt
        self._old_q = q
        fts = self.get_fts()
        hits = ["""
            <html><head><style>
                * { font-family: sans-serif; background: white; }
                pre { font-family: monospace; }
                pre * { font-family: monospace; }
                a { text-decoration: none; }
                a:hover { text-decoration: underline; color: red; }
                pre { margin-top: 0; margin-bottom: 0; }
            </style></head><body>
        """]
        fts_max_hits = limit=g.app.config.getInt('fts_max_hits') or 30
        res = fts.search(q, fts_max_hits)
        outlines = {}
        for r in res:
            if '#' in r["parent"]:
                file_name, node = r["parent"].split('#', 1)
            else:
                file_name, node = r["parent"], None                
            outlines.setdefault(file_name, []).append(r)
        hits.append("<p>%d hits (max. hits reported = %d)</p>"%
            (len(res), fts_max_hits))
        if len(outlines) > 1:
            hits.append("<p><div>Hits in:</div>")
            for outline in outlines:
                hits.append("<div><a href='#%s'>%s</a>"%(outline, outline))   
                if outline == target_outline:
                    hits.append("<b> (moved to top)</b>")
                hits.append("</div>")       
            hits.append("</p>")
        outline_order = outlines.keys()
        outline_order.sort(key=lambda x:'' if x==target_outline else x)
        for outline in outline_order:
            hits.append("<div id='%s'><p><b>%s</b></p>"%(outline, outline))
            res = outlines[outline]
            for r in res:
                #print("hit", r)
                hits.append("<p>")
                hits.append("<div>")
                add_anchor(hits, r["gnx"], r["h"])
                hits.append("</div>")
                # always show opener link because r['f'] is True when
                # outline was open but isn't any more (GnxCache stale)
                if False and r['f']:
                    opener = ""
                else:
                    opener = ' (<a href="unl!%s">open</a>)' % r["parent"]
                hl = r.get("highlight")
                if hl:
                    hits.append("<pre>%s</pre>" % hl)
                    
                hits.append("""<div><small><i>%s</i>%s</small></div>""" % (r["parent"], opener))          
                hits.append("</p>")    
                
            hits.append("<hr/></div>")
            
        hits.append("</body></html>")
        html = "".join(hits)
        tgt.web.setHtml(html)
        self.bd.set_link_handler(self.do_link_jump_gnx)
    #@-others
#@+node:ekr.20140919160020.17920: ** class LeoConnector
class LeoConnector(QtCore.QObject):
    pass

#@-others

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    bd = GlobalSearch()
    sys.exit(app.exec_())

#@@language python
#@@tabwidth -4
#@-leo
