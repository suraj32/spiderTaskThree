from flask import Flask, render_template, redirect, request,url_for
from flask.helpers import flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import urllib.request
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///shop.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
app.secret_key = 'spider'

UPLOAD_FOLDER = 'static/uploads/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
 
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(50), nullable=False)
    products = db.relationship('Product', backref = "owner")

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ptitle = db.Column(db.String(100), nullable=False)
    pdesc = db.Column(db.String(100), nullable=False)
    pimg = db.Column(db.String, nullable=False)
    hbid = db.Column(db.Integer)
    bidby = db.Column(db.String)
    owner_id = db.Column(db.Integer,db.ForeignKey('user.id'))

@app.route('/')
def hello_world():
    return render_template('layout.html')

@app.route('/login',methods = ["GET","POST"])
def login():
    if request.method=='POST':
        username = request.form['name']
        password = request.form['psword']
        user = User.query.filter_by(username = username).first()
        if user and user.password == password:
            allProducts = Product.query.all()
            return render_template('index.html',user = user,allProducts=allProducts)
        else:
            flash("Incorrect Username or Password")
            return redirect("/login")
    return render_template('login.html')

@app.route('/register',methods = ['GET','POST'])
def register():
    if request.method=='POST':
        username = request.form['name']
        password = request.form['psword']
        confirm = request.form['repeatPassword']
        #print(username)
        if username and password and confirm:
            if password == confirm :
                person = User(username = username,password= confirm)
                print(person)
                db.session.add(person)
                db.session.commit()
                return redirect('/login')
            else:
                flash('Confirm passowrd properly')
                return redirect('/register')
        else:
            flash('All credentials are required')
            return redirect('/register')
    return render_template('register.html')

@app.route('/index/<int:id>')
def index(id):
    user = User.query.filter_by(id =id).first()
    allProducts = Product.query.all()
    return render_template('index.html',user = user,allProducts=allProducts)

@app.route('/profile/<int:id>',methods = ['GET','POST'])
def profile(id):
    if request.method == 'POST':
        title = request.form['title']
        desc = request.form['desc']
        if 'file' not in request.files:
            flash('No file part')
        file = request.files['img']
        if file.filename == '':
            flash('No image selected for uploading')
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            flash('Image successfully uploaded')
        else:
            flash('Allowed image types are - png, jpg, jpeg, gif')
        if title and desc:
            person = User.query.filter_by(id = id).first()
            product = Product(ptitle = title,pdesc = desc, pimg= filename, owner=person)
            db.session.add(product)
            db.session.commit()
        else:
            flash('All parameters are required')
        person = User.query.filter_by(id = product.owner_id).first()
        return render_template('profile.html',user = person)
    person = User.query.filter_by(id=id).first()
    return render_template('profile.html',user = person)

@app.route('/display/<filename>')
def display_image(filename):
    #print('display_image filename: ' + filename)
    return redirect(url_for('static', filename='uploads/' + filename), code=301)

@app.route('/logout')
def logout():
    return render_template('layout.html')

@app.route('/bid/<int:pid>/<int:uid>',methods = ['POST','GET'])
def bid(pid,uid):
    if request.method == 'POST':
        bidCall = request.form['bidamount']
        product = Product.query.filter_by(id = pid).first()
        user = User.query.filter_by(id = uid).first()
        if bidCall:
            if not product.hbid:
                product.hbid = bidCall
                product.bidby = user.username
                db.session.add(product)
                db.session.commit()
            elif bidCall > product.hbid:
                product.hbid = bidCall
                product.bidby = user.username
                db.session.add(product)
                db.session.commit()
        allProducts = Product.query.all()
        return render_template('index.html',user = user,allProducts=allProducts)

    user = User.query.filter_by(id = uid).first()
    allProducts = Product.query.all()
    return render_template('index.html',user = user,allProducts=allProducts)

@app.route('/delete/<int:id>')
def delete(id):
    product = Product.query.filter_by(id = id).first()
    productOwnerId = product.owner_id
    db.session.delete(product)
    db.session.commit()
    user = User.query.filter_by(id = productOwnerId).first()
    return render_template('profile.html',user = user)

@app.route('/edit/<int:id>',methods=['GET','POST'])
def edit(id):
    if request.method == 'POST':
        product = Product.query.filter_by(id = id).first()
        title = request.form['title']
        desc = request.form['desc']
        file = request.files['img']
        if file.filename:
            if allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                product.pimg = filename
                flash('Image successfully uploaded')
            else:
                flash('Allowed image types are - png, jpg, jpeg, gif')
        if title and desc:
            product.ptitle = title
            product.pdesc = desc
            db.session.add(product)
            db.session.commit()
            person = User.query.filter_by(id = product.owner_id).first()
            return render_template('profile.html',user = person)
        else:
            flash('All parameters are required')
    product = Product.query.filter_by(id = id).first()
    person = User.query.filter_by(id = product.owner_id).first()
    return render_template('edit.html',product = product,user=person)

if __name__ == "__main__":
    app.run(debug=True)