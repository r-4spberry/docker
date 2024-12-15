from flask import Flask, request
from flask_restx import Api, Resource, fields, reqparse
import os
from PyPDF2 import PdfReader
import torch
from PIL import Image
from pix2tex.cli import LatexOCR
import tempfile
from werkzeug.datastructures import FileStorage
from flask_cors import CORS
from latex_to_custom import latex_to_custom, custom_to_latex
from sympy.parsing.latex.errors import LaTeXParsingError
import sys
import time
import logging
from flask.logging import default_handler
from flask import (
    render_template_string,
    Response,
    request,
    make_response,
    render_template_string,
)
from functools import wraps
from dotenv import load_dotenv
import os
import yaml

with open("operations.yml", "r") as file:
    operations_config = yaml.safe_load(file)


from expressionChecker import ExpressionChecker

app = Flask(__name__)
CORS(app)

# Logging setup
file_handler = logging.FileHandler("app_logs.log")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
)

# Configure Flask's logger
app.logger.removeHandler(default_handler)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.DEBUG)

# Use Flask's logger for custom logs
logger = app.logger

TIMEOUT = 10000

api = Api(
    app,
    version="1.0",
    title="LaTeX API",
    description="An API for handling LaTeX comparisons and conversions",
)

ocr_model = LatexOCR()

ns = api.namespace("api", description="LaTeX operations")

file_upload_parser = reqparse.RequestParser()
file_upload_parser.add_argument(
    "file", type=FileStorage, location="files", required=True, help="File to upload"
)

# Define models for Swagger documentation
compare_model = api.model(
    "CompareModel",
    {
        "latex1": fields.String(required=True, description="First LaTeX string"),
        "latex2": fields.String(required=True, description="Second LaTeX string"),
    },
)


@ns.route("/compare")
class Compare(Resource):
    @api.expect(compare_model)
    def post(self):
        """Compare two LaTeX strings"""
        data = request.get_json()
        if not data or "latex1" not in data or "latex2" not in data:
            logger.error("Missing LaTeX strings in request.")
            return {"error": "Missing LaTeX strings"}, 400

        latex1 = data["latex1"]
        latex2 = data["latex2"]
        logger.info(f"Received comparison request: {latex1=} {latex2=}")

        try:
            # Transform latex to cutom grammar
            try:
                latex1_transformed = latex_to_custom(latex1)
                logger.debug(f"Transformed latex1: {latex1_transformed}")
            except (ValueError, LaTeXParsingError) as e:
                logger.warning(f"Error parsing latex1: {e}")
                return {"error": f"latex1: {str(e)}"}, 409

            try:
                latex2_transformed = latex_to_custom(latex2)
                logger.debug(f"Transformed latex2: {latex2_transformed}")
            except (ValueError, LaTeXParsingError) as e:
                logger.warning(f"Error parsing latex2: {e}")
                return {"error": f"latex2: {str(e)}"}, 409

        except Exception as e:
            logger.exception("Unexpected error during transformation.")
            return {"error": str(e)}, 500

        numIter = 1000
        timer_start = time.perf_counter_ns()

        ec = ExpressionChecker(latex1_transformed, latex2_transformed, True)
        logger.info("Initialized ExpressionChecker.")

        # Check custom grammar strings with ExpressionChecker
        try:
            run = ec.search(numIter)

            for result in run:
                [progress, similarity, new_1, new_2] = result
                logger.debug(
                    f"Iteration result: {progress=}, {similarity=}, {new_1=}, {new_2=}"
                )

                if progress == "n" or progress == "f":
                    logger.info("Search completed.")
                    break

                if timer_start + TIMEOUT * 1000000 < time.perf_counter_ns():
                    logger.warning("Search timed out.")
                    break

            new_latex1 = custom_to_latex(new_1.getGrammarStringRepr())
            new_latex2 = custom_to_latex(new_2.getGrammarStringRepr())
            logger.info(f"Final similarity: {similarity*100:.2f}%")
            logger.info(
                f"Time taken (s): {(time.perf_counter_ns() - timer_start) / 1000000000:.2f}"
            )
            return {
                "similarity": f"{similarity*100:.2f}%",
                "latex1": new_latex1,
                "latex2": new_latex2,
            }

        except Exception as e:
            logger.exception("Error during comparison execution.")
            return {"error": str(e)}, 500


# Load environment variables
load_dotenv()
USERNAME = os.getenv("LOGS_USERNAME", "admin")
PASSWORD = os.getenv("LOGS_PASSWORD", "secret")


# Authentication decorator
def requires_auth(username, password):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            auth = request.authorization
            if not auth or auth.username != username or auth.password != password:
                response = make_response("Unauthorized", 401)
                response.headers["WWW-Authenticate"] = 'Basic realm="Login Required"'
                return response
            return f(*args, **kwargs)

        return wrapper

    return decorator


@ns.route("/logs/pretty")
class PrettyLogs(Resource):
    def output_html(self, data, code, headers=None):
        """Helper to return HTML response."""
        resp = Response(data, mimetype="text/html", headers=headers)
        resp.status_code = code
        return resp

    @requires_auth(username=USERNAME, password=PASSWORD)
    def get(self):
        """Serve pretty logs as an HTML page with auto-refresh and authentication"""
        try:
            with open("app_logs.log", "r") as log_file:
                logs = []
                for line in log_file.readlines()[-100:]:  # Fetch last 100 lines
                    # Attempt to parse the log lines
                    parts = line.split(" - ", 2)
                    if len(parts) == 3:
                        timestamp, levelname, message = parts
                        logs.append(
                            {
                                "timestamp": timestamp.strip(),
                                "levelname": levelname.strip(),
                                "message": message.strip(),
                            }
                        )
                    else:
                        logs.append(
                            {
                                "timestamp": "Unknown",
                                "levelname": "unknown",
                                "message": line.strip(),
                            }
                        )
            response = render_template_string(
                """
                <!DOCTYPE html>
                <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <meta http-equiv="refresh" content="20">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Application Logs</title>
                    <style>
                        body { font-family: Arial, sans-serif; margin: 0; padding: 0; background-color: #f4f4f9; }
                        .log { padding: 10px; border-bottom: 1px solid #ddd; }
                        .info { background-color: #e8f5e9; color: #2e7d32; }
                        .debug { background-color: #e3f2fd; color: #0277bd; }
                        .warning { background-color: #fff3e0; color: #f57c00; }
                        .error, .critical { background-color: #ffebee; color: #c62828; }
                        header { padding: 20px; text-align: center; background: #6200ea; color: #fff; }
                    </style>
                </head>
                <body>
                    <header><h1>Application Logs</h1></header>
                    <div>
                        {% for line in logs %}
                        <div class="log {{ line.levelname|lower }}">
                            <strong>{{ line.timestamp }}</strong> - 
                            <span>{{ line.levelname }}</span>: 
                            {{ line.message }}
                        </div>
                        {% endfor %}
                    </div>
                </body>
                </html>
                """,
                logs=logs,
            )
            return self.output_html(response, 200)
        except Exception as e:
            logger.exception("Error rendering pretty logs.")
            return {"error": str(e)}, 500


@ns.route("/operations")
class Operations(Resource):
    def get(self):
        """List all supported LaTeX operations"""
        logger.info("Requested list of supported LaTeX operations.")
        return operations_config


# @ns.route("/pdf2latex")
# class PdfToLatex(Resource):
#     @api.expect(file_upload_parser)
#     def post(self):
#         """Extract LaTeX formulas from a PDF"""
#         args = file_upload_parser.parse_args()
#         file = args["file"]
#         if not file:
#             logger.error("No file provided for PDF to LaTeX conversion.")
#             return {"error": "No file provided"}, 400

#         with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
#             file.save(tmp_file.name)
#             file_path = tmp_file.name

#         logger.info(f"Saved uploaded PDF to temporary file: {file_path}")

#         try:
#             extracted_formulas = []
#             reader = PdfReader(file_path)
#             for page in reader.pages:
#                 text = page.extract_text()
#                 formulas = [line for line in text.splitlines() if "\\" in line]
#                 logger.debug(f"Extracted formulas from page: {formulas}")
#                 extracted_formulas.extend(formulas)
#         except Exception as e:
#             logger.exception("Error extracting formulas from PDF.")
#             os.remove(file_path)
#             return {"error": str(e)}, 500

#         os.remove(file_path)
#         logger.info("Temporary file removed.")
#         return {"formulas": extracted_formulas}


@ns.route("/pix2tex")
class PixToTex(Resource):
    @api.expect(file_upload_parser)
    def post(self):
        """Extract LaTeX formulas from an image"""
        args = file_upload_parser.parse_args()
        file = args["file"]
        if not file:
            logger.error("No file provided for image to LaTeX conversion.")
            return {"error": "No file provided"}, 400

        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
            file.save(tmp_file.name)
            file_path = tmp_file.name

        logger.info(f"Saved uploaded image to temporary file: {file_path}")

        try:
            image = Image.open(file_path).convert("RGB")
            latex_formula = ocr_model(image)
            logger.debug(f"Extracted LaTeX formula: {latex_formula}")

            try:
                converted = latex_to_custom(latex_formula)
                logger.debug(f"Converted formula to custom format: {converted}")
            except Exception as e:
                logger.warning(f"Error converting formula: {e}")
                os.remove(file_path)
                return {
                    "error": f"couldn't parse the string {latex_formula}, {str(e)}"
                }, 409

        except Exception as e:
            logger.exception("Error during image processing.")
            os.remove(file_path)
            return {"error": str(e)}, 500

        os.remove(file_path)
        logger.info("Temporary file removed.")
        return {"formulas": [latex_formula]}


if __name__ == "__main__":
    logger.info("Starting Flask application.")
    app.run(host="0.0.0.0", port=5000, debug=True)
