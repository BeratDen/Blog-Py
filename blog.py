from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps

# region Dekaratörler
# kullanıcı giriş decorator'ı


def login_required(f):
    @wraps(f)
    def decated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Lütfen giriş yapınız...", "danger")
            return redirect(url_for("login"))
    return decated_function

# endregion

# region Formlar

# Kullanıcı Kayıt Formu


class RegisterForm(Form):
    name = StringField("İsim Soyisim : ", validators=[
                       validators.length(min=4, max=25, message="İsminiz en az 4 enfazla 25 karakterden oluşmalıdır...")])

    user_name = StringField("Kullanıcı Adınız : ", validators=[
        validators.length(min=5, max=35)])

    email = StringField("Email Adresi : ", validators=[
        validators.Email(message="Lütfen Geçerli Bir Email Adresi Girin..."), validators.DataRequired(message="Email Zorunlu Bir Alandır...")])

    password = PasswordField("Parola : ", validators=[validators.DataRequired(
        message="Lütfen Bir Parola Belirleyiniz..."), validators.EqualTo(fieldname="confirm", message="Parolanız Uyuşmuyor...")])

    confirm = PasswordField("Parola Tekrarı : ")

# login formu


class LoginForm(Form):
    user_name = StringField("Kullanıcı adı :")
    password = PasswordField("Şifreniz:")

# makele formu


class ArticleForm(Form):
    title = StringField("Makale Başlığı", validators=[
                        validators.length(min=5, max=100)])
    content = TextAreaField("Makale İçeriği", validators=[
                            validators.length(min=10)])

# endregion


app = Flask(__name__)

app.secret_key = "ybblog"

app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = "Courseapp_123"
app.config["MYSQL_DB"] = "ybblog"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

mysql = MySQL(app)


@app.route("/")
def index():

    numbers = [1, 2, 3, 4, 5]

    articles = [

        {'id': 1, 'tiltle': 'Deneme1', "content": "Deneme1 içerik"},
        {'id': 2, 'tiltle': 'Deneme2', "content": "Deneme2 içerik"},
        {'id': 3, 'tiltle': 'Deneme3', "content": "Deneme3 içerik"},
        {'id': 4, 'tiltle': 'Deneme4', "content": "Deneme4 içerik"},
        {'id': 5, 'tiltle': 'Deneme5', "content": "Deneme5 içerik"},

    ]

    return render_template("index.html", islem=1, numbers=numbers, articles=articles)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/dashboard")
@login_required
def dashboard():
    cursor = mysql.connection.cursor()
    sorgu = "SELECT * FROM articles WHERE author = %s"
    result = cursor.execute(sorgu, (session['user_name'],))
    if result > 0:
        articles = cursor.fetchall()
        return render_template("dashboard.html", articles=articles)
    return render_template("dashboard.html")


@app.route("/articles")
def articles():

    cursor = mysql.connection.cursor()

    sorgu = "SELECT * FROM articles"

    result = cursor.execute(sorgu)

    if result > 0:
        articles = cursor.fetchall()
        return render_template("articles.html", articles=articles)
    else:
        return render_template("articles.html")


@app.route("/articles/<string:id>")
def articleDetail(id):
    cursor = mysql.connection.cursor()

    sorgu = "SELECT * FROM articles WHERE id = %s"

    result = cursor.execute(sorgu, (id,))

    if result > 0:
        article = cursor.fetchone()
        return render_template("articledetail.django.html", article=article)
    else:
        return render_template("articledetail.django.html")


@app.route("/addarticle", methods=["GET", "POST"])
@login_required
def addArticle():
    form = ArticleForm(request.form)
    if request.form and form.validate():
        title = form.title.data
        content = form.content.data

        cursor = mysql.connection.cursor()
        sorgu = "INSERT INTO articles(title,author,content) VALUES(%s,%s,%s)"
        cursor.execute(sorgu, (title, session['user_name'], content))

        mysql.connection.commit()

        cursor.close()
        flash("Makale Başarıyla Eklendi", "success")
        return redirect(url_for("dashboard"))

    return render_template("addarticle.django.html", form=form)


@app.route("/article/edit/<string:id>", methods=["GET", "POST"])
@login_required
def editArticle(id):
    if request.method == "GET":
        cursor = mysql.connection.cursor()
        sorgu = "Select * From articles Where id = %s and author = %s"
        result = cursor.execute(sorgu, (id, session['user_name']))
        if result == 0:
            flash("Böyle bir makale yok veya bu makaleye erişimin yok.", "danger")
            return redirect(url_for("dashboard"))
        else:
            article = cursor.fetchone()
            form = ArticleForm()
            form.title.data = article["title"]
            form.content.data = article["content"]
            return render_template("editarticle.django.html", form=form)
    else:
        cursor = mysql.connection.cursor()
        form = ArticleForm(request.form)

        newTitle = form.title.data
        newContent = form.content.data

        sorgu = "UPDATE articles SET title = %s, content = %s Where id = %s"
        result = cursor.execute(sorgu, (newTitle, newContent, id))
        if result > 0:
            mysql.connection.commit()
            cursor.close()
            flash("Makale güncellendi.", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Makale güncellenirken bir hata oluştu", "danger")
            return redirect(url_for("dashboard"))


@app.route("/article/delete/<string:id>")
@login_required
def deleteArticle(id):
    cursor = mysql.connection.cursor()
    sorgu = "SELECT * FROM articles WHERE id=%s AND author=%s"
    result = cursor.execute(sorgu, (id, session['user_name']))

    if result > 0:
        sorgu2 = "DELETE FROM articles WHERE id=%s AND author=%s"
        result2 = cursor.execute(sorgu2, (id, session['user_name']))

        if result2 > 0:
            mysql.connection.commit()
            cursor.close()

            flash("Makale silindi.", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Makale silinemedi", "danger")
            return redirect(url_for("dashboard"))
    else:
        flash("Böyle bir makale bulunamadı", "danger")
        return redirect(url_for("dashboard"))


@app.route("/login", methods=["GET", "POST"])
def login():

    form = LoginForm(request.form)

    if request.method == "POST":

        user_name = form.user_name.data
        entered_password = form.password.data

        cursor = mysql.connection.cursor()
        sorgu = "Select * From users where user_name = %s"

        result = cursor.execute(sorgu, (user_name,))

        if result > 0:
            data = cursor.fetchone()
            real_password = data["password"]
            if sha256_crypt.verify(entered_password, real_password):
                flash("Giriş Yapıldı", "success")

                session["logged_in"] = True
                session["user_name"] = user_name

                return redirect(url_for("index"))
            else:
                flash("Şifre yanlış...", "danger")
                return redirect(url_for("login"))
        else:
            flash("Kullanıcı bulunamadı...", "danger")
            return redirect(url_for("login"))

    else:
        return render_template("login.html", form=form)


@app.route("/search", methods=["GET", "POST"])
def search():
    if request.method == "GET":
        return redirect(url_for("articles"))
    else:
        q = request.form.get("q")
        cursor = mysql.connection.cursor()
        sorgu = "Select * From articles where title Like '%"+q+"%'"
        result = cursor.execute(sorgu)
        if result == 0:
            flash("Aranana kelime ile makale bulunmadı...", "warning")
            return redirect(url_for("articles"))
        else:
            articles = cursor.fetchall()
            return render_template("articles.html", articles=articles)


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm(request.form)

    if request.method == "POST" and form.validate():

        name = form.name.data
        user_name = form.user_name.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data)

        cursor = mysql.connection.cursor()
        sorgu = "Insert Into users(name,user_name,email,password) Values(%s,%s,%s,%s)"

        cursor.execute(sorgu, (name, user_name, email, password))

        mysql.connection.commit()

        cursor.close()

        flash("Başarıyla Kayıt Oldunuz...", "success")

        return redirect(url_for("login"))
    else:
        return render_template("register.html", form=form)


@app.route("/logout")
def logout():
    session.clear()
    flash("Çıkış yapıldı...", "success")
    return redirect(url_for("index"))

# Makale Ekleme


if __name__ == "__main__":
    app.run(debug=True)
