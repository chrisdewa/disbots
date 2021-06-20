from datetime import datetime

import motor.motor_asyncio


client = motor.motor_asyncio.AsyncIOMotorClient()

db = client.reminders



"""
document = {
    "user_id"
    "channel_id"
    "datetime"
    "finished"
    "every"
}

"""