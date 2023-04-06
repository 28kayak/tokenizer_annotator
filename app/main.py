import streamlit as st
import pandas as pd
import psycopg2
import os
import syslog
# Annotation Options
OPTIONS = ["Ipaidc", "Unidic", "Both Incorrect", "Both Correct"]
state = st.session_state

def get_connection():
    #postgresConnection = psycopg2.connect("dbname=labelling user=admin password='admin'")
    postgresConnection = psycopg2.connect("postgresql://admin:admin@db:5432/labelling")
    return postgresConnection

def get_total_rows():
    conn = get_connection()
    cur = conn.cursor()
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) AS total_rows FROM annotation_queue_1 where status = false;")
        total_rows = cur.fetchone()
    #conn.close
    return total_rows[0]    

def get_completed_rows():
    conn = get_connection()
    cur = conn.cursor()
    with conn.cursor():
        cur.execute("SELECT COUNT(*) AS completed_rows FROM annotation_queue_1 where status = ture;")
        completed_rows = cur.fetchone()
    return completed_rows[0]
        


def insert_result(id, label):
    conn = get_connection()
    cur = conn.cursor()

    with conn.cursor() as cur:
        cur.execute("UPDATE annotation_queue_1 SET result = '{}' WHERE id = {};".format(label, id))
        syslog.syslog("{}, {} have been updated".format(id, label))
    conn.commit()
    #conn.close()

# run when OPTION is clicked
# update data frame and insert DB
# argument label contains the reulst of clicked option
def annotate(label, id):
    st.write('annotating')
    st.write(label, id)
    insert_result(id=id, label=label)
   


def pop(nrows):
    # read first 10 row from db
    # SQL: SELECT * FROM your_table_name LIMIT 5;
    conn = get_connection()
    cur = conn.cursor()

    with conn.cursor() as cur:
        cur.execute('SELECT * FROM annotation_queue_1 WHERE status = false LIMIT 10;')
        # convert data type as Panda's Dataframe
        df = pd.DataFrame(cur.fetchall(), columns=[col.name for col in cur.description])
        retreived = df['id'].to_list()
        # make retreaved rows as annotated (True)  
        #cur.execute("SELECT * FROM data WHERE id = ANY(%s);", (yourList,))
        cur.execute("UPDATE annotation_queue_1 SET status = true WHERE id = ANY(%s);", (retreived,))
        conn.commit()
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

# Truncate Data and Reset AutoIncrement
def clean_db():
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("DELETE FROM annotation_queue_1;")
        cur.execute("ALTER SEQUENCE annotation_queue_1_id_seq RESTART;")
    conn.commit()
    

# === MAIN  ===
st.title("Tokenizer Annotation")

if st.button('Inset Data to DB'):
    # TODO: DB のクリーンナップ
    clean_db()
    all_data = read_tsv('./data/books_2023-01-15.tsv')
    bluk_import_from_df(all_data, 'annotation_queue_1')
else:
    st.write('data is inserted')

if st.button('clean Data'):
    clean_db()


if "annotations" not in state:
    state.annotations = {}
    state.candidates = pd.DataFrame()
    state.index = 0
    state.candidates = pop(10)
rows = get_total_rows()
st.write(f"{rows} rows in DB")
percent_complete=0
progress_text = "Progress"
progerss_bar = st.progress(0, text=progress_text)

with st.expander('Will Annotate the Following Data'):
    st.dataframe(state.candidates.head(10))
#st.write(state.candidates.empty)
if state.index < 10 and not state.candidates.empty:
    # display terms
    #state.candidates.replace(to_replace =' ', value = '_', regex = True)
    st.dataframe(state.candidates[['id', 'ipadic', 'unidic', 'result', 'is_same']].loc[state.index].replace(to_replace =' ', value = '_', regex = True), use_container_width=True)
    #st.write(state.candidates.loc[state.index])
    # display options and call annotate on clicking
    c = st.columns(len(OPTIONS))
    for idx, option in enumerate(OPTIONS):
        c[idx].button(f"{option}", on_click=annotate, args=(option, state.candidates['id'].loc[state.index] ))
    # increment index
    st.write(state.index)
    state.index = state.index + 1 
else:
   st.info('Press C + R to go on Next Set', icon="ℹ️")
   progerss_bar.progress(percent_complete + 10, text=progress_text)
