import requests
from bs4 import BeautifulSoup
from datetime import datetime


class TrackingDetail:
    def __init__(self, tracking_id: int):
        self.tracking_id = tracking_id
        self.status: str = None
        self.store_name: str = None
        self.store_address: str = None
        self.shipping_date: datetime = None
        self.estimated_arrival_date: datetime = None
        self.pickup_deadline: datetime = None
        self.payment_type: str = None
        self.shipping_timeline: list = []


class ShippingStatus:
    def __init__(self, date: datetime, status: str):
        self.date = date
        self.status = status


def get_details(tracking_id: int):
    session = requests.Session()
    session.headers[
        "User-Agent"
    ] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

    # get __VIEWSTATE
    r = session.get("https://eservice.7-11.com.tw/e-tracking/search.aspx")
    soup = BeautifulSoup(r.text, "html.parser")

    __VIEWSTATE = soup.find(id="__VIEWSTATE")
    __VIEWSTATEGENERATOR = soup.find(id="__VIEWSTATEGENERATOR")

    # save verify code
    r = session.get(f"https://eservice.7-11.com.tw/e-tracking/ValidateImage.aspx?ts={int(datetime.now().timestamp())}")

    with open("verify_code.jpg", "wb+") as f:
        f.write(r.content)

    verify_code = input("Verify code:")

    # post data
    r = session.post(
        "https://eservice.7-11.com.tw/e-tracking/search.aspx",
        data={
            "__VIEWSTATE": __VIEWSTATE,
            "__VIEWSTATEGENERATOR": __VIEWSTATEGENERATOR,
            "__EVENTTARGET": "submit",
            "txtProductNum": tracking_id,
            "tbChkCode": verify_code,
            "txtPage": 1,
        },
    )

    soup = BeautifulSoup(r.text, "html.parser")

    error = soup.find(id="lbMsg")
    if error:
        raise ValueError(f"Could not find tracking id: {tracking_id}.")

    result = soup.find(class_="result")

    if not result:
        raise ValueError("Invalid verify code.")

    detail = TrackingDetail(tracking_id)
    detail.status = result.find(id="last_message").text
    detail.store_name = result.find(id="store_name").text
    detail.store_address = result.find(id="store_address").text
    detail.shipping_date = datetime.strptime(result.find(id="store_outdate").text, "%Y-%m-%d")
    detail.estimated_arrival_date = datetime.strptime(result.find(id="arrivalstore_date").text, "%Y-%m-%d")
    detail.pickup_deadline = datetime.strptime(result.find(id="deadline").text, "%Y-%m-%d")
    detail.payment_type = result.find(id="servicetype").text

    for i in result.find(id="timeline_status"):
        status = i.contents[1].contents
        detail.shipping_timeline.append(
            ShippingStatus(date=datetime.strptime(status[2], "%Y/%m/%d %H:%M"), status=status[0])
        )

    return detail
