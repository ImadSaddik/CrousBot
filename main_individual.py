import os
import time
import smtplib
import requests
import traceback

from bs4 import BeautifulSoup
from dotenv import load_dotenv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


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
                    print(
                        f"Found {individual_appartments_counter} new offers in {location}")
                    send_email(location=location, message=message, url=url,
                               receiver_email=os.getenv("RECEIVER_EMAIL"))


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

            if check_if_new_offers_available(card):
                log_content("Individual Appartment found", apartment_title)
                individual_appartments_counter += 1

    return individual_appartments_counter


def check_if_new_offers_available(card):
    apartment_link = card.find("a")["href"]
    appartment_offer_page = f"""https://trouverunlogement.lescrous.fr{
        apartment_link}"""

    response = requests.get(appartment_offer_page)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")

        div_container = soup.find("div", class_="fr-mb-3w")
        a_tag = div_container.find("a", class_="fr-btn")
        if a_tag:
            return True

    return False


def log_content(location, message):
    print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {location}: {message}\n")


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
    load_dotenv()

    url_1 = "https://trouverunlogement.lescrous.fr/tools/37/search?bounds=2.224122_48.902156_2.4697602_48.8155755"
    url_2 = "https://trouverunlogement.lescrous.fr/tools/37/search?bounds=2.3456154_48.8420887_2.3481533_48.8407925"
    url_3 = "https://trouverunlogement.lescrous.fr/tools/37/search?bounds=2.3475418_48.8403664_2.349218_48.8392315"
    url_4 = "https://trouverunlogement.lescrous.fr/tools/37/search?bounds=2.338511_48.8460901_2.3398229_48.8446256"
    url_5 = "https://trouverunlogement.lescrous.fr/tools/37/search?bounds=2.3426248_48.8441866_2.3447498_48.8435835"
    url_6 = "https://trouverunlogement.lescrous.fr/tools/37/search?bounds=2.2723279_48.8710747_2.2745213_48.8691568"
    url_7 = "https://trouverunlogement.lescrous.fr/tools/37/search?bounds=2.3290562_48.849943_2.3309234_48.8479074"
    url_8 = "https://trouverunlogement.lescrous.fr/tools/37/search?bounds=2.3453689_48.8276182_2.3469872_48.8259151"
    url_9 = "https://trouverunlogement.lescrous.fr/tools/37/search?bounds=2.4130316_48.6485333_2.4705092_48.6109217"

    locations = {
        # "Paris": url_1,
        # "ESPCI Paris, Paris": url_2,
        # "AgroParisTech, Paris": url_3,
        # "MINES ParisTech, Paris": url_4,
        # "Chimie ParisTech, Paris": url_5,
        # "Université Paris-Dauphine, Paris": url_6,
        # "Institut Catholique de Paris, Paris": url_7,
        # "Télécom ParisTech, Paris": url_8,
        "Evry": url_9
    }

    counter = 0
    max_iterations = 600
    while counter < max_iterations:
        for location, url in locations.items():
            check_for_new_offers(location, url)
            
        time.sleep(1)
        counter += 1
