import os
import requests
import traceback
from bs4 import BeautifulSoup

from dotenv import load_dotenv

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import logging
from logging.handlers import RotatingFileHandler

load_dotenv()


def setup_logger(log_dir="logs", log_file="scraper.log", max_bytes=10*1024*1024, backup_count=5):
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    log_dir = os.path.join(os.getcwd(), log_dir)
    os.makedirs(log_dir, exist_ok=True)
    file_handler = RotatingFileHandler(
        filename=os.path.join(log_dir, log_file),
        maxBytes=max_bytes,
        backupCount=backup_count
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)

    logger.addHandler(file_handler)
    return logger

logger = setup_logger()


def check_for_new_offers(location, url):
    response = requests.get(url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        search_result = soup.find("h2", class_="SearchResults-desktop")

        if search_result:
            message = search_result.get_text(strip=True)

            if "Aucun logement" not in message:
                individual_appartments_counter = get_inidividual_appartment_offers_count(
                    soup)

                if individual_appartments_counter > 0:
                    log_content(location, message)
                    send_email(location, message, url, os.getenv("RECEIVER_EMAIL")) # send it to other person
                    send_email(location, message, url, os.getenv("SENDER_EMAIL")) # send it to me 2


def get_inidividual_appartment_offers_count(soup):
    card_classes = "fr-col-12 fr-col-sm-6 fr-col-md-4 svelte-11sc5my fr-col-lg-4"
    aprtment_cards = soup.find_all("li", class_=card_classes)

    individual_appartments_counter = 0
    for card in aprtment_cards:
        card_detail_classes = "fr-card__detail fr-icon-group-fill"
        card_detail = card.find("p", class_=card_detail_classes)
        card_colocation_or_individual_text = card_detail.get_text(strip=True)

        if card_colocation_or_individual_text == "Colocation":
            continue
        elif card_colocation_or_individual_text == "Individuel":
            apartment_title = card.find(
                "h3", class_="fr-card__title").get_text(strip=True)
            log_content("Individual Appartment found", apartment_title)
            individual_appartments_counter += 1

    return individual_appartments_counter


def log_content(location, message):
    log_entry = f"{location.ljust(60)}: {message}\n"
    logger.info(log_entry)


def send_email(location, message, url, receiver_email):
    sender_email = os.getenv("SENDER_EMAIL")
    sender_password = os.getenv("SENDER_PASSWORD")

    subject = "New Apartment Offers"
    body = f"There are new apartment offers in \
        {location}: {message}\nurl : {url}"

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            text = msg.as_string()
            server.sendmail(sender_email, receiver_email, text)
            print(f"Email notification sent for {location}")
    except Exception as e:
        print(f"Error sending email: {e}")
        traceback.print_exc()
        
        
if __name__ == "__main__":
    url = "https://trouverunlogement.lescrous.fr/tools/36/search?bounds=2.4130316_48.6485333_2.4705092_48.6109217"

    locations = {
        "Evry": url,
    }
    
    logger.info("Starting the scraper")
    while True:
        for location, url in locations.items():
            check_for_new_offers(location, url)

