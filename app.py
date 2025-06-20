from flask import Flask, request, render_template, redirect, url_for
from openai import OpenAI
from dotenv import load_dotenv
import os
import requests
import json
import re
import ast

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ORG_ID = os.getenv("ORG_ID")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
client = OpenAI(api_key=OPENAI_API_KEY, organization=ORG_ID)


app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        TARGET_COMPANY = request.form.get("target_company")
        TARGET_URL = request.form.get("target_url")
        NOTES = request.form.get("notes")
        CATEGORIES = request.form.get("categories")

        # Try to convert string to list if needed
        if isinstance(CATEGORIES, str) and CATEGORIES.strip().startswith("["):
            try:
                CATEGORIES = json.loads(CATEGORIES)
            except json.JSONDecodeError:
                return render_template("index.html", error="Categories field looks like a list but is not valid JSON.")

        # Validate it's now a list or empty
        if not isinstance(CATEGORIES, list) and CATEGORIES != "":
            return render_template("index.html", error="Incorrectly formatted categories, please reformat.")



        if not TARGET_COMPANY or not TARGET_URL:
            return render_template("index.html", error="Please enter both company name and URL")

        try:
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

Do not include any text in the list besides the names of the companies.

**EXCEPTIONS**

Do not ever cite or research using IBIS World

**INPUT**

Your company is: {TARGET_COMPANY}: {TARGET_URL}

Additional notes: {NOTES}
""",
                timeout=1800
            )
        except Exception as e:
            print(f"OpenAI request failed: {e}")
            return render_template("index.html", error="The request to OpenAI failed or timed out. Please try again later.")
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

        # Create a JSON array with company names and descriptions

        companies_with_descriptions = []
        for company in companies:
            response = client.responses.create(
                model="gpt-4.1",
                input=f"Write a brief description of what this company, {company}, does. Do not provide any other text other than the description."
            )
            
            companies_with_descriptions.append({
                "name": company,
                "description": response.output_text.strip()
            })
            
        if CATEGORIES == "":
            response = client.responses.create(
                    model="gpt-4.1",
                    input=f"""
                    Given this list of company names and descriptions {companies_with_descriptions}, generate 3-5 buckets based on company functionality. Format the output as a json array containing the names and descriptions of each category, along with a list of the companies in the category.

                    Here's an exmple of a well-done bucketing. Follow this formatting exactly. Do not include any additional text besides the json array.

                    [
        {{
            "name": "Comprehensive Property Management Platforms",
            "description": "Companies offering all-in-one solutions for property management, typically including accounting, leasing, maintenance, communication, rent collection, and reporting, suitable for residential, multifamily, and/or commercial real estate.",
            "companies": [
                "AppFolio",
                "Buildium",
                "Entrata",
                "ResMan",
                "Yardi Systems",
                "RealPage",
                "Rent Manager",
                "Rentvine",
                "DoorLoop",
                "ManageCasa"
            ]
        }},
        {{
            "name": "Landlord & Small Portfolio Management Tools",
            "description": "Platforms focused on independent landlords or small-to-medium property managers, providing streamlined tools for rent collection, lease management, tenant screening, and maintenance tracking.",
            "companies": [
                "TenantCloud",
                "Avail",
                "Hemlane",
                "Rentec Direct",
                "TurboTenant",
                "RentRedi",
                "Innago",
                "Azibo",
                "Rentroom"
            ]
        }},
        {{
            "name": "Specialized Leasing & CRM Solutions",
            "description": "Companies specializing in lead management, leasing automation, tenant communications, and multifamily CRM functionalities rather than full property management.",
            "companies": [
                "Funnel Leasing",
                "Knock CRM",
                "VTS"
            ]
        }},
        {{
            "name": "Maintenance, Operations, & Inspections",
            "description": "Companies focusing on maintenance coordination, inspections, resident engagement, and streamlining property operations, often complementing broader management software.",
            "companies": [
                "Property Meld",
                "Latchel",
                "HappyCo",
                "SightPlan",
                "Building Engines"
            ]
        }},
        {{
            "name": "Other Specialized Real Estate Tech",
            "description": "Companies with a specialized focus beyond core property management, such as smart home automation or insurance for real estate and gig economy purposes.",
            "companies": [
                "SmartRent",
                "Zego"
            ]
        }}
    ]
                    """
                )


        else:
            response = client.responses.create(
                    model="gpt-4.1",
                    input=f"""
                    Given this list of company names and descriptions {companies_with_descriptions} and this list of buckets {CATEGORIES}, put each company in a bucket. Format your output like this example. Do not include any additional text.

                     [
        {{
            "name": "Comprehensive Property Management Platforms",
            "description": "Companies offering all-in-one solutions for property management, typically including accounting, leasing, maintenance, communication, rent collection, and reporting, suitable for residential, multifamily, and/or commercial real estate.",
            "companies": [
                "AppFolio",
                "Buildium",
                "Entrata",
                "ResMan",
                "Yardi Systems",
                "RealPage",
                "Rent Manager",
                "Rentvine",
                "DoorLoop",
                "ManageCasa"
            ]
        }},
        {{
            "name": "Landlord & Small Portfolio Management Tools",
            "description": "Platforms focused on independent landlords or small-to-medium property managers, providing streamlined tools for rent collection, lease management, tenant screening, and maintenance tracking.",
            "companies": [
                "TenantCloud",
                "Avail",
                "Hemlane",
                "Rentec Direct",
                "TurboTenant",
                "RentRedi",
                "Innago",
                "Azibo",
                "Rentroom"
            ]
        }},
        {{
            "name": "Specialized Leasing & CRM Solutions",
            "description": "Companies specializing in lead management, leasing automation, tenant communications, and multifamily CRM functionalities rather than full property management.",
            "companies": [
                "Funnel Leasing",
                "Knock CRM",
                "VTS"
            ]
        }},
        {{
            "name": "Maintenance, Operations, & Inspections",
            "description": "Companies focusing on maintenance coordination, inspections, resident engagement, and streamlining property operations, often complementing broader management software.",
            "companies": [
                "Property Meld",
                "Latchel",
                "HappyCo",
                "SightPlan",
                "Building Engines"
            ]
        }},
        {{
            "name": "Other Specialized Real Estate Tech",
            "description": "Companies with a specialized focus beyond core property management, such as smart home automation or insurance for real estate and gig economy purposes.",
            "companies": [
                "SmartRent",
                "Zego"
            ]
        }}
    ]

                    """
                )
            # Convert to JSON string
        companies_json = json.dumps(companies_with_descriptions, indent=2)

        # Get the bucketing result from response
        try:
            bucketing = json.loads(response.output[0].content[0].text)
        except json.JSONDecodeError:
            bucketing = []

        # Create a mapping of company names to their categories
        company_to_bucket_map = {}
        for bucket in bucketing:
            bucket_name = bucket.get("name", "Uncategorized")
            bucket_description = bucket.get("description", "")
            for company_name in bucket.get("companies", []):
                company_to_bucket_map[company_name] = {
                    "bucket_name": bucket_name,
                    "bucket_description": bucket_description
                }
        company_names = [company["name"] for company in companies_with_descriptions]

        # Send to webhook
        webhook_results = []
        for company_data in companies_with_descriptions:
            company_name = company_data["name"]
            bucket_info = company_to_bucket_map.get(company_name, {"bucket_name": "Uncategorized", "bucket_description": ""})
            
            data = {
                "source_company": TARGET_COMPANY,
                "source_url": TARGET_URL,
                "competitor_company": company_name,
                "competitor_description": company_data["description"],
                "bucket_name": bucket_info["bucket_name"],
                "bucket_description": bucket_info["bucket_description"]
            }
            
            try:
                r = requests.post(
                    WEBHOOK_URL,
                    json=data,
                    headers={"Content-Type": "application/json"},
                )
                webhook_results.append(f"✓ {company_name}: Status {r.status_code}")
            except Exception as e:
                webhook_results.append(f"✗ {company_name}: Error - {str(e)}")

        return render_template(
            "results.html",
            TARGET_COMPANY=TARGET_COMPANY,
            TARGET_URL=TARGET_URL,
            companies=company_names,
            companies_json=companies_json,
            bucketing=bucketing,
            webhook_results=webhook_results
        )
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
