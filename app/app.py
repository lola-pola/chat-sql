
from langchain import SQLDatabase, SQLDatabaseChain
from langchain.llms import AzureOpenAI
from langchain.agents import create_sql_agent
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from langchain.sql_database import SQLDatabase
from langchain.agents import initialize_agent
from langchain.agents import AgentExecutor
from langchain.llms.openai import OpenAI
from langchain.agents import load_tools
from langchain.agents import AgentType
from streamlit_chat import message
import streamlit as st
import os
import pandas as pd
import pymysql


st.session_state['generated'] = []
st.session_state['past'] = []
# Define Streamlit app
def app():
    chat , db, openai ,graph = st.tabs(["chat","database configuration", "openai","graph"])
    db_conigured = False
    openai_conigured = False
    with db:
     mysql_connection_string = None
     st.header("database configuration")
     checkbox = st.selectbox("database type", ["sql lite", "mysql"], key="database_type")
     if checkbox == "sql lite":
         _sqlite = st.file_uploader("Upload your sqlite file", type=["db", "sqlite", "sql"])
         if _sqlite:
                 with open('data/'+_sqlite.name, "wb") as f:
                     f.write(_sqlite.getbuffer())
                 mysql_connection_string = "sqlite:///data/"+_sqlite.name
         else:
             mysql_connection_string = "sqlite:///chinook.db"
     elif checkbox == "mysql":
            mysql_connection_string = st.text_input("mysql connection string", key="mysql_connection_string")
     if st.checkbox("Submit", key="db"):
            st.success("Submitted!")
            db_conigured = True

    with openai:
       st.header("openai configuration")
       context = st.text_area("Add Context Here", height=100, key="add context here", value="")
       max_tokens = st.slider("Max tokens", value=1000, key="max_tokens")
       temperature = st.slider("Temperature", max_value=1.0 ,min_value=0.0 ,value=1.0, key="temperature")
       engine = st.text_input("Engine", "text-davinci-002", key="engine")
       # Set up OpenAI API key
       os.environ["OPENAI_API_TYPE"] = "azure"
       os.environ["OPENAI_API_BASE"] = st.text_input("API base", value='https://xxx.openai.azure.com/', key="api_base")
       os.environ["OPENAI_API_VERSION"] = st.text_input("api version",value="2022-12-01")
       os.environ["OPENAI_API_KEY"] = st.text_input('azure openai key', key="KEY_AZURE_AI", value='xxxxxx', type="password") 
       if st.checkbox("Submit", key="openai"):
           st.success("Submitted!")
           openai_conigured = True
           
    with chat:
       st.header("start ask your data bases questions")

       if mysql_connection_string:
           db = SQLDatabase.from_uri(mysql_connection_string)
           if checkbox == "mysql":
              toolkit = SQLDatabaseToolkit(db=db)
              

              
   
   
           llm = AzureOpenAI(temperature=temperature ,
                           verbose=True,
                           deployment_name=engine,                       
                           max_tokens=max_tokens)
           if checkbox == "mysql":
            agent_executor = create_sql_agent(llm=llm,toolkit=toolkit,verbose=True)
           else: 
            db_chain = SQLDatabaseChain.from_llm(llm, db, verbose=True,top_k=3)
   
   
   
   
   
           if 'generated' not in st.session_state:
               st.session_state['generated'] = []
           if 'past' not in st.session_state:
               st.session_state['past'] = []
               
               
           st.write("Welcome to the chatbot")
           user_input=st.text_input("You:",key='input')
   
           if user_input:
               print(context + user_input)
               if checkbox == "mysql":
                output=agent_executor.run(context + user_input)
               else:
                output=db_chain.run(context + user_input)
               st.session_state['past'].append(user_input)
               st.session_state['generated'].append(output)
               if st.session_state['generated']:
                   for i in range(len(st.session_state['generated'])-1, -1, -1):
                       message(st.session_state["generated"][i], key=str(i))
                       message(st.session_state['past'][i], is_user=True, key=str(i) + '_user') 
                       st.session_state.generated = ''
       else:
        st.write("please configure your database and openai first")
    with graph:
       if mysql_connection_string:
           db = SQLDatabase.from_uri(mysql_connection_string)
   
   
   
           llm = AzureOpenAI(temperature=temperature ,
                           verbose=True,
                           deployment_name=engine,                       
                           max_tokens=max_tokens)
   
           db_chain = SQLDatabaseChain.from_llm(llm, db, verbose=True,top_k=10)        

           user_input = st.text_input("You:",key='input1')
           if user_input:
            context = '''
    
            query requires creating a line chart, reply as follows:
            line chart data for streamlit st.line_chart
            Below is the query.
                Query: + ''' + user_input +'''
                return answer only as pandas dataframe
                '''
            
            tools = load_tools([], llm=llm)

            agent = initialize_agent(tools, llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, verbose=True)
            

            _context = agent.run(context)

                
            output=db_chain.run(_context)
            st.code(output)



def main():
    app()
if __name__ == '__main__':
    main()