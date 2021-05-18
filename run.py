from flask import Flask, request, render_template, make_response, url_for, redirect, flash, session, jsonify
# from foo.utils.CaptchaUtils import cg
from foo.conf.config import DEBUG
from foo.service.admin.Section import section_dict

import os
import json
import logging
import foo.client.MongoClient as MongoClient
import foo.service.admin.Login as admin_login
import foo.service.admin.Stage as admin_stage
import foo.service.admin.User as admin_user
import foo.service.admin.Logger as admin_log
import foo.service.user.Login as user_login
import foo.service.user.Register as user_register
import foo.service.user.Stage as user_stage
import foo.utils.StageUtils as Stage

LOGGER = logging.getLevelName("run")
MONGO_CLIENT = MongoClient.MongoClient()
# ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
app = Flask(__name__, static_url_path='/static')
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['BABEL_DEFAULT_LOCALE'] = 'zh_Hans_CN'
app.secret_key = os.urandom(24)
app.debug = DEBUG


@app.route('/')
def index():
    return render_template('index.html', section_dict=section_dict)


@app.route('/<section>/')
def board(section):
    page = int(request.args.get('page', 1))
    page_size = 10
    # MONGO_CLIENT.set_col('section')
    # section_desc = MONGO_CLIENT.get_col().find_one({"code": int(section)}, {"name": 1})["name"]
    if section == "time":
        section_desc = "时间线"
        topics, page_has_next, page_num = Stage.get_topics_with_time(is_admin=True if session.get(
            "pet") is not None else False,
                                                                     page_size=page_size,
                                                                     page_no=page)
    else:
        section_desc = section_dict.get(int(section)).get("name")
        MONGO_CLIENT.set_col('stage')
        topics, page_has_next, page_num = Stage.get_topics_with_time(int(section),
                                                                     is_admin=True if session.get(
                                                                         "pet") is not None else False,
                                                                     page_size=page_size,
                                                                     page_no=page)
    page_dict = {"page": page,
                 "page_size": page_size,
                 "page_num": page_num,
                 "page_prev": max(1, page - 5),
                 "page_last": min(max(10, page + 5), page_num) + 1,
                 "has_prev": 1 if page_num > 0 and page != 1 else 0,
                 "has_next": 1 if page_has_next else 0}
    return render_template('board.html',
                           stages=topics,
                           board=section,
                           board_desc=section_desc,
                           history=0,
                           page_dict=page_dict,
                           section_dict=section_dict
                           )


@app.route('/<int:section>/post', methods=['POST'])
def post(section):
    name = request.cookies.get('uid')
    rev = None
    if name is not None:
        rev = user_stage.post(serial=request.cookies.get('serial'),
                              title=request.form.get('title'),
                              author=name,
                              content=request.form.get('content'),
                              section_code=section)
    else:
        pet = session.get('pet')
        if pet is not None:
            rev = admin_stage.post(admin=session.get('admin'),
                                   title=request.form.get('title'),
                                   author=pet,
                                   content=request.form.get('content'),
                                   section_code=section)
        else:
            flash("你还没有登录。", 'warning')
    if rev is not None:
        if isinstance(rev, Exception):
            flash(str(rev))
        elif rev:
            flash("发表成功。", 'success')
        else:
            flash("发生了预期之外的错误，请联系管理员。", 'error')
    return redirect(url_for('board', _external=True, section=section))


@app.route('/login/')
def login():
    link = str(request.args.get('link', "index"))
    args = eval(request.args.get('args', '{}'))
    url = url_for(link, _external=True, **args)
    return render_template('login.html', link=url)


@app.route('/logout/')
def logout():
    link = str(request.args.get('link', "index"))
    args = eval(request.args.get('args', '{}'))
    response = make_response(redirect(url_for(link, _external=True, **args)))
    response.delete_cookie("serial")
    response.delete_cookie("uid")
    return response


@app.route('/login/service', methods=['POST'])
def login_service():
    serial = request.form.get("serial")
    uid = user_login.login(serial)
    link = str(request.form.get("link", 'index'))
    args = eval(request.form.get("args", '{}'))
    if args is None:
        args = {}
    if uid is not None:
        response = make_response(redirect(url_for(link, _external=True, **args)))
        response.set_cookie("serial", serial)
        response.set_cookie("uid", uid)
        session.clear()
        flash("欢迎你，" + uid, "success")
        return response
    else:
        flash("序列号不存在。", 'warning')
        print(url_for('login', _external=True, link=link, args=args))
        return redirect(url_for('login', _external=True, link=link, args=args))


@app.route('/register/')
def register():
    uid, serial = user_register.get()
    user_register.register(uid, serial, request.remote_addr)
    link = str(request.args.get('link', "index"))
    args = eval(request.args.get('args', '{}'))
    response = make_response(redirect(url_for(link, _external=True, **args)))
    response.set_cookie("serial", serial)
    response.set_cookie("uid", uid)
    session.clear()
    flash("".join(["请妥善保管为你分配的唯一序列号：", serial, "。"]))
    return response


@app.route('/<section>/report/<stage>/', methods=['POST'])
def report4borad(section, stage):
    serial = request.cookies.get('serial')
    notes = str(request.form.get('notes'))
    rev = None
    if serial is not None:
        rev = Stage.report(stage, serial, notes)
    else:
        flash("你还没有登录。", 'warning')
    if rev is not None:
        if isinstance(rev, Exception):
            flash(str(rev), 'error')
        elif rev:
            flash("举报成功。", 'success')
        else:
            flash("发生了预期之外的错误，请联系管理员。", 'error')
    return redirect(url_for('board', _external=True, section=section, page=request.args.get('page', 1)))


@app.route('/reply/<prefix>/report/<stage>/', methods=['POST'])
def report4reply(prefix, stage):
    serial = request.cookies.get('serial')
    notes = request.form.get('notes')
    if notes is not None:
        notes = str(notes)
    rev = None
    if serial is not None:
        rev = Stage.report(stage, serial, notes)
    else:
        flash("你还没有登录。", 'warning')
    if rev is not None:
        if isinstance(rev, Exception):
            flash(str(rev), 'error')
        elif rev:
            flash("举报成功。", 'success')
        else:
            flash("发生了预期之外的错误，请联系管理员。", 'error')
    return redirect(url_for('reply', _external=True, stage=prefix, page=request.args.get('page', 1)))


@app.route('/reply/<stage>/')
def reply(stage):
    page = int(request.args.get('page', 1))
    page_size = 10
    MONGO_CLIENT.set_col('section')
    stage_value = Stage.get_with_time(stage, page_size=page_size, page_no=page,
                                      is_admin=True if session.get("pet") is not None else False, )
    if 'replies' in stage_value:
        replies = stage_value['replies']
    else:
        replies = Stage.get_reply(code=stage,
                                  is_admin=True if session.get("pet") is not None else False,
                                  page_size=page_size,
                                  page_no=page)
    if isinstance(replies, Exception):
        return str(replies)
    else:
        page_dict = {"total": replies.get("total"),
                     "page": page,
                     "page_size": page_size,
                     "page_num": replies.get("page_num"),
                     "page_prev": max(1, page - 5),
                     "page_last": min(max(10, page + 5), replies.get("page_num")) + 1,
                     "has_prev": 1 if replies.get("page_num") > 0 and page != 1 else 0,
                     "has_next": 1 if replies.get("page_has_next") else 0}
        return render_template('reply.html',
                               stage=stage_value,
                               replies=replies["data"],
                               page_dict=page_dict,
                               section_dict=section_dict)


@app.route('/post_reply/<prefix>', methods=['POST'])
def post_reply(prefix):
    name = request.cookies.get('uid')
    rev = None
    if name is not None:
        rev = user_stage.reply(serial=request.cookies.get('serial'),
                               title=request.form.get('title'),
                               author=name,
                               content=request.form.get('content'),
                               prefix=prefix)
    else:
        pet = session.get("pet")
        if pet is not None:
            rev = admin_stage.reply(admin=session.get("admin"),
                                    title=request.form.get('title'),
                                    author=pet,
                                    content=request.form.get('content'),
                                    prefix=prefix)
        else:
            flash("你还没有登录。", 'warning')
    if rev is not None:
        if isinstance(rev, Exception):
            flash(str(rev))
        elif rev:
            flash("发表成功。", 'success')
        else:
            flash("发生了预期之外的错误，请联系管理员。", 'error')
    return redirect(url_for('reply', _external=True, stage=prefix))


@app.route('/admin/')
def admin():
    pet = session.get("pet")
    if pet is not None:
        return redirect('/')
    else:
        link = str(request.args.get('link', "index"))
        args = eval(request.args.get('args', '{}'))
        url = url_for(link, _external=True, **args)
        return render_template('admin.html', link=url)


@app.route('/admin/login', methods=['POST'])
def admin_login_service():
    name = request.form.get('admin')
    password = request.form.get('password')
    pet = admin_login.login(name, password)
    link = str(request.form.get("link", 'index'))
    args = eval(request.form.get("args", '{}'))
    if args is None:
        args = {}
    if pet is not None:
        session["pet"] = pet
        session["admin"] = name
        response = make_response(redirect(url_for(link, _external=True, **args)))
        response.delete_cookie("serial")
        response.delete_cookie("uid")
        flash("欢迎你，" + pet, "success")
        return response
    else:
        flash("用户名或密码错误。")
        return redirect(url_for('admin', _external=True, link=link, args=args))


@app.route('/admin/logout/')
def admin_logout():
    link = str(request.args.get('link', "index"))
    args = eval(request.args.get('args', '{}'))
    session.pop('pet')
    session.pop('admin')
    return redirect(url_for(link, _external=True, **args))


@app.route('/<section>/notes/<stage>/', methods=['POST'])
def notes4board(section, stage):
    pet = session.get('pet')
    notes = request.form.get('notes')
    if notes is None:
        flash("内容为空。", "warning")
    else:
        notes = str(notes)
        notes_prev = str(request.form.get('notes_prev'))
        if notes == notes_prev:
            flash("内容无更改。", "warning")
            return redirect(url_for('board', _external=True, section=section))
        rev = None
        if pet is not None:
            rev = admin_stage.note(stage, content=notes, operator=pet)
        else:
            flash("非法操作。", 'warning')
        if rev is not None:
            if isinstance(rev, Exception):
                flash(str(rev), 'error')
            elif rev:
                flash("备注成功。", 'success')
            else:
                flash("发生了预期之外的错误，请联系管理员。", 'error')
    return redirect(url_for('board', _external=True, section=section, page=request.args.get('page', 1)))


@app.route('/reply/<prefix>/notes/<stage>/', methods=['POST'])
def notes4reply(prefix, stage):
    pet = session.get('pet')
    notes = request.form.get('notes')
    if notes is None:
        flash("内容为空。", "warning")
    else:
        notes = str(notes)
        notes_prev = str(request.form.get('notes_prev'))
        if notes == notes_prev:
            flash("内容无更改。", "warning")
            return redirect(url_for('reply', _external=True, stage=prefix))
        rev = None
        if pet is not None:
            rev = admin_stage.note(stage, content=notes, operator=pet)
        else:
            flash("非法操作。", 'warning')
        if rev is not None:
            if isinstance(rev, Exception):
                flash(str(rev), 'error')
            elif rev:
                flash("备注成功。", 'success')
            else:
                flash("发生了预期之外的错误，请联系管理员。", 'error')
    return redirect(url_for('reply', _external=True, stage=prefix, page=request.args.get('page', 1)))


@app.route("/admin/<section_code>/<action>/<code>/")
def admin_action(section_code, action, code):
    pet = session.get('pet')
    if pet is not None:
        if action == 'delete':
            o_type = str(request.args.get('type'))
            if o_type == 'stage':
                o_section = int(request.args.get('section'))
                admin_stage.action(action, code, pet, is_cache_decr=True, section_code=o_section)
            else:
                admin_stage.action(action, code, pet)
        elif action == 'restore':
            o_type = str(request.args.get('type'))
            if o_type == 'stage':
                o_section = int(request.args.get('section'))
                admin_stage.action(action, code, pet, is_cache_incr=True, section_code=o_section)
            else:
                admin_stage.action(action, code, pet)
        else:
            admin_stage.action(action, code, pet)
    return redirect(url_for('board', _external=True, section=section_code, page=request.args.get('page', 1)))


@app.route("/admin/<section_code>/<action>/<code>/<prefix>/")
def admin_action_reply(section_code, action, code, prefix):
    pet = session.get('pet')
    if pet is not None:
        if action == 'delete':
            o_type = str(request.args.get('type'))
            if o_type == 'stage':
                o_section = int(request.args.get('section'))
                admin_stage.action(action, code, pet, is_cache_decr=True, section_code=o_section)
            else:
                admin_stage.action(action, code, pet)
        elif action == 'restore':
            o_type = str(request.args.get('type'))
            if o_type == 'stage':
                o_section = int(request.args.get('section'))
                admin_stage.action(action, code, pet, is_cache_incr=True, section_code=o_section)
            else:
                admin_stage.action(action, code, pet)
        else:
            admin_stage.action(action, code, pet)
    return redirect(url_for('reply', _external=True, stage=prefix, page=request.args.get('page', 1)))


@app.route("/admin_user_operator/<section>/<code>/<react>/<action>/<uid>/")
def admin_action_user(section, code, react, action, uid):
    pet = session.get('pet')
    if pet is None:
        return url_for("index")
    if react == "A":
        rev = admin_user.get_stages(uid, is_admin=True)
        board_desc = uid + "的历史发言记录"
        return render_template("board.html", stages=rev, board_desc=board_desc, history=1, section_dict=section_dict)
    else:
        rev = admin_user.action(uid, action, pet)
        if action == "search":
            if rev:
                board_desc = uid + "的历史发言记录"
                return render_template("board.html", stages=rev, board_desc=board_desc, history=1,
                                       section_dict=section_dict)
            else:
                flash("用户查询异常，请联系研发人员。")
                if react == "S":
                    return redirect(url_for('board', _external=True, section=section, page=request.args.get('page', 1)))
                elif react == "R":
                    return redirect(url_for('reply', _external=True, stage=code, page=request.args.get('page', 1)))
        else:
            if action == "delete":
                flash("已清退")
            elif action == "restore":
                flash("无罪释放")
            if react == "U":
                return redirect(
                    url_for('admin_action_user', section=section, code=code, react='U', action='search', uid=uid,
                            section_dict=section_dict, page=request.args.get('page', 1)))
            elif react == "S":
                return redirect(url_for('board', _external=True, section=section, page=request.args.get('page', 1)))
            elif react == "R":
                return redirect(url_for('reply', _external=True, stage=code, page=request.args.get('page', 1)))


@app.route('/admin/service/', methods=['GET', 'POST'])
def admin_service():
    if request.method == 'GET':
        link = str(request.args.get('link', "index"))
        args = eval(request.args.get('args', '{}'))
        url = url_for(link, _external=True, **args)
        reports = dict(
            zip(['data', 'has_next', 'page_num', 'total'], admin_log.get_report(reader=session.get('admin'))))
        reports['page_prev'] = 1
        reports['page'] = 1
        reports['page_last'] = min(max(10, 1 + 5), reports['page_num']) + 1
        admin_logger = dict(
            zip(['data', 'has_next', 'page_num', 'total'], admin_log.get_admin_log(reader=session.get('admin'))))
        admin_logger['page_prev'] = 1
        admin_logger['page'] = 1
        admin_logger['page_last'] = min(max(10, 1 + 5), admin_logger['page_num']) + 1
        return render_template('admin_service.html', report=reports, logger=admin_logger, link=url, page_size = 15)
    if request.method == 'POST':
        nify = {'code': 400, 'message': 'UnKnown Error'}
        data = request.form
        operator = data.get('operator', None)
        page_size = int(data.get('page_size', 15))
        page_no = int(data.get('page', 1))
        if data.get('type') == 'report':
            try:
                reports = dict(
                    zip(['data', 'has_next', 'page_num', 'total'],
                        admin_log.get_report(reader=session.get('admin'),
                                             operator=operator,
                                             page_size=page_size,
                                             page_no=page_no)))
                reports['page_prev'] = max(1, page_no - 5)
                reports['page'] = page_no
                reports['page_last'] = min(max(10, page_no + 5), reports['page_num']) + 1
                nify = {'code': 200, 'report': reports}
            except Exception as err:
                nify = {'code': 400, 'message': str(err)}
        if data.get('type') == 'admin':
            action = data.get('action', None)
            try:
                admin_logger = dict(
                    zip(['data', 'has_next', 'page_num', 'total'],
                        admin_log.get_admin_log(reader=session.get('admin'),
                                                operator=operator,
                                                action=action,
                                                page_size=page_size,
                                                page_no=page_no)))
                admin_logger['page_prev'] = max(1, page_no - 5)
                admin_logger['page'] = page_no
                admin_logger['page_last'] = min(max(10, page_no + 5), admin_logger['page_num']) + 1
                nify = {'code': 200, 'logger': admin_logger}
            except Exception as err:
                nify = {'code': 400, 'message': str(err)}
        return jsonify(nify)


@app.route('/admin/report/')
def admin_report():
    operator = str(request.args.get('operator'))
    object_ = str(request.args.get('object'))
    admin_log.delete_report_log(reader=session.get('admin'), operator=operator, object_str=object_)
    return """
    <body onload='setTimeout("mm()",0)'>
        <script>function mm(){ window.opener=null;
            window.close();} 
        </script>
    </body>
    """


@app.route('/search.html/')
def search():
    q = str(request.args.get('q'))
    rev = user_stage.search(q)
    board_desc = "关于  \"{}\" 的搜索结果".format(q)
    if isinstance(rev, Exception):
        flash(str(rev))
        return render_template("board.html", stages=[], board_desc=board_desc, history=1, section_dict=section_dict)
    return render_template("board.html", stages=rev, board_desc=board_desc, history=1, section_dict=section_dict)


# @app.route('/get_captcha', methods=['GET'])
# def get_captcha():
#     result = cg.generate()
#     session['captcha'] = cg.code.lower()
#     response = make_response(result)
#     response.headers["Content-type"] = "image/png"
#     return response
#
#
# @app.route('/captcha')
# def captcha():
#     return render_template('captcha.html')


# @app.route('/test')
# def test():
#     return time.asctime(time.localtime(time.time())).format("%Y-%m-%d %H:%M:%S")
#     return request.remote_addr


def main():
    app.run(host='0.0.0.0')


if __name__ == '__main__':
    main()