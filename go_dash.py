import os
import dash_html_components as html
from dash import dcc
import pandas as pd
import dash
from dash import Dash, dash_table
from threading import Timer
import webbrowser
from goatools import obo_parser
import wget
import dash_bootstrap_components as dbc



def fetch_data(data_folder):
    if (not os.path.isfile(data_folder)):
        # Emulate mkdir -p (no error if folder exists)
        try:
            os.mkdir(data_folder)
        except OSError as e:
            if (e.errno != 17):
                raise e
    else:
        raise Exception('Data path (' + data_folder + ') exists as a file. '
                                                      'Please rename, remove or change the desired location of the data path.')

    # Check if the file exists already
    if (not os.path.isfile(data_folder + '/go-basic.obo')):
        print("download data  !!!")
        go_obo = wget.download(go_obo_url, data_folder + '/go-basic.obo')
    go_obo = data_folder + '/go-basic.obo'
    print("-"*100)
    print("obo raw data is available !!!")

    return go_obo


def transitive_closure(go_term, go):
    go_term_set = set()
    find_parents(go_term, go, go_term_set)
    find_children(go_term, go, go_term_set)
    return go_term_set


def find_parents(term1, go, go_term_set={}, ret=False):
    for term2 in term1.parents:
        go_term_set.update({term2})
        # Recurse on term to find all parents
        find_parents(term2, go, go_term_set)
    if (ret):
        return go_term_set


def find_children(term1, go, go_term_set={}, ret=False):
    for term2 in term1.children:
        go_term_set.update({term2})

        # Recurse on term to find all children
        find_children(term2, go, go_term_set)
    if (ret):
        return go_term_set

def add_tag(df_input,
            column,
            debug=False,
            ):
    l = []
    for x in df_input[column]:
        if x == "id:":
            l.append("1")
        else:
            l.append("2")
    df_input["tag"] = l
    df_output = df_input[df_input["tag"] == "1"]
    if debug:
        print("quality check") # counts should be equal
        print(len(df_output))
        print(df_output["Term"].nunique())
    print("-" * 100)
    print("Adding tag is done !!!")
    return df_output
def curate_ontology_data(path):
    # Reading data in TXT
    obo_data = pd.read_csv(path,
                           on_bad_lines='skip',
                           sep=" ")
    obo_data = obo_data.rename(columns={'[Term]': 'Term'})
    obo_data = obo_data[obo_data["Term"].astype(str).str.contains("GO")]
    obo_data = obo_data.reset_index(drop=False)
    obo_data = obo_data.rename(columns={"index": "id"})
    print("-" * 100)
    print("Curated ontology step was done !")
    return obo_data

def extract_edges(df_input):
    appended_data = []
    go_id_l = df_input["Term"].unique()
    for go_id_input in go_id_l:
        try:
            go_term = go[go_id_input]
            rec = go[go_id_input]
            parents = rec.get_all_parents()
            children = rec.get_all_children()
            id_list = []
            names_list = []
            depth_list = []
            level_list = []
            obsolete_go_terms = []
            for term in parents.union(children):
                t = go[term]
                # adding id
                go_id = t.id
                id_list.append(go_id)
                # addding the names
                name = t.name
                names_list.append(name)
                # adding the deptj
                depth = t.depth
                depth_list.append(depth)
                # adding level
                level = t.level
                level_list.append(level)
                # creating DataFrame
            go_pd = pd.DataFrame(list(zip(id_list, level_list, depth_list, names_list)),
                                          columns=["go_id", "level", "depth", "names"])
            # filtering down
            go_pd = go_pd[go_pd["depth"] >= 2]
            # adding the go_id
            go_pd["input_go_id"] = go_id_input
            # filling list
            appended_data.append(go_pd)

        # except KeyError as e:
        except KeyError:
            obsolete_go_terms.append(go_id_input)
            pass
    appended_data = pd.concat(appended_data)

    # saving final curated dataset
    print("-" * 50)
    print("Checking data ...")
    if (not os.path.isfile(data_folder + '/obo_data_curated_07_10.csv')):
        print("CSV DATA IS NOT THERE ")
        print("-" * 100)
        appended_data.to_csv(data_folder + "/obo_data_curated_07_10.csv", index=False)
    print("CSV DATA IS IS available, reading it ... ")
    print("-" * 100)
    go_pd = pd.read_csv(data_folder + "/obo_data_curated_07_10.csv")
    print("-" * 100)
    print("Pandas data format is  done !")
    return go_pd


def render_app(input_data):
    FONT_AWESOME = external_stylesheets = [{
        'href': 'https://use.fontawesome.com/releases/v5.8.1/css/all.css',
        'rel': 'stylesheet',
        'integrity': 'sha384-50oBUHEmvpQ+1lW4y57PTFmhCaXp0ML5d60M1M7uH2+nqUivzIebhndOJK28anvf',
        'crossorigin': 'anonymous'
    }]

    external_stylesheets = [dbc.themes.BOOTSTRAP, FONT_AWESOME]

    # defining the app
    external_stylesheets = [dbc.themes.BOOTSTRAP, FONT_AWESOME]
    app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

    # defining LayOut
    app.layout = dbc.Container([
        dcc.Interval(id='interval1', interval=5 * 1000, n_intervals=0),
        html.H1(id='label1', children=''),

        dash_table.DataTable(
            columns=[
                {'name': 'INPUT_GO_ID', 'id': 'input_go_id', 'type': 'text'},
                {'name': 'GO_ID', 'id': 'go_id', 'type': 'text'},
                {'name': 'LEVEL', 'id': 'level', 'type': 'numeric'},
                {'name': 'DEPTH', 'id': 'depth', 'type': 'numeric'},
                {'name': 'NAMES', 'id': 'names', 'type': 'text'}

            ],

            data = input_data.to_dict('records'),

            filter_action='native',

            style_table={'height': 400},

            style_data={'width': '150px',
                        'minWidth': '150px',
                        'maxWidth': '150px',
                        'overflow': 'hidden',
                        'textOverflow': 'ellipsis',
                        # 'border':'1px solid blue'},
                        'border': '1px solid black'},

            style_data_conditional=[{'if': {'filter_query': '{depth} > 3'},
                                     'backgroundColor': '#3D9970',
                                     'color': 'white'}],

            style_header={'border': '3px solid orange',
                          'backgroundColor': 'rgb(230, 230, 230)',
                          'fontWeight': 'bold',
                          'textAlign': 'center'},

            style_cell_conditional=[
                {'if': {'column_id': c},
                 'textAlign': 'center'
                 } for c in ['depth', 'level']],

            page_size=10

        ),  # Close Table


    ],  # close container
        className='m-4'
    )


    return  app


def open_browser():
    """
    https://stackoverflow.com/questions/71697716/how-to-automatically-open-a-website-when-launching-the-dash
    https://stackoverflow.com/questions/9449101/how-to-stop-flask-from-initialising-twice-in-debug-mode

    :return:
    """
    if not os.environ.get("WERKZEUG_RUN_MAIN"):
        webbrowser.open_new('http://127.0.0.1:1222/')



if __name__ == "__main__":
    go_obo_url = 'http://purl.obolibrary.org/obo/go/go-basic.obo'
    data_folder = os.getcwd() + '/data'


    go_obo = fetch_data(data_folder = data_folder)

    obo_data_raw = curate_ontology_data(path="data/obo-basic.csv")

    obo_data_raw = add_tag(df_input = obo_data_raw,
                           column = "id",
                           debug = True)

    go = obo_parser.GODag(go_obo)

    df = extract_edges(df_input = obo_data_raw)

    app = render_app(input_data= df)
    Timer(1, open_browser).start()
    app.run_server(debug=False,
                   port=1222)



