#!/usr/bin/env python2.7

"""
Columbia W4111 Intro to databases
Example webserver
To run locally
    python server.py
Go to http://localhost:8111 in your browser
A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""

import os

from flask import (Flask, Response, abort, flash, g, redirect, render_template,
                   request, session)
from sqlalchemy import *
from sqlalchemy.pool import NullPool

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)
genders = ['Female', 'Male', 'Non-binary', 'NA']
myprofile=dict()



# XXX: The Database URI should be in the format of: 
#
#     postgresql://USER:PASSWORD@<IP_OF_POSTGRE_SQL_SERVER>/<DB_NAME>
#
# For example, if you had username ewu2493, password foobar, then the following line would be:
#
#     DATABASEURI = "postgresql://ewu2493:foobar@<IP_OF_POSTGRE_SQL_SERVER>/postgres"
#
# For your convenience, we already set it to the class database

# Use the DB credentials you received by e-mail
DB_USER = "zj2334"
DB_PASSWORD = "1502"

DB_SERVER = "w4111project1part2db.cisxo09blonu.us-east-1.rds.amazonaws.com"

DATABASEURI = "postgresql://"+DB_USER+":"+DB_PASSWORD+"@"+DB_SERVER+"/proj1part2"


#
# This line creates a database engine that knows how to connect to the URI above
#
engine = create_engine(DATABASEURI)


# Here we create a test table and insert some values in it
engine.execute("""DROP TABLE IF EXISTS test;""")
engine.execute("""CREATE TABLE IF NOT EXISTS test (
  id serial,
  name text
);""")
engine.execute("""INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace');""")



@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request 
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request
  The variable g is globally accessible
  """
  try:
    g.conn = engine.connect()
  except:
    print ("uh oh, problem connecting to database")
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass


def reset():
  session['genders']=genders
  session['signup']=dict()
  session['modifyprofile']=dict()
  session['myprofile']=dict()

@app.route('/')
def home():
  if not session.get('uid') or session['uid']=='':
    reset()
    return render_template('login.html')
  else:
	  return render_template('user_main_page.html')

@app.route('/login', methods=['POST'])
def login():
  login_query="SELECT * FROM users WHERE name=(%s) AND passwd=(%s);"
  data=(request.form['username'], request.form['password'],)
  cursor=g.conn.execute(login_query,data)
  row = cursor.fetchone()
  if  row:
    reset()
    session['uid']=row['uid']
  else:
    cursor.close()
    return render_template('wrong_password.html')
  cursor.close()
  return home()

@app.route("/retry", methods=['POST'])
def retry():
	session['logged_in'] = False
	return home()

@app.route("/sendmessage", methods=['POST'])
def sendmessage():
  if not session.get('uid') or session['uid']=='':
    return home()
  get_next_cid_query="SELECT max(cid)+1 as cid FROM chat_send_receive;"
  cursor=g.conn.execute(get_next_cid_query)
  row = cursor.fetchone()
  cid=row['cid']
  send_query="INSERT INTO chat_send_receive VALUES ((%s),(%s),(%s),(%s),(%s));"
  data=(cid, str(session['uid']),str(request.form['uid']),'now' ,request.form['content'],)
  g.conn.execute(send_query,data)
  return chat()

@app.route("/chat", methods=['POST'])
def chat():
  if not session.get('uid') or session['uid']=='':
    return home()
  chat_query="SELECT sender,content FROM chat_send_receive WHERE (sender=(%s) and receiver=(%s)) or (sender=(%s) and receiver=(%s)) ORDER BY t;"
  myname=g.conn.execute('SELECT name FROM users WHERE uid=(%s)',(session['uid'],)).fetchone()['name']
  data=(session['uid'],request.form['uid'],request.form['uid'],session['uid'],)
  raw=g.conn.execute(chat_query,data)
  messages=[]
  for message in raw:
    if message['sender']==session['uid']:
      messages.append(dict([('name',myname),('content',message['content'])]))
    else:
      messages.append(dict([('name',request.form['username']),('content',message['content'])]))
  other=dict([('uid',request.form['uid']),('name',request.form['username'])])
  Liked=False
  if g.conn.execute('SELECT * FROM Liked WHERE A_uid=(%s) AND B_uid=(%s)', (int(request.form['uid']),session['uid'],)).fetchone():
    Liked=True
  return render_template('chat.html', **dict([('messages',messages),('other',other),("Liked",Liked)]))

@app.route("/logout", methods=['POST'])
def logout():
  session['uid']=''
  return home()

@app.route("/signuppage", methods=['POST'])
def signuppage():
	return render_template('sign_up.html')

@app.route("/myprofilepage", methods=['POST'])
def myprofilepage():
  if not session.get('uid') or session['uid']=='':
    return home()
  reset()
  login_query="SELECT * FROM users WHERE uid=(%s);"
  data=(session['uid'],)
  cursor=g.conn.execute(login_query,data)
  row = cursor.fetchone()
  session['myprofile']['username'] = row['name']
  session['myprofile']['password'] = row['passwd']
  session['myprofile']['uid']=row['uid']
  session['myprofile']['gender'] =  row['gender']
  session['myprofile']['self_desc']= row['self_description']
  session['myprofile']['city']=row['city'] 
  session['myprofile']['bday'] = row['birthday']
  session['myprofile']['pgender']=row['p_gender']
  session['myprofile']['pcity']=row['p_city']
  session['myprofile']['page'] = row['p_age']
  session['myprofile']['genders']=genders
  return render_template('my_profile_page.html',**session['myprofile'])

@app.route("/getuserinformation", methods=['POST'])
def getuserinformation():
  if not session.get('uid') or session['uid']=='':
    return home()
  reset()
  login_query="SELECT * FROM users WHERE uid=(%s);"
  data=(request.form['uid'],)
  cursor=g.conn.execute(login_query,data)
  row = cursor.fetchone()
  user=dict()
  user['username'] = row['name']
  user['password'] = row['passwd']
  user['uid']=row['uid']
  user['gender'] =  row['gender']
  user['self_desc']= row['self_description']
  user['city']=row['city'] 
  user['bday'] = row['birthday']
  user['pgender']=row['p_gender']
  user['pcity']=row['p_city']
  user['page'] = row['p_age']
  user['genders']=genders
  return render_template('user_profile_page.html',**user)

@app.route("/userspage", methods=['POST'])
def userspage():
  if not session.get('uid') or session['uid']=='':
    return home()
  offset=0
  try:
    offset=int(request.form["page_num"])
  except:
    pass
  get_users_count_query="SELECT COUNT (*) AS count FROM users WHERE NOT uid=(%s) ;"
  get_users_query="SELECT uid,name FROM users WHERE NOT uid=(%s) LIMIT 7 OFFSET (%s)"
  data=(session['uid'],offset*7,)
  users=g.conn.execute(get_users_query,data).fetchall()
  count=int(g.conn.execute(get_users_count_query,(session['uid'],)).fetchone()['count'])//7
  data=dict([('users',users),('count',list(range(0,count+1))),('page_num',offset)])
  return render_template('users.html', **data)

@app.route("/posts", methods=['POST'])
def posts():
  if not session.get('uid') or session['uid']=='':
    return home()
  get_posts_count_query="SELECT COUNT (*) AS count FROM post_posted;"
  get_posts_query="SELECT P.uid,P.pid, P.content,U.name, P.nlikes FROM post_posted AS P,users AS U WHERE P.uid=U.uid ORDER BY t DESC LIMIT 7 OFFSET (%s)"
  offset=0
  try:
    offset=int(request.form['page_num'])
  except:
    pass
  posts=g.conn.execute(get_posts_query,offset*7).fetchall()
  count=int(g.conn.execute(get_posts_count_query).fetchone()['count'])//7
  data=dict([('posts',posts),('count',list(range(0,count+1))),('page_num',offset)])
  return render_template('posts.html', **data)

@app.route("/comments", methods=['POST'])
def comments():
  if not session.get('uid') or session['uid']=='':
    return home()
  get_comments_count_query="SELECT COUNT (*) AS count FROM comment_post_belong WHERE pid=(%s);"
  get_comments_query="SELECT C.cid, C.uid, C.content, U.name, C.nlikes FROM comment_post_belong AS C,users AS U WHERE C.pid=(%s) AND U.uid=C.uid ORDER BY t LIMIT 7 OFFSET (%s)"
  offset=0
  try:
    offset=int(request.form['page_num'])
  except:
    pass
  comments=g.conn.execute(get_comments_query,(request.form['pid'], offset*7)).fetchall()
  count=int(g.conn.execute(get_comments_count_query,request.form['pid']).fetchone()['count'])//7
  post=g.conn.execute('SELECT * FROM post_posted,users WHERE post_posted.pid=(%s) AND post_posted.uid=users.uid',request.form['pid']).fetchone()
  data=dict([('comments',comments),('count',list(range(0,count+1))),('page_num',offset),('post',post)])
  return render_template('comments.html', **data)

@app.route("/likecomment", methods=['POST'])
def likecomment():
  if not session.get('uid') or session['uid']=='':
    return home()
  get_comment_like_query="SELECT nlikes FROM comment_post_belong WHERE cid=(%s);"
  nlikes=int(g.conn.execute(get_comment_like_query, (request.form['cid'],)).fetchone()['nlikes'])+1
  increment_comment_like_query="UPDATE comment_post_belong SET nlikes=(%s) WHERE cid=(%s)"
  g.conn.execute(increment_comment_like_query,(nlikes,request.form['cid'],))
  return comments()

@app.route("/deletecomment", methods=['POST'])
def deletecomment():
  if not session.get('uid') or session['uid']=='':
    return home()
  delete_query="DELETE FROM comment_post_belong WHERE cid=(%s)"
  g.conn.execute(delete_query, (request.form['cid'],))
  return comments()

@app.route("/addcomment", methods=['POST'])
def addcomment():
  if not session.get('uid') or session['uid']=='':
    return home()
  get_next_cid_query="SELECT max(cid)+1 as cid FROM comment_post_belong;"
  cid=g.conn.execute(get_next_cid_query).fetchone()['cid']
  send_query="INSERT INTO comment_post_belong VALUES ((%s),(%s),(%s),(%s),(%s),(%s));"
  data=(cid, session['uid'],request.form['pid'],'now' ,request.form['content'],0,)
  g.conn.execute(send_query,data)
  return comments()

@app.route("/likepost", methods=['POST'])
def likepost():
  if not session.get('uid') or session['uid']=='':
    return home()
  get_post_like_query="SELECT nlikes FROM post_posted WHERE pid=(%s);"
  nlikes=int(g.conn.execute(get_post_like_query, (request.form['pid'],)).fetchone()['nlikes'])+1
  increment_post_like_query="UPDATE post_posted SET nlikes=(%s) WHERE pid=(%s)"
  g.conn.execute(increment_post_like_query,(nlikes,request.form['pid'],))
  return posts()

@app.route("/deletepost", methods=['POST'])
def deletepost():
  if not session.get('uid') or session['uid']=='':
    return home()
  delete_query="DELETE FROM post_posted WHERE pid=(%s)"
  g.conn.execute(delete_query, (request.form['pid'],))
  return posts()

@app.route("/addpost", methods=['POST'])
def addpost():
  if not session.get('uid') or session['uid']=='':
    return home()
  get_next_pid_query="SELECT max(pid)+1 as pid FROM post_posted;"
  pid=g.conn.execute(get_next_pid_query).fetchone()['pid']
  send_query="INSERT INTO post_posted VALUES ((%s),(%s),(%s),(%s),(%s));"
  data=(pid, session['uid'],'now' ,request.form['content'],0,)
  g.conn.execute(send_query,data)
  return posts()

@app.route("/modifymyprofilepage", methods=['POST'])
def modifymyprofilepage():
  if not session.get('uid') or session['uid']=='':
    return home()
  return render_template('modify_myprofile.html')


@app.route("/modifymyprofile", methods=['POST'])
def modifymyprofile():
  if not session.get('uid') or session['uid']=='':
    return home()
  if (len(request.form['password'])>0 and len(request.form['password'])<6):
    session['modifyprofile']['short_password'] = True
    return modifymyprofilepage()
  
  username=session['myprofile']['username']
  if not len(request.form['username'])==0:
    username=request.form['username']
  
  password=session['myprofile']['password']
  if not len(request.form['password'])==0:
    password=request.form['password']
  if not session['myprofile']['username']==username or not session['myprofile']['password']==password:
    check_query="SELECT * FROM users WHERE name=(%s) AND passwd=(%s);"
    data=(username, password,)
    cursor=g.conn.execute(check_query,data)
    row = cursor.fetchone()
    if  row:
      session['modifyprofile']['dup_name_password'] = True
      return render_template('modify_myprofile.html')
  session['myprofile']['username']=username
  session['myprofile']['password']=password

  if not request.form['gender']=='-1':
    session['myprofile']['gender']=int(request.form['gender'])

  if not len(request.form['self_desc'])==0:
    session['myprofile']['self_desc']=request.form['self_desc']

  if not len(request.form['city'])==0:
    session['myprofile']['city']=request.form['city']

  if not len(request.form['bday'])==0:
    session['myprofile']['bday']=request.form['bday']

  if not request.form['pgender']=='-1':
    session['myprofile']['pgender']=int(request.form['pgender'])

  if not len(request.form['pcity'])==0:
    session['myprofile']['pcity']=request.form['pcity']

  if not len(request.form['page'])==0:
    session['myprofile']['page']=int(request.form['page'])

  signup_query="UPDATE users SET passwd=(%s), gender=(%s), name=(%s),self_description=(%s), city=(%s), birthday=(%s), p_gender=(%s),p_city=(%s),p_age=(%s) WHERE uid=(%s);"
  data= (session['myprofile']['password'], session['myprofile']['gender'], session['myprofile']['username'], session['myprofile']['self_desc'],session['myprofile']['city'], session['myprofile']['bday'],session['myprofile']['pgender'], session['myprofile']['pcity'],session['myprofile']['page'],session['uid'],)
  g.conn.execute(signup_query,data)
  return render_template('success.html') 

@app.route("/signup", methods=['POST'])
def signup():
  reset()
  if (len(request.form['password'])<6):
    session['signup']['short_password'] = True
    return signuppage()
  if (len(request.form['username']) ==0 or len(request.form['bday'])==0):
    session['signup']['missing_input'] = True
    return signuppage()

  check_query="SELECT * FROM users WHERE name=(%s) AND passwd=(%s);"
  data=(request.form['username'], request.form['password'],)
  cursor=g.conn.execute(check_query,data)
  row = cursor.fetchone()
  if  row:
    session['signup']['dup_name_password'] = True
  else:
    check_query="SELECT max(uid)+1 as uid FROM users;"
    cursor=g.conn.execute(check_query)
    row = cursor.fetchone()
    uid=row['uid']
    page=None
    if not len(request.form['page'])==0:
      page=int(request.form['page'])
    signup_query="INSERT INTO  users VALUES ((%s),(%s),(%s),(%s),(%s),(%s),(%s),(%s),(%s),(%s));"
    data= (uid, request.form['password'], int(request.form['gender']), request.form['username'], request.form['self_desc'],request.form['city'], request.form['bday'],int(request.form['pgender']), request.form['pcity'],page)
    g.conn.execute(signup_query,data)
    return render_template('success.html')
  return render_template('sign_up.html')

@app.route("/success", methods=['POST'])
def success():
	return home()


if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)


  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using
        python server.py
    Show the help text using
        python server.py --help
    """

    HOST, PORT = host, port
    print ("running on %s:%d" % (HOST, PORT))
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)

  app.secret_key = "super secret key"

  run()
