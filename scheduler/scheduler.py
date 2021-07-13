from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from ws.ws_server import ws_manager
from lib.firebase import pots_collection
from lib.custom_logger import logger
from validations.be2pot_schemas import MessageToPot, Action, PotSendDataDictBool, PotSendDataBool

async def daily_check_in_alert():
    all_pots = pots_collection.get()

    for pot in all_pots:
        pot_id = pot.to_dict()['potId']
        firestore_input = {"session.checkIn.showCheckIn": True}
        # Update Firebase to alert mobile app
        pots_collection.document(pot_id).update(firestore_input)
        # Alert Pot
        alert_message = MessageToPot(action=Action.update,
                                potId=pot_id, 
                                data=[PotSendDataDictBool(
                                    field=PotSendDataBool.showCheckIn,
                                    value=True)])
        await ws_manager.send_personal_message_json(alert_message.dict(), pot_id)
        logger.info("Sent Check In alert to Pot {}".format(pot_id))
        # TODO: Need a message queue for messages not sent to pots with failed websocket connection

async def quiz_alert():
    current_date = datetime.utcnow().strftime('%Y%m%d')
    # NOTE: For Python, all string fields with an integer value like '1' require ``
    retrieved_pots = pots_collection.where('session.quiz.quizDates', 'array_contains', current_date).get()

    # TODO: parse this properly to Pot object
    for pot in retrieved_pots:
        pot_id = pot.to_dict()["potId"]
        quiz_day_number_idx = pot.to_dict()['session']['quiz']['quizDates'].index(current_date)
        quiz_day_number = pot.to_dict()['session']['quiz']['quizDayNumbers'][quiz_day_number_idx]
        current_show_quiz_numbers: list = pot.to_dict()['session']['quiz']['showQuizNumbers']
        firestore_input = {"session.quiz.showQuizNumbers": current_show_quiz_numbers.append(quiz_day_number),
                            "session.quiz.currentQuizDayNumber" : quiz_day_number}

        # Update Firebase to alert mobile app
        pots_collection.document(pot_id).update(firestore_input)
        logger.info("Updated Quiz {} alert for Pot {} to database".format(quiz_day_number, pot_id))
        
        #TODO: Also alert when previous quiz not yet completed 
        # Alert Pot
        alert_message = MessageToPot(action=Action.update,
                                potId=pot_id, 
                                data=[PotSendDataDictBool(
                                    field=PotSendDataBool.showQuiz,
                                    value=True)])
        await ws_manager.send_personal_message_json(alert_message.dict(), pot_id)

        logger.info("Sent Quiz {} alert to Pot {}".format(quiz_day_number, pot_id))

scheduler = AsyncIOScheduler({'apscheduler.timezone': 'UTC'})

# UTC Time is 8 hours ahead of SGT, so UTC 1600 == SGT 0000
scheduler.add_job(daily_check_in_alert, 'cron', hour=16)
scheduler.add_job(quiz_alert, 'cron', hour=16)
scheduler.start()