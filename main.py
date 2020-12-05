import MySQLdb as msd
import json
import logging
import re
import requests
import time
import yaml
from lxml import html

# load config
config = yaml.safe_load(open("config.yml"))

# if key is provided, import and initialize sentry
sentry_sdk = None
if config["main"]["sentry_dns"]:
    import sentry_sdk

    sentry_sdk.init(config["main"]["sentry_dns"], traces_sample_rate=1.0, ignore_errors=[KeyboardInterrupt])

# enable logging
logging.basicConfig(level=config["main"]["log_level"])
log = logging.getLogger(__name__)

old_data = {}

ditto_url = "https://leekduck.com/FindDitto/"


def fetch_data() -> dict:
    r = requests.get(ditto_url, headers={"User-Agent": config["main"]["user_agent"]})
    tree = html.fromstring(r.content)
    output, poke_ids, poke_names = {}, [], []
    poke = tree.xpath('//li[@class="pkmn-list-item"]')

    for row in poke:
        poke_id = int(row.find('div/img').get("src").split("pokemon_icon_")[1].split("_")[0])  # call me lazy
        poke_name = row.find('div[@class="pkmn-name"]').text
        poke_ids.append(poke_id)
        poke_names.append(poke_name)

    for ix, poke_id in enumerate(poke_ids):
        output[poke_id] = poke_names[ix]

    output = dict(sorted(output.items()))
    return output


def send_alert(message: str) -> None:
    data = {
        "content": message,
        "username": config["main"]["discord_username"],
    }

    result = requests.post(
        config["main"]["discord_webhook"],
        data=json.dumps(data),
        headers={
            "Content-Type": "application/json"
        }
    )

    try:
        result.raise_for_status()
    except Exception as ex:
        if sentry_sdk:
            sentry_sdk.capture_exception(ex)
        log.error(f'[Discord] Failed to sent: {data["content"]}! Exception {e}')


def compare_changed(new_data: dict) -> dict:
    global old_data
    output = None

    if not old_data:
        old_data = new_data
    elif old_data != new_data:
        output = new_data
        old_data = new_data

    return output


def update_db(new_data: dict) -> None:
    con = msd.connect(
        host=config["rdm_db"]["host"],
        user=config["rdm_db"]["user"],
        passwd=config["rdm_db"]["password"],
        db=config["rdm_db"]["name"],
        connect_timeout=config["rdm_db"]["connect_timeout"],
    )

    cur = con.cursor()

    sql = """
        UPDATE
            `metadata`
        SET
            `value` = %(ditto_ids)s
        WHERE
            `key` = 'DITTO_DISGUISES';
    """
    val = ",".join([str(r) for r in new_data.keys()])

    log.debug(f"Query: {sql} Values: {val}")
    cur.execute(sql, {"ditto_ids": val})

    con.commit()
    con.close()


def main():
    new_data = fetch_data()
    new_ditto = compare_changed(new_data)

    if new_ditto:
        message = config["main"]["discord_message"].format(', '.join(new_ditto.values()))
        log.info(message)

        if config["main"]["discord_webhook"]:
            send_alert(message)
            log.info("Discord alert sent.")

        if config["rdm_db"]["enabled"]:
            update_db(new_ditto)
            log.info("Db updated.")


if __name__ == '__main__':
    log.info("Started pogodittoupdater \\o/")

    while True:
        try:
            main()
        except Exception as e:
            log.error(f"Exception: {e}")
            if sentry_sdk:
                sentry_sdk.capture_exception(e)
        finally:
            time.sleep(config["main"]["loop_sleep"])
