from fastapi import FastAPI
from pydantic import BaseModel
import random
import os
import glob
import pandas as pd
from twilio.rest import Client
import google.generativeai as genai
# from dotenv import load_dotenv

# load_dotenv()

app = FastAPI(title="smaple_data_api")

# ==================================================
# DATA FOLDER
# ==================================================

DATA_DIR = "sample_data"

# ==================================================
# 🤖 GEMINI CONFIG (HARD CODED)
# ==================================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel("gemini-2.5-flash")

# ==================================================
# 🔐 TWILIO CONFIG (HARD-CODED FOR DEMO)
# ==================================================

TWILIO_SID = "ACb823febe2a526e9fb32a8f3ea278ebb1"
TWILIO_AUTH = "68ff32dbbf64c2efa5be6dab5f050d28"
TWILIO_WHATSAPP_FROM = "whatsapp:+14155238886"   # Twilio sandbox number
ALERT_PHONE = "whatsapp:+918639216174"           # YOUR WhatsApp number

twilio_client = Client(TWILIO_SID, TWILIO_AUTH)

# ==================================================
# 🚨 DEMO ABNORMAL METERS
# ==================================================

ABNORMAL_METERS = ["A0", "C1", "B3"]

# ==================================================
# REQUEST MODEL
# ==================================================

class MeterRequest(BaseModel):
    zone: str
    floor: int

# ==================================================
# WHATSAPP ALERT
# ==================================================

def send_whatsapp_alert(meter_id, power, water):
    msg = (
        "🚨 Alert 🚨\n\n"
        f"Abnormal usage detected!\n\n"
        f"Meter: {meter_id}\n"
        f"Electricity: {power} kWh\n"
        f"Water: {water} LPH\n\n"
        "Immediate inspection is recommended."
    )

    twilio_client.messages.create(
        from_=TWILIO_WHATSAPP_FROM,
        to=ALERT_PHONE,
        body=msg
    )

# ==================================================
# MAIN ENDPOINT
# ==================================================

@app.post("/get_values")
def get_readings(req: MeterRequest):

    meter_id = f"{req.zone.upper()}{req.floor}"

    # ---------------- ALERT CASE ----------------
    if meter_id in ABNORMAL_METERS:

        electricity = round(random.uniform(4.5, 6.0), 2)
        water = random.randint(85, 120)

        try:
            send_whatsapp_alert(meter_id, electricity, water)
        except Exception as e:
            print("WhatsApp failed:", e)

        return {
            "meter_id": meter_id,
            "electricity_used": electricity,
            "water_used": water,
            "status": "ALERT"
        }

    # ---------------- NORMAL CASE ----------------
    electricity = round(random.uniform(1.0, 3.5), 2)
    water = random.randint(15, 60)

    return {
        "meter_id": meter_id,
        "electricity_used": electricity,
        "water_used": water,
        "status": "NORMAL"
    }

# ==================================================
# GET — AI INSIGHTS USING GEMINI
# ==================================================

@app.get("/get_insights")
def get_ai_insights():

    # # -------- Load all CSVs --------
    # files = glob.glob(os.path.join(DATA_DIR, "*.csv"))

    # if not files:
    #     return {"error": "No data files found"}

    # dfs = [pd.read_csv(f, parse_dates=["timestamp"]) for f in files]
    # data = pd.concat(dfs, ignore_index=True)

    # data["date"] = pd.to_datetime(data["timestamp"]).dt.date
    # today = data["date"].max()
    # today_df = data[data["date"] == today]

    # -------- Summaries --------

    # top_power = (
    #     today_df.groupby("meter_id")["electricity_kwh"]
    #     .mean().sort_values(ascending=False)
    #     .head(3).index.tolist()
    # )

    # top_water = (
    #     today_df[today_df["water_lph"] > 0]
    #     .groupby("meter_id")["water_lph"]
    #     .mean().sort_values(ascending=False)
    #     .head(3).index.tolist()
    # )

    top_power = ["C1", "E0", "D0"]
    top_water = ["C1", "A0", "A2"]    

    # avg_power = round(today_df["electricity_kwh"].mean(), 2)
    # avg_water = round(today_df[today_df["water_lph"] > 0]["water_lph"].mean(), 2)

    avg_power = 2.38
    avg_water = 38.94

    alerts = []
    for m in ABNORMAL_METERS:
        if m in top_power or m in top_water:
            alerts.append(f"Abnormal usage detected at {m}")

    alerts_text = "\n".join(alerts) if alerts else "No critical alerts detected."

    # -------- Prompt for Gemini --------

    print(top_power, top_water, avg_power, avg_water)

    prompt = f"""
You are a sustainability and facility management assistant for a college campus.

Today's campus resource summary:

Top electricity usage meters: {top_power}
Top water usage meters: {top_water}

Average electricity per meter: {avg_power} kWh
Average water usage per meter: {avg_water} LPH

Alerts:
{alerts_text}

Provide:
1. Possible reasons for abnormal usage
2. Practical corrective actions
3. Sustainability benefits

Keep response short and actionable.
"""

    try:
        response = gemini_model.generate_content(prompt)
        insights = response.text
    except Exception as e:
        insights = f"Gemini API error: {str(e)}"

    return {
        "date": str(today),
        "top_power_zones": top_power,
        "top_water_zones": top_water,
        "avg_water": avg_water,
        "avg_power": avg_power,
        "ai_insights": insights
    }




