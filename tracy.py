from flask import Flask, request
import json
import sys
from mysql.connector import Error, connect

api = Flask(__name__)
connection = {}

@api.route("/summary", methods=['GET'])
def summary():
    query = request.args.get("query")
    print(query)
    return json.dumps({"error": "Not Implemented"})

def main():
    global connection
    if len(sys.argv) != 2:
        print("Usage: python tracy.py <config_file>")
        sys.exit(1)
    config_file = sys.argv[1]
    with open(config_file, 'r+') as inf:
        config = json.load(inf)
        db_host = config["db_host"]
        database = config["db"]
        user = config["username"]
        password = config["pwd"]
        try:
            connection = connect(host=db_host, database=database, user=user, password=password)
            if connection.is_connected():
                print("Connected to MySQL server")
        except Error as e:
            print("Error while connecting to database", e)
            sys.exit(1)
    api.run(host=config["host"], port=config["port"])

if __name__ == '__main__':
    main()
