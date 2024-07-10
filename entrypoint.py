# import the flask web framework
import json
import redis as redis
from flask import Flask, request,jsonify
from loguru import logger

HISTORY_LENGTH = 10
DATA_KEY = "engine_temperature"

# create a Flask server, and allow us to interact with it using the app variable
app = Flask(__name__)


# define an endpoint which accepts POST requests, and is reachable from the /record endpoint
@app.route('/record', methods=['POST'])
def record_engine_temperature():
    # every time the /record endpoint is called, the code in this block is executed

    try:
        payload = request.get_json(force=True)
        logger.info(f"(*) record request --- {json.dumps(payload)} (*)")

        engine_temperature = payload.get("engine_temperature")
        if engine_temperature is None:
            return jsonify({"error": "Missing engine_temperature in payload"}), 400

        logger.info(f"engine temperature to record is: {engine_temperature}")

        try:
            database = redis.Redis(host="redis", port=6379, db=0, decode_responses=True)
            database.lpush(DATA_KEY, float(engine_temperature))
            logger.info(f"stashed engine temperature in redis: {engine_temperature}")

            while database.llen(DATA_KEY) > HISTORY_LENGTH:
                database.rpop(DATA_KEY)
            engine_temperature_values = database.lrange(DATA_KEY, 0, -1)
            logger.info(f"engine temperature list now contains these values: {engine_temperature_values}")
        except redis.RedisError as e:
            logger.error(f"Redis error: {str(e)}")
            return jsonify({"error": "Database error"}), 500

        logger.info("record request successful")
        return jsonify({"success": True}), 200

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

# practically identical to the above
@app.route('/collect', methods=['GET'])
def collect_engine_temperature():
    try:
        database = redis.Redis(host="redis", port=6379, db=0, decode_responses=True)
        current_engine_temperature = database.rpop(DATA_KEY)
        engine_temperature_values = database.lrange(DATA_KEY, 0, -1)
        sum_engine_temperature_values = 0.0
        if len(engine_temperature_values):
            for i in engine_temperature_values:
                sum_engine_temperature_values = sum_engine_temperature_values + float(i)
                average_engine_temperature = sum_engine_temperature_values/len(engine_temperature_values)
            return {"current_engine_temperature": current_engine_temperature,
                "average_engine_temperature": average_engine_temperature}
        else:
            return jsonify({"error": "no engine temperature values found"})
    except redis.RedisError as e:
        logger.error(f"Redis error: {str(e)}")
        return jsonify({"error": "Database error"}), 500