import locale
import os
import json
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
    with open(data_path, "w") as f:
        json.dump(data, f)
    return tpl_env.get_template("edit.html").render(
        tournaments=make_tournaments(data["tournaments"])
    )


def application(environ, start_response):
    body = ""
    method = environ.get("REQUEST_METHOD")
    if method == "GET":
        body = get()
    elif method == "POST":
        body = post(json.loads(environ.get("wsgi.input").read()))
    status = "200 OK"
    headers = [("Content-type", "text/html")]
    start_response(status, headers)
    return [body.encode()]
