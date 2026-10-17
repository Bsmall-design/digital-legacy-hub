from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_file
import sqlite3
import os, io, csv, json
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

app=Flask(__name__, template_folder='../web/templates', static_folder='../web/static', static_url_path='/static'); app.secret_key=os.environ.get('SECRET_KEY', os.environ.get('DLH_SECRET','change-this-secret-key'))
DB=os.path.join(os.path.dirname(__file__),'legacy.db')
DATA_DIR=os.path.join(os.path.dirname(__file__),'datasets'); os.makedirs(DATA_DIR,exist_ok=True)


def db():
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c

def init():
    c=db(); c.executescript('''
    CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT,email TEXT UNIQUE,password TEXT,role TEXT DEFAULT 'student',created_at TEXT DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS paths(id INTEGER PRIMARY KEY AUTOINCREMENT,title TEXT,slug TEXT UNIQUE,icon TEXT,description TEXT);
    CREATE TABLE IF NOT EXISTS lessons(id INTEGER PRIMARY KEY AUTOINCREMENT,path_id INTEGER,title TEXT,content TEXT,order_no INTEGER);
    CREATE TABLE IF NOT EXISTS progress(user_id INTEGER,lesson_id INTEGER,completed_at TEXT DEFAULT CURRENT_TIMESTAMP,PRIMARY KEY(user_id,lesson_id));
    CREATE TABLE IF NOT EXISTS challenges(id INTEGER PRIMARY KEY AUTOINCREMENT,path_id INTEGER,title TEXT,question TEXT,solution TEXT);
    CREATE TABLE IF NOT EXISTS attempts(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,challenge_id INTEGER,answer TEXT,score INTEGER,created_at TEXT DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS projects(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,title TEXT,description TEXT,status TEXT DEFAULT 'Draft',created_at TEXT DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS ai_messages(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,role TEXT,message TEXT,created_at TEXT DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS datasets(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT,slug TEXT UNIQUE,description TEXT,filename TEXT);
    CREATE TABLE IF NOT EXISTS certificates(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,path_id INTEGER,code TEXT UNIQUE,issued_at TEXT DEFAULT CURRENT_TIMESTAMP);
    ''')
    if c.execute('SELECT COUNT(*) FROM paths').fetchone()[0]==0:
        paths=[('Programming Foundations','programming','⌘','Algorithms, Python, problem solving and coding fundamentals.'),('Data Analytics','analytics','◈','Excel, SQL, Python, statistics, dashboards and real datasets.'),('Database Engineering','database','▦','Relational databases, SQL, design, keys, joins and normalization.'),('Web Development','web','◉','HTML, CSS, JavaScript, responsive interfaces and deployment.'),('Cyber & Network','cyber','◇','Networking, security principles and practical digital safety.'),('Digital Productivity','productivity','✦','Word, Excel, PowerPoint, collaboration and professional workflows.')]
        c.executemany('INSERT INTO paths(title,slug,icon,description) VALUES(?,?,?,?)',paths)
        lesson_map={'programming':['Algorithms & Flowcharts','Variables & Data Types','Conditions','Loops','Functions','Basic Python','Problem Solving'],'analytics':['Data Fundamentals','Excel for Analysis','SQL Fundamentals','Statistics Basics','Python & Pandas','Data Cleaning','Visualization & Dashboards','Final Analytics Project'],'database':['Database Concepts','Tables & Keys','Relationships','SELECT & Filtering','JOINs','Normalization','Database Project'],'web':['HTML Foundations','CSS Layout','JavaScript Basics','Forms & Validation','Responsive Design','Web Project'],'cyber':['Network Fundamentals','Threats & Vulnerabilities','Authentication & Access','Safe Computing','Cybersecurity Project'],'productivity':['Professional Documents','Excel Essentials','Presentations','Digital Collaboration','Productivity Project']}
        for p in c.execute('SELECT id,slug FROM paths').fetchall():
            for i,t in enumerate(lesson_map[p['slug']],1):
                content=f'''<h2>{t}</h2><p>This lesson is part of the Digital Legacy Hub curriculum. Read the concept, study the example, complete the practice task and then attempt the challenge.</p><h3>Learning objective</h3><p>Understand the core idea and apply it to a small real-world problem.</p><h3>Practice</h3><p>Write down the input, process and expected output before you build. Test with at least two examples.</p>'''
                c.execute('INSERT INTO lessons(path_id,title,content,order_no) VALUES(?,?,?,?)',(p['id'],t,content,i))
            first=lesson_map[p['slug']][0]; c.execute('INSERT INTO challenges(path_id,title,question,solution) VALUES(?,?,?,?)',(p['id'],first+' Challenge','Explain the core idea and give one practical example.','Break the problem into steps, identify inputs and expected output, implement or explain the process, then test your example.'))
    if c.execute('SELECT COUNT(*) FROM datasets').fetchone()[0]==0:
        c.execute('INSERT INTO datasets(name,slug,description,filename) VALUES(?,?,?,?)',('Student Performance Dataset','student-performance','A practice dataset for cleaning, grouping, averages and visualization.','student_performance.csv'))
        c.execute('INSERT INTO datasets(name,slug,description,filename) VALUES(?,?,?,?)',('Sales Transactions','sales-transactions','A practice dataset for SQL aggregation, trends and product analysis.','sales_transactions.csv'))
    admin_email=os.environ.get('ADMIN_EMAIL'); admin_pw=os.environ.get('ADMIN_PASSWORD')
    if admin_email and admin_pw and not c.execute("SELECT 1 FROM users WHERE role='admin' LIMIT 1").fetchone():
        c.execute("INSERT OR IGNORE INTO users(name,email,password,role) VALUES(?,?,?,'admin')",('Platform Admin',admin_email.lower(),generate_password_hash(admin_pw)))
    c.commit(); c.close()
    seed_datasets()

def seed_datasets():
    p=os.path.join(DATA_DIR,'student_performance.csv')
    if not os.path.exists(p):
        rows=[['student_id','name','gender','department','attendance','score'],['S001','Aisha','F','Computer Science',92,86],['S002','Musa','M','Computer Science',78,72],['S003','Zainab','F','Data Science',95,91],['S004','Umar','M','Data Science',81,68],['S005','Fatima','F','Cyber Security',88,79],['S006','Ali','M','Computer Science',90,83],['S007','Maryam','F','Data Science',97,94],['S008','Sani','M','Cyber Security',75,61]]
        with open(p,'w',newline='') as f: csv.writer(f).writerows(rows)
    p=os.path.join(DATA_DIR,'sales_transactions.csv')
    if not os.path.exists(p):
        rows=[['id','date','product','category','quantity','unit_price'],[1,'2026-09-01','Laptop','Electronics',2,650000],[2,'2026-09-02','Mouse','Accessories',15,8500],[3,'2026-09-03','Keyboard','Accessories',8,18000],[4,'2026-09-04','Laptop','Electronics',1,650000],[5,'2026-09-05','Monitor','Electronics',4,210000],[6,'2026-09-06','Mouse','Accessories',20,8500]]
        with open(p,'w',newline='') as f: csv.writer(f).writerows(rows)
init()

def user():
    if 'uid' not in session:return None
    c=db(); u=c.execute('SELECT * FROM users WHERE id=?',(session['uid'],)).fetchone(); c.close(); return u

def admin_required(): return user() and user()['role']=='admin'

@app.context_processor
def inject(): return {'current_user':user()}

@app.route('/')
def home(): return render_template('index.html',u=user())
@app.route('/register',methods=['GET','POST'])
def register():
    if request.method=='POST':
        try:
            c=db(); c.execute('INSERT INTO users(name,email,password) VALUES(?,?,?)',(request.form['name'],request.form['email'].lower(),generate_password_hash(request.form['password']))); c.commit(); uid=c.execute('SELECT last_insert_rowid()').fetchone()[0]; c.close(); session['uid']=uid; return redirect(url_for('dashboard'))
        except sqlite3.IntegrityError: flash('Email already registered.')
    return render_template('auth.html',mode='Register')
@app.route('/login',methods=['GET','POST'])
def login():
    if request.method=='POST':
        c=db(); u=c.execute('SELECT * FROM users WHERE email=?',(request.form['email'].lower(),)).fetchone(); c.close()
        if u and check_password_hash(u['password'],request.form['password']): session['uid']=u['id']; return redirect(url_for('dashboard'))
        flash('Invalid email or password.')
    return render_template('auth.html',mode='Login')
@app.route('/logout')
def logout(): session.clear(); return redirect(url_for('home'))

@app.route('/dashboard')
def dashboard():
    u=user();
    if not u:return redirect(url_for('login'))
    c=db(); paths=c.execute('SELECT * FROM paths').fetchall(); total=c.execute('SELECT COUNT(*) FROM lessons').fetchone()[0]; done=c.execute('SELECT COUNT(*) FROM progress WHERE user_id=?',(u['id'],)).fetchone()[0]; projects=c.execute('SELECT * FROM projects WHERE user_id=?',(u['id'],)).fetchall(); attempts=c.execute('SELECT COUNT(*) n,COALESCE(AVG(score),0) avg FROM attempts WHERE user_id=?',(u['id'],)).fetchone(); c.close()
    return render_template('dashboard.html',u=u,paths=paths,total=total,done=done,projects=projects,attempts=attempts)

@app.route('/path/<slug>')
def path(slug):
    u=user(); c=db(); p=c.execute('SELECT * FROM paths WHERE slug=?',(slug,)).fetchone()
    if not p:return redirect(url_for('dashboard'))
    lessons=c.execute('SELECT l.*,CASE WHEN pr.user_id IS NULL THEN 0 ELSE 1 END done FROM lessons l LEFT JOIN progress pr ON l.id=pr.lesson_id AND pr.user_id=? WHERE l.path_id=? ORDER BY order_no',(u['id'] if u else -1,p['id'])).fetchall(); ch=c.execute('SELECT * FROM challenges WHERE path_id=?',(p['id'],)).fetchall(); cert=c.execute('SELECT * FROM certificates WHERE user_id=? AND path_id=?',(u['id'],p['id'])).fetchone() if u else None; c.close(); return render_template('path.html',u=u,p=p,lessons=lessons,challenges=ch,cert=cert)

@app.route('/lesson/<int:lid>',methods=['GET','POST'])
def lesson(lid):
    u=user();
    if not u:return redirect(url_for('login'))
    c=db(); l=c.execute('SELECT l.*,p.title path_title,p.slug FROM lessons l JOIN paths p ON p.id=l.path_id WHERE l.id=?',(lid,)).fetchone()
    if request.method=='POST': c.execute('INSERT OR IGNORE INTO progress(user_id,lesson_id) VALUES(?,?,)',(u['id'],lid)) if False else c.execute('INSERT OR IGNORE INTO progress(user_id,lesson_id) VALUES(?,?)',(u['id'],lid)); c.commit(); c.close(); return redirect(url_for('path',slug=l['slug']))
    c.close(); return render_template('lesson.html',u=u,l=l)

@app.route('/challenge/<int:cid>',methods=['GET','POST'])
def challenge(cid):
    u=user();
    if not u:return redirect(url_for('login'))
    c=db(); ch=c.execute('SELECT ch.*,p.slug,p.title path_title FROM challenges ch JOIN paths p ON p.id=ch.path_id WHERE ch.id=?',(cid,)).fetchone(); submitted=False
    if request.method=='POST':
        answer=request.form.get('answer',''); score=min(100,max(10,len(answer.strip())*2)); c.execute('INSERT INTO attempts(user_id,challenge_id,answer,score) VALUES(?,?,?,?)',(u['id'],cid,answer,score)); c.commit(); submitted=True
    c.close(); return render_template('challenge.html',u=u,ch=ch,submitted=submitted)

@app.route('/projects',methods=['GET','POST'])
def projects():
    u=user();
    if not u:return redirect(url_for('login'))
    c=db()
    if request.method=='POST': c.execute('INSERT INTO projects(user_id,title,description,status) VALUES(?,?,?,?)',(u['id'],request.form['title'],request.form['description'],request.form.get('status','Draft'))); c.commit()
    ps=c.execute('SELECT * FROM projects WHERE user_id=? ORDER BY id DESC',(u['id'],)).fetchall(); c.close(); return render_template('projects.html',u=u,projects=ps)

# Python code playground: browser executes with Pyodide; this endpoint just supplies the page.
@app.route('/code')
def code(): return render_template('code.html',u=user())

# Safe in-memory SQL playground using a fresh SQLite database per request.
@app.route('/sql')
def sql():
    c=db(); datasets=c.execute('SELECT * FROM datasets').fetchall(); c.close(); return render_template('sql.html',u=user(),datasets=datasets)
@app.route('/api/sql',methods=['POST'])
def api_sql():
    q=request.json.get('query','').strip(); slug=request.json.get('dataset','student-performance')
    if not q:return jsonify(error='Enter a SQL query.')
    c=db(); d=c.execute('SELECT * FROM datasets WHERE slug=?',(slug,)).fetchone(); c.close()
    if not d:return jsonify(error='Dataset not found.')
    mem=sqlite3.connect(':memory:'); mem.row_factory=sqlite3.Row
    try:
        with open(os.path.join(DATA_DIR,d['filename']),newline='') as f: rows=list(csv.reader(f))
        headers=rows[0]; mem.execute('CREATE TABLE data (%s)' % ','.join('"%s" TEXT'%h for h in headers)); mem.executemany('INSERT INTO data VALUES (%s)'%','.join('?',)*len(headers),rows[1:]); mem.commit()
        # Only SELECT/EXPLAIN/PRAGMA are allowed.
        first=q.lstrip().split(None,1)[0].upper()
        if first not in ('SELECT','WITH','EXPLAIN','PRAGMA'): return jsonify(error='Only read-only queries are allowed in the playground.')
        cur=mem.execute(q); out=[dict(r) for r in cur.fetchmany(200)]; cols=[x[0] for x in cur.description] if cur.description else []
        return jsonify(columns=cols,rows=out)
    except Exception as e: return jsonify(error=str(e))
    finally: mem.close()

@app.route('/datasets')
def datasets():
    c=db(); ds=c.execute('SELECT * FROM datasets').fetchall(); c.close(); return render_template('datasets.html',u=user(),datasets=ds)
@app.route('/dataset/<slug>')
def dataset(slug):
    c=db(); d=c.execute('SELECT * FROM datasets WHERE slug=?',(slug,)).fetchone(); c.close()
    if not d:return redirect(url_for('datasets'))
    with open(os.path.join(DATA_DIR,d['filename']),newline='') as f: rows=list(csv.reader(f))
    return render_template('dataset.html',u=user(),d=d,headers=rows[0],rows=rows[1:])

@app.route('/analytics')
def analytics():
    u=user();
    if not u:return redirect(url_for('login'))
    c=db(); stats=c.execute('SELECT COUNT(*) lessons FROM progress WHERE user_id=?',(u['id'],)).fetchone(); att=c.execute('SELECT COUNT(*) attempts,COALESCE(AVG(score),0) avg_score FROM attempts WHERE user_id=?',(u['id'],)).fetchone(); projects=c.execute('SELECT COUNT(*) n FROM projects WHERE user_id=?',(u['id'],)).fetchone(); c.close()
    return render_template('analytics.html',u=u,stats=stats,att=att,projects=projects)

@app.route('/certificate/<int:path_id>')
def certificate(path_id):
    u=user();
    if not u:return redirect(url_for('login'))
    c=db(); p=c.execute('SELECT * FROM paths WHERE id=?',(path_id,)).fetchone(); total=c.execute('SELECT COUNT(*) FROM lessons WHERE path_id=?',(path_id,)).fetchone()[0]; done=c.execute('SELECT COUNT(*) FROM progress pr JOIN lessons l ON l.id=pr.lesson_id WHERE pr.user_id=? AND l.path_id=?',(u['id'],path_id)).fetchone()[0]; cert=c.execute('SELECT * FROM certificates WHERE user_id=? AND path_id=?',(u['id'],path_id)).fetchone()
    if total and done>=total:
        if not cert:
            code=f'DLH-{u["id"]}-{path_id}-{datetime.utcnow().strftime("%Y%m%d%H%M%S")}'; c.execute('INSERT INTO certificates(user_id,path_id,code) VALUES(?,?,?)',(u['id'],path_id,code)); c.commit(); cert=c.execute('SELECT * FROM certificates WHERE user_id=? AND path_id=?',(u['id'],path_id)).fetchone()
        c.close(); return render_template('certificate.html',u=u,p=p,cert=cert)
    c.close(); flash('Complete all lessons in this learning path before issuing the certificate.'); return redirect(url_for('path',slug=p['slug']))

# Optional real AI: set OPENAI_API_KEY and install openai. Without it, the tutor uses a safe local guidance fallback.
@app.route('/ai',methods=['POST'])
def ai():
    u=user(); msg=(request.json or {}).get('message','').strip()
    if not u:return jsonify(error='Login required.'),401
    if not msg:return jsonify(error='Ask me something about your learning.')
    answer=None
    key=os.environ.get('OPENAI_API_KEY')
    if key and OpenAI:
        try:
            client=OpenAI(api_key=key)
            r=client.responses.create(model=os.environ.get('OPENAI_MODEL','gpt-5.6-luna'),input=[{'role':'system','content':'You are Legacy Guide, a patient professional tutor inside Digital Legacy Hub. Teach by explanation, example, hint, practice, and feedback. Do not simply give away challenge answers unless the learner asks for the solution.'},{'role':'user','content':msg}])
            answer=r.output_text
        except Exception as e: answer='AI service is temporarily unavailable. Try again or continue with the built-in guidance.'
    if not answer:
        low=msg.lower()
        if 'loop' in low: answer='A loop repeats a block of code. In Python, start with for loops: for item in items:. Trace each iteration with a small list, then try a practice task.'
        elif 'sql' in low or 'database' in low: answer='Think of SQL as asking a database precise questions. Start with SELECT and WHERE, then GROUP BY and JOIN. In the SQL Playground you can practice safely on the supplied datasets.'
        elif 'data' in low or 'pandas' in low: answer='A data-analysis workflow is: understand the question → inspect the dataset → clean → analyze → visualize → communicate. Start with the Student Performance dataset.'
        elif 'python' in low: answer='Build Python confidence in layers: variables → conditions → loops → functions → data structures → small projects. When stuck, write the expected input and output first.'
        else: answer='I am Legacy Guide. Tell me your topic, what you already understand, and exactly where you are stuck. I will guide you step by step.'
    c=db(); c.execute('INSERT INTO ai_messages(user_id,role,message) VALUES(?,?,?)',(u['id'],'user',msg)); c.execute('INSERT INTO ai_messages(user_id,role,message) VALUES(?,?,?)',(u['id'],'assistant',answer)); c.commit(); c.close(); return jsonify(answer=answer)

# Admin / CMS
@app.route('/admin',methods=['GET','POST'])
def admin():
    u=user()
    if not admin_required(): return redirect(url_for('dashboard'))
    c=db()
    if request.method=='POST':
        action=request.form.get('action')
        if action=='lesson': c.execute('INSERT INTO lessons(path_id,title,content,order_no) VALUES(?,?,?,?)',(request.form['path_id'],request.form['title'],request.form['content'],request.form.get('order_no',99)))
        elif action=='challenge': c.execute('INSERT INTO challenges(path_id,title,question,solution) VALUES(?,?,?,?)',(request.form['path_id'],request.form['title'],request.form['question'],request.form['solution']))
        c.commit()
    paths=c.execute('SELECT * FROM paths').fetchall(); users=c.execute('SELECT id,name,email,role,created_at FROM users ORDER BY id DESC').fetchall(); lessons=c.execute('SELECT l.*,p.title path_title FROM lessons l JOIN paths p ON p.id=l.path_id ORDER BY l.id DESC LIMIT 20').fetchall(); c.close(); return render_template('admin.html',u=u,paths=paths,users=users,lessons=lessons)

@app.route('/admin/promote/<int:uid>')
def promote(uid):
    if not admin_required():return redirect(url_for('dashboard'))
    c=db(); c.execute("UPDATE users SET role='admin' WHERE id=?",(uid,)); c.commit(); c.close(); return redirect(url_for('admin'))

if __name__=='__main__': app.run(debug=True)
