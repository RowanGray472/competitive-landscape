from flask import Flask, request, render_template, redirect, url_for
from openai import OpenAI
from dotenv import load_dotenv
import os
import requests
import json
import re

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ORG_ID = os.getenv("ORG_ID")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        TARGET_COMPANY = request.form.get("target_company")
        TARGET_URL = request.form.get("target_url")

        if not TARGET_COMPANY or not TARGET_URL:
            return render_template("index.html", error="Please enter both company name and URL")

        # Call OpenAI
        try:
            client = OpenAI(api_key=OPENAI_API_KEY, organization=ORG_ID)
            response = client.responses.create(
                model="o3-pro",
                reasoning={"effort": "high"},
                input=f"""
  **ROLE**

You are a business researcher

**TASK**

Your task is to generate a competitive landscape for a specific software company. To do this, you should first carefully determine what sector that company sells into and what sort of software they make, and then find as many companies that make software for a sector of the economy as you can. Your list should only include companies that make software specifically for that sector. Do not include companies that serve sectors other than the specified sector. 

First, visit the URL of the specified company to make sure you target the right sector.

Try to make your list as exhaustive as possible within that sector. You should aim for at least 30 companies.

Ensure all the companies you find are 'real' companies. Remember, they must be Software as a Service companies that focus on making software for a specific sector.

Focus on companies founded after 2010 who have raised less than 50M in funding, but include major companies outside of these bands.

Only look at companies headquartered in the United States.

Fill out this blank template for each company

Company Name:

**EXAMPLES**

Here are a few examples of well-done lists for specific sectors.

**FORMAT**

Format your response as a python list of company names.

Do not include any other text besides the list.

Do not  include any text in the list besides the names of the companies.

**EXCEPTIONS**

Do not ever cite or research using IBIS World

**INPUT**

Your company is: {TARGET_COMPANY}: {TARGET_URL}
"""
            )
            response_text = response.output[1].content[0].text

            # Extract company list
            companies = []
            match = re.search(r'\[(.*?)\]', response_text, re.DOTALL)
            if match:
                companies_text = match.group(1)
                companies = re.findall(r'["\']([^"\']+)["\']', companies_text)
            else:
                companies = [
                    line.strip().strip('"\'')
                    for line in response_text.strip().split('\n')
                    if line.strip() and not line.startswith("[") and not line.startswith("]")
                ]

            # Send to webhook
            webhook_results = []
            for competitor in companies:
                data = {
                    "source_company": TARGET_COMPANY,
                    "source_url": TARGET_URL,
                    "competitor_company": competitor,
                }
                try:
                    r = requests.post(
                        WEBHOOK_URL,
                        data=json.dumps(data),
                        headers={"Content-Type": "application/json"},
                    )
                    webhook_results.append(f"✓ {competitor}: Status {r.status_code}")
                except Exception as e:
                    webhook_results.append(f"✗ {competitor}: Error - {str(e)}")

            return render_template(
                "results.html",
                TARGET_COMPANY=TARGET_COMPANY,
                TARGET_URL=TARGET_URL,
                companies=companies,
                webhook_results=webhook_results
            )

        except Exception as e:
            return render_template("index.html", error=f"Processing error: {e}")

    return render_template("index.html")
if __name__ == "__main__":
    app.run(debug=True)

