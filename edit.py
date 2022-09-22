import locale
import os
import json
import sass
import jinja2
from dictknife import deepmerge

locale.setlocale(locale.LC_CTYPE, ("en_US", "UTF-8"))
docroot = os.path.dirname(__file__)
data_path = os.path.join(docroot, "data.json")
tpl_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.join(docroot, "res/templates"))
)


def make_tournaments(tournaments):
    with open(os.path.join(docroot, "res/tournaments_base.json")) as f:
        tournaments_base = json.load(f)
    for t, matches in tournaments.items():
        _matches = {}
        for bm in tournaments_base["tournaments"][t]["matches"]:
            if matches.get(bm):
                _matches.update({bm: matches.get(bm)})
        matches = _matches
        for m, p in matches.items():
            if p == [0, 0]:
                continue
            try:
                base_m = tournaments_base["tournaments"][t]["matches"][m]
                winner = base_m["team{}".format(p.index(max(p)))]
                loser = base_m["team{}".format(p.index(min(p)))]
                update = deepmerge(
                    base_m["update"][p.index(max(p))], base_m["update"][2]
                )
                tournaments_base["tournaments"][t] = deepmerge(
                    tournaments_base["tournaments"][t],
                    json.loads(
                        json.dumps(update)
                        .replace("{point0}", str(p[0]))
                        .replace("{point1}", str(p[1]))
                        .replace("{winner}", winner)
                        .replace("{loser}", loser)
                    ),
                )
                base_m["point0"] = p[0]
                base_m["point1"] = p[1]
            except Exception:
                pass
    return tournaments_base["tournaments"]


def get():
    data = {"tournaments": {}, "yt_list": []}
    if os.path.exists(data_path):
        with open(data_path) as f:
            data = json.load(f)
    return tpl_env.get_template("edit.html").render(
        tournaments=make_tournaments(data["tournaments"])
    )


def post(postdata):
    data = {"tournaments": {}, "yt_list": []}
    if os.path.exists(data_path):
        with open(data_path) as f:
            data = json.load(f)
    yt_list = [s for s in data["yt_list"] if s]
    for t, tournament in postdata["tournaments"].items():
        for m, p in tournament.items():
            if t not in data["tournaments"]:
                data["tournaments"][t] = {}
            data["tournaments"][t][m] = p
    generated = tpl_env.get_template("main.html").render(
        ids=yt_list,
        tournaments=make_tournaments(data["tournaments"]),
    )
    with open(os.path.join(docroot, "index.html"), "w") as f:
        f.write(generated)
    sass.compile(
        dirname=(os.path.join(docroot, "res/scss"), os.path.join(docroot, "css")),
        output_style="compressed",
    )
    with open(data_path, "w") as f:
        json.dump(data, f)
    return tpl_env.get_template("edit_inner.html").render(
        tournaments=make_tournaments(data["tournaments"])
    )


def get_yt():
    data = {"tournaments": {}, "yt_list": []}
    if os.path.exists(data_path):
        with open(data_path) as f:
            data = json.load(f)
    return tpl_env.get_template("edit_yt.html").render(
        yt_list="\n".join(data["yt_list"])
    )


def post_yt(postdata):
    data = {"tournaments": {}, "yt_list": []}
    if os.path.exists(data_path):
        with open(data_path) as f:
            data = json.load(f)
    data["yt_list"] = [s for s in postdata if s]
    with open(data_path, "w") as f:
        json.dump(data, f)
    generated = tpl_env.get_template("main.html").render(
        ids=data["yt_list"],
        tournaments=make_tournaments(data["tournaments"]),
    )
    with open(os.path.join(docroot, "index.html"), "w") as f:
        f.write(generated)
    return


def application(environ, start_response):
    status = "200 OK"
    headers = [("Content-type", "text/html")]
    body = ""
    method = environ.get("REQUEST_METHOD")
    query = environ.get("QUERY_STRING").split("&")
    if "key=" + environ.get("EDIT_KEY") not in query:
        status = "403 Forbidden"
        body = "<!DOCTYPE HTML PUBLIC \"-//IETF//DTD HTML 2.0//EN\"><html><head><title>403 Forbidden</title></head><body><h1>Forbidden</h1><p>You don't have permission to access this resource.</p><hr>{}</body></html>".format(environ.get("SERVER_SIGNATURE"))
    elif method == "GET":
        if "s=yt" in query:
            body = get_yt()
        else:
            body = get()
    elif method == "POST":
        postdata = json.loads(environ.get("wsgi.input").read())
        if "s=yt" in query:
            body = post_yt(postdata)
        else:
            body = post(postdata)
    start_response(status, headers)
    return [body.encode()]
