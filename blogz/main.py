from flask import Flask, request, redirect, render_template, session, flash
from flask_sqlalchemy import SQLAlchemy
import cgi

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://blogz:blogz@localhost:8888/blogz'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)
app.secret_key = 'Ampongan'

class Blog(db.Model): 

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    body = db.Column(db.String(1000))
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, title, body, owner):
        self.title = title   
        self.body = body
        self.owner = owner

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique = True)
    password = db.Column(db.String(120))
    blogs = db.relationship('Blog', backref='owner')

    def __init__(self, username, password):
        self.username = username
        self.password = password

@app.before_request
def require_login():
    allowed_routes = ['login', 'signup', 'blog', 'index']
    if request.endpoint not in allowed_routes and 'username' not in session:
        return redirect('/login')


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            session['username'] = username
            flash("Logged in.")
            print(session)
            return redirect('/newpost')
        else:
            flash('User password incorrect, or user does not exist', 'error')

    return render_template('login.html')



@app.route('/signup', methods=['POST', 'GET'])
def signup():
    username = ""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        verify = request.form['verify']

        # TODO - validate user's data

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Duplicate User')
        elif len(username) < 3 or len(password) < 3:
            flash('Invalid username or password.')
        elif password != verify:
            flash('Passwords do not match.')
        elif not existing_user and password == verify:
            new_user = User(username, password)
            db.session.add(new_user)
            db.session.commit()
            session['username'] = username
            return redirect('/newpost')
        
    return render_template('signup.html', username = username)



@app.route('/blog', methods=['POST', 'GET'])
def blog():
    view = 'default'
    blogs = []

    if request.args:
        id = request.args.get('id')
        username = request.args.get('user')
        if id:
            blogs.append(Blog.query.get(id))
            view = 'single'
        else:
            owner = User.query.filter_by(username = username).first()
            blogs = Blog.query.filter_by(owner = owner).all()
    else:
        blogs = Blog.query.all()    


    return render_template('blog.html', title="Blogz", blogs=blogs, view=view)


@app.route('/newpost', methods=['POST', 'GET'])  
def newpost():
    title = ""
    title_error = ""
    body = ""
    body_error = ""
    owner = User.query.filter_by(username = session['username']).first()

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']

        if not len(title) > 0:
            title_error = "Title must contain a value"
            
        if not len(body) > 0:
            body_error = "Body must contian a value"
         
        if not(title_error) and not(body_error):
            new_post = Blog(title = title, body = body, owner = owner )
            db.session.add(new_post)
            db.session.commit()
            db.session.refresh(new_post)
            return redirect('/blog?id='+ str(new_post.id))            
    
    return render_template('newpost.html', page_title = "Add A Post", title = title, 
        title_error = title_error, body = body, body_error = body_error) 

@app.route('/logout')
def logout():
    del session['username']
    return redirect('/blog')



@app.route('/', methods=['POST', 'GET'])
def index():
    users = User.query.all()
    return render_template('index.html', title="Blogz", users=users)


if __name__ == '__main__':
    app.run()