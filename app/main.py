import streamlit as st
import pandas as pd
import psycopg2
import os

# Annotation Options
OPTIONS = ["Ipaidc", "Unidic", "Both Incorrect"]
state = st.session_state

def get_connection():
    #postgresConnection = psycopg2.connect("dbname=labelling user=admin password='admin'")
    postgresConnection = psycopg2.connect("postgresql://admin:admin@db:5432/labelling")
    return postgresConnection

def get_total_rows():
    conn = get_connection()
    cur = conn.cursor()
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) AS total_rows FROM annotation_queue_1;")
        total_rows = cur.fetchone()
    #conn.close
    return total_rows[0]    

def insert_result(id, label):
    conn = get_connection()
    cur = conn.cursor()

    with conn.cursor() as cur:
        cur.execute("UPDATE annotation_queue_1 SET result = '{}' WHERE id = {};".format(label, id))
    conn.commit()
    #conn.close()

# run when OPTION is clicked
# update data frame and insert DB
# argument label contains the reulst of clicked option
def annotate(label, id):
    insert_result(id=id, label=label)
    st.write(label)


def pop(nrows):
    # read first 10 row from db
    # SQL: SELECT * FROM your_table_name LIMIT 5;
    conn = get_connection()
    cur = conn.cursor()

    with conn.cursor() as cur:
        cur.execute('SELECT * FROM annotation_queue_1 WHERE status = false LIMIT 5;')
        # convert data type as Panda's Dataframe
        df = pd.DataFrame(cur.fetchall(), columns=[col.name for col in cur.description])
        # make retreaved rows as annotated (True) 
        cur.execute("UPDATE annotation_queue_1 SET status = TRUE FROM (SELECT * FROM annotation_queue_1 WHERE status = false LIMIT 5) poped;")
        conn.commit()
    #conn.close
    return df

def bluk_import_from_df(dataframe, destination_table_name ):
    conn = get_connection()
    query = f"""
        INSERT INTO {destination_table_name} ({", ".join(dataframe.columns)})
        VALUES {", ".join(["(" + ", ".join(["%s"] * len(dataframe.columns)) + ")"] * len(dataframe))}
        """
    with conn.cursor() as cur:
        cur.execute(query, dataframe.values.flatten())
    conn.commit()

def read_tsv(file_path):
    all_data = pd.read_table(file_path, usecols=['rank','frequency','byte_size','script','raw_query','ipadic','unidic','is_same'])
    # set status to be false 
    all_data['status'] = 'false'
    st.write(all_data.head(5))
    return all_data
    

# === MAIN  ===

st.title("Tokenizer Annotation")
if st.button('Inset Data to DB'):
    # TODO: DB のクリーンナップ
    all_data = read_tsv('./data/books_2023-01-15.tsv')
    bluk_import_from_df(all_data, 'annotation_queue_1')
else:
    st.write('data is inserted')

if "annotations" not in state:
    state.annotations = {}
    state.candidates = pd.DataFrame()
    state.index = 0
rows = get_total_rows()
st.write(f"{rows} rows in DB")

state.candidates = pop(10)
percent_complete=0
progress_text = "Progress"
progerss_bar = st.progress(0, text=progress_text)

#st.write(state.index)
#st.dataframe(state.candidates)
if state.index < 10 and state.candidates is not None:
    # display terms
    st.dataframe(state.candidates.loc[state.index], use_container_width=True)
    #st.write(state.candidates.loc[state.index])
    # display options and call annotate on clicking
    c = st.columns(len(OPTIONS))
    for idx, option in enumerate(OPTIONS):
        c[idx].button(f"{option}", on_click=annotate, args=(option, state.candidates['id'].loc[state.index] ))
    progerss_bar.progress(percent_complete + 1, text=progress_text)

else:
    st.write('iteration is done')



