from flask import Flask, request
import json

api = Flask(__name__)

@api.route("/summary", methods=['GET'])
def summary():
    query = request.args.get("query")
    print(query)
    return json.dumps({"error": "Not Implemented"})

def main():
    api.run()

if __name__ == '__main__':
    main()
