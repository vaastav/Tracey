from flask import Flask, request
import json
import sys

api = Flask(__name__)

@api.route("/summary", methods=['GET'])
def summary():
    query = request.args.get("query")
    print(query)
    return json.dumps({"error": "Not Implemented"})

def main():
    if len(sys.argv) != 2:
        print("Usage: python tracy.py <config_file>")
        sys.exit(1)
    config_file = sys.argv[1]
    with open(config_file, 'r+') as inf:
        config = json.load(inf)
        print(config)
    api.run(host=config["host"], port=config["port"])

if __name__ == '__main__':
    main()
