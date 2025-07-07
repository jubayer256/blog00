from datetime import datetime
from flask import Flask, render_template, request, redirect, session
import time

import db
from hashids import Hashids

app = Flask(__name__)
app.secret_key = "12345abcde67890"

@app.route("/")
def home():
    return redirect("/posts")


@app.template_filter()
def timestamp_to_datetime(s):
    dt = datetime.fromtimestamp(int(s))
    return dt.strftime("%b %d, %Y  %I:%M %p")


@app.template_filter()
def timestamp_to_date(s):
    dt = datetime.fromtimestamp(int(s))
    return dt.strftime("%b %d, %Y")


@app.route("/posts")
def posts():
    args = request.args.to_dict()
    data = db.get_approved_posts(args)
    return render_template("posts.html", categories=db.get_categories(), posts=data)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if session:
        return redirect("/")
    if request.method == "POST":
        data = request.form.to_dict()
        name = data["fullname"]
        username = data["username"]
        email = data["email"]
        password = data["password"]
        gender = data["gender"]
        role = "Member"
        created = int(time.time())

        check = db.check_if_user_exists(email, username)
        if check:
            return check

        db.insert_user(name, username, email, password, gender, role, created)
        return redirect("/login")

    return render_template("signup.html")


@app.route("/logout")
def logout():
    if session:
        session.clear()
    return redirect("/login")


@app.route("/login", methods=["GET", "POST"])
def login():
    if session:
        return redirect("/")
    if request.method == "POST":
        data = request.form.to_dict()
        email_or_username = data["email_or_username"]
        password = data["password"]
        resp = db.login(email_or_username, password)
        if not resp:
            return "Login failed"
        else:
            session["name"] = resp[0]
            session["username"] = resp[1]
            session["email"] = resp[2]
            session["admin"] = True if resp[3] == "Admin" else False
        return redirect("/posts")
    return render_template("login.html")


@app.route("/create", methods=["GET", "POST"])
def create_post():
    if not session:
        return redirect("/login")
    if request.method == "POST":
        data = request.form.to_dict()
        title = data["title"]
        category = data["category"]
        content = data["content"].replace('"', '“')
        file = request.files["image"]

        file_ext = file.filename.split(".")[-1]
        h = Hashids(min_length=10, salt="zaqmlp42517")
        last_id = db.table_last_id()
        filename = h.encode(last_id+1) + "." + file_ext
        file.save("static/img/post/{}".format(filename))

        db.insert_post(title, content, filename, session["username"], category, "Pending")
        return redirect("/posts")
    return render_template("create.html", categories=db.get_categories())


@app.route("/post/<int:postID>")
def view_post(postID):
    db.add_visit_to_post(postID)
    data = db.get_post_data(postID)
    comments = db.get_comments_of_post(postID)
    return render_template("single-post.html", data=data, comments=comments)


@app.route("/add_comment/<int:postID>", methods=["POST"])
def add_comment(postID):
    if not session:
        return redirect("/")
    comment_text = request.form.to_dict()["comment_text"].replace('"', '“')
    username = session["username"]
    created = time.time()

    db.add_comment_to_post(postID, username, comment_text, created)
    return redirect("/post/{}".format(postID))


@app.route("/delete_comment/<int:postID>/<int:commentID>", methods=["POST"])
def delete_comment(postID, commentID):
    if not session:
        return redirect("/")
    db.delete_comment(postID, commentID)
    return redirect("/post/{}".format(postID))


#################### Admin Panel ############################
def check_admin():
    if session:
        if session["admin"]:
            return True
        return False
    return False


@app.route("/admin")
def admin():
    if check_admin():
        data = db.get_posts()
        return render_template("/admin/admin-posts.html", data=data)
    return redirect("/")


@app.route("/admin/post/<post_id>/<action>")
def post_action(post_id, action):
    if check_admin():
        db.post_action(post_id, action)
    return redirect("/admin")


@app.route("/admin/post/delete/<post_id>")
def admin_delete_post(post_id):
    if check_admin():
        db.admin_delete_post(post_id)
        return redirect("/admin")
    return redirect("/")


@app.route("/admin/users")
def admin_users():
    if check_admin():
        return render_template("admin/admin-users.html", users=db.get_all_users())
    return redirect("/")


######################### profile ##################################
@app.route("/profile")
def profile():
    if not session:
        return redirect("/login")
    user_data = db.get_logged_in_user()
    user_posts = db.get_logged_in_user_posts()
    return render_template("profile.html", user=user_data, posts=user_posts)


@app.route("/edit-post/<post_id>", methods=["GET", "POST"])
def edit_post(post_id):
    if not session:
        return redirect("/login")
    if request.method == "POST":
        data = request.form.to_dict()
        title = data["title"]
        cat = data["category"]
        content = data["content"].replace('"', '“')
        image = request.files["image"]
        if image:
            filename = db.get_post_image_filename(post_id)
            image.save(f"static/img/post/{filename}")

        db.edit_post(post_id, title, cat, content)
        return redirect("/profile")

    post = db.get_post_data(post_id)
    categories = db.get_categories()
    return render_template("edit-post.html", categories=categories, post=post)


@app.route("/delete_own_post/<post_id>")
def delete_own_post(post_id):
    if not session:
        return redirect("/")
    db.delete_own_post(post_id)
    return redirect("/profile")


@app.route("/update_profile", methods=["POST"])
def update_profile():
    if not session:
        return redirect("/")
    data = request.form.to_dict()
    name = data["fullname"]
    username = data["username"]
    email = data["email"]
    gender = data["gender"]

    check = db.check_if_user_exists_while_update(email, username)
    if check:
        return check
    db.update_profile(name, email, username, gender)
    return redirect("/profile")

